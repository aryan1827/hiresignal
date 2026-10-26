"""Stage 2: preprocessing.

Raw records from six sources become one clean, de-duplicated table
(``data/processed/postings.parquet``). Steps, in order:

1. HTML to text: BeautifulSoup strips tags; HTML entities are unescaped;
   unicode is normalised (NFKC) and whitespace collapsed.
2. PII scrubbing: e-mail addresses, phone numbers, URLs and @handles are
   replaced by placeholders. HN usernames were already dropped at collection.
3. HN header parsing: the first line of each HN post
   ("Company | Role | Location | REMOTE | $150k") is split and every segment is
   classified as company, role, location, work mode, salary, visa or link.
4. Normalisation: role family and seniority from the title, city/country/region
   and work mode from the location, salary to annual USD, posting month.
5. Language detection (English vs German) with a stop-word ratio.
6. De-duplication: exact duplicates by source id and by text fingerprint, and
   cross-board duplicates by (company, title) key.
7. Tokens for term mining: lowercase, punctuation and numbers removed,
   stop-words removed, Porter-stemmed (the Experiment 4 pipeline).
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata

import pandas as pd
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer

from . import config, geo, roles, salary
from .extract import extract

SOURCES = ["hn", "arbeitnow", "remoteok", "jobicy", "himalayas", "pyjobs"]
SOURCE_LABEL = {"hn": "Hacker News", "arbeitnow": "Arbeitnow", "remoteok": "Remote OK",
                "jobicy": "Jobicy", "himalayas": "Himalayas", "pyjobs": "Python.org Jobs"}

EMAIL = re.compile(r"[\w.+\-]+\s?(?:@|\[at\]|\(at\))\s?[\w\-]+(?:\.|\s?\[dot\]\s?)[\w.\-]+", re.I)
URL = re.compile(r"https?://\S+|www\.\S+", re.I)
PHONE = re.compile(r"(?<!\w)(?:\+?\d{1,3}[\s.\-]?)?(?:\(\d{2,4}\)[\s.\-]?)?\d{3,4}[\s.\-]\d{3,4}(?:[\s.\-]\d{2,4})?(?!\w)")
HANDLE = re.compile(r"(?<![\w@])@[A-Za-z_][\w]{2,}")

GERMAN = set("und der die das wir sie mit für ist ein eine zu von auf bei im den dem als oder auch "
             "wird sind ihre unsere deine du ihr nicht".split())
ENGLISH = set("the and you we our with for are is to of in a an will on as be your this that".split())

STOPWORDS = set("""a an the this that these those and or but if while of to in on at by for with about
against between into through during before after above below from up down out off over under again
further then once here there all any both each few more most other some such no nor not only own same
so than too very s t can will just don should now is are was were be been being have has had having do
does did doing i me my we our you your he him his she her it its they them their what which who whom as
until because how when where why also etc us via per within across including work working team teams
role roles job jobs company companies experience years year looking join apply new strong build building
help please hiring hire""".split())
STEM = PorterStemmer()

ROLE_WORDS = re.compile(
    r"engineer|developer|scientist|designer|manager|lead|architect|analyst|devops|\bsre\b|intern|"
    r"head of|\bcto\b|founding|researcher|specialist|administrator|consultant|marketing|sales|"
    r"recruiter|product|programmer|\bswe\b|director|technician|writer|advocate|operator|associate|"
    r"engineering|frontend|backend|full[\s\-]?stack|\bml\b|\bai\b|data|positions|roles|multiple", re.I)
SAL_WORDS = re.compile(r"[$€£₹]\s?\d|\d\s?k\b|\d{2,3},\d{3}|salary|\bequity\b|\bcomp\b|\busd\b|\beur\b|\bgbp\b|\blpa\b", re.I)
REMOTE_WORDS = re.compile(r"remote|on[\s\-]?site|onsite|hybrid|in[\s\-]office|in[\s\-]person|wfh|distributed", re.I)
VISA_WORDS = re.compile(r"visa|sponsor", re.I)
TYPE_WORDS = re.compile(r"full[\s\-]?time|part[\s\-]?time|contract|freelance|permanent|intern(?:ship)?\b|\bft\b|\bpt\b", re.I)
LINK_WORDS = re.compile(r"https?://|www\.|\.(?:com|io|ai|co|org|dev|app)\b", re.I)


# ------------------------------------------------------------------ cleaning
def html_to_text(raw: str | None) -> str:
    if not raw:
        return ""
    soup = BeautifulSoup(raw, "lxml")
    for bad in soup(["script", "style"]):
        bad.decompose()
    text = soup.get_text("\n")
    text = html.unescape(text)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def scrub_pii(text: str) -> str:
    text = EMAIL.sub("[email]", text)
    text = URL.sub("[link]", text)
    text = PHONE.sub("[phone]", text)
    text = HANDLE.sub("[handle]", text)
    return text


def tokens(text: str) -> list[str]:
    t = text.lower()
    t = re.sub(r"\[(?:email|link|phone|handle)\]", " ", t)
    t = re.sub(r"[^a-z\s]", " ", t)
    return [STEM.stem(w) for w in t.split() if len(w) > 2 and w not in STOPWORDS]


def language(text: str) -> str:
    words = re.findall(r"[a-zäöüß]+", text.lower())[:400]
    if not words:
        return "unknown"
    de = sum(w in GERMAN for w in words)
    en = sum(w in ENGLISH for w in words)
    return "de" if de > en else "en"


# ------------------------------------------------------- HN header parsing
def parse_hn_header(raw_html: str) -> dict:
    """Split the first line of a Who-is-hiring post into labelled fields."""
    first = re.split(r"<p>|\n", raw_html or "", maxsplit=1)[0]
    first = html_to_text(first)
    out = {"company": None, "title": None, "location_raw": None, "remote_raw": None,
           "salary_text": None, "visa": False, "employment_type": None, "header_ok": False}
    segs = [s.strip(" -–—\t") for s in re.split(r"\s\|\s|\|", first) if s.strip(" -–—\t")]
    if len(segs) < 2:
        return out
    out["header_ok"] = True
    out["company"] = re.sub(r"\(.*?\)|\[link\]|https?://\S+", "", segs[0], flags=re.S).strip(" ()")[:80] or None
    titles, locs = [], []
    for seg in segs[1:]:
        if LINK_WORDS.search(seg) and len(seg.split()) <= 3:
            continue
        if VISA_WORDS.search(seg):
            out["visa"] = not re.search(r"\bno\b|not|unable|cannot", seg, re.I)
            continue
        if SAL_WORDS.search(seg):
            out["salary_text"] = (out["salary_text"] or "") + " " + seg
            continue
        if REMOTE_WORDS.search(seg):
            out["remote_raw"] = (out["remote_raw"] or "") + " " + seg
            # "Remote (US)" also carries a location
            rest = REMOTE_WORDS.sub("", seg)
            if geo.normalise(rest)["country"] or geo.normalise(rest)["region"]:
                locs.append(seg)
            continue
        if TYPE_WORDS.search(seg) and len(seg.split()) <= 4 and not ROLE_WORDS.search(seg):
            out["employment_type"] = seg
            continue
        g = geo.normalise(seg)
        if (g["city"] or g["country"]) and not ROLE_WORDS.search(seg):
            locs.append(seg)
            continue
        if ROLE_WORDS.search(seg):
            titles.append(seg)
            continue
        if g["region"]:
            locs.append(seg)
    out["title"] = "; ".join(titles)[:200] or None
    out["location_raw"] = "; ".join(locs)[:200] or None
    return out


ROLE_PHRASE = re.compile(
    r"((?:(?:senior|sr\.?|staff|principal|lead|junior|founding|head of)\s+)?"
    r"(?:[A-Za-z/+#.\-]+\s+){0,3}"
    r"(?:engineers?|developers?|scientists?|designers?|managers?|architects?|analysts?|"
    r"researchers?|programmers?|SREs?|interns?))\b", re.I)


def guess_title(text: str) -> str | None:
    body = (text or "").split("\n", 1)
    m = ROLE_PHRASE.search(body[0][:300]) or (ROLE_PHRASE.search(body[1][:600]) if len(body) > 1 else None)
    return m.group(1).strip()[:120] if m else None


# ---------------------------------------------------------------- pipeline
def load_raw() -> pd.DataFrame:
    frames = []
    for src in SOURCES:
        p = config.RAW / f"{src}.json"
        if p.exists():
            frames.append(pd.DataFrame(json.loads(p.read_text())))
    return pd.concat(frames, ignore_index=True)


def _month(row) -> str | None:
    if row.get("thread_month"):
        return row["thread_month"]
    ts = pd.to_datetime(row.get("posted_at"), errors="coerce", utc=True)
    return None if pd.isna(ts) else ts.strftime("%Y-%m")


def run() -> pd.DataFrame:
    df = load_raw()
    stats = {"raw_records": int(len(df))}
    print(f"[preprocess] {len(df)} raw records")

    # 1. exact duplicates by id
    df = df.drop_duplicates("source_id").reset_index(drop=True)
    stats["after_id_dedupe"] = int(len(df))

    # 2-3. text cleaning, PII scrubbing and HN header parsing
    texts, pii_counts = [], {"email": 0, "link": 0, "phone": 0, "handle": 0}
    for i, row in df.iterrows():
        text = html_to_text(row["description_html"])
        for k, rg in (("email", EMAIL), ("link", URL), ("phone", PHONE), ("handle", HANDLE)):
            pii_counts[k] += len(rg.findall(text))
        if row["source"] == "hn":
            h = parse_hn_header(row["description_html"])
            for k in ("company", "title", "location_raw", "remote_raw"):
                df.at[i, k] = h[k]
            df.at[i, "salary_text"] = h["salary_text"]
            df.at[i, "visa"] = h["visa"]
            df.at[i, "header_ok"] = h["header_ok"]
        texts.append(scrub_pii(text))
    df["text"] = texts
    stats["pii_replaced"] = pii_counts
    df = df.drop(columns=["description_html"])

    # drop posts with almost no content
    df["n_chars"] = df["text"].str.len()
    df = df[df["n_chars"] >= 60].copy()
    stats["after_empty_filter"] = int(len(df))

    # 6. fingerprint and cross-board duplicates
    df["fingerprint"] = df["text"].str.lower().str.replace(r"\W+", "", regex=True).map(
        lambda s: hashlib.md5(s[:2000].encode()).hexdigest())
    before = len(df)
    df = df.drop_duplicates(["source", "thread_month", "fingerprint"])
    df["key"] = (df["company"].fillna("").str.lower().str.replace(r"\W+", "", regex=True) + "|" +
                 df["title"].fillna("").str.lower().str.replace(r"\W+", "", regex=True))
    boards = df[df["source"] != "hn"].sort_values("n_chars", ascending=False)
    dup_mask = boards.duplicated("key") & (boards["key"] != "|")
    df = df.drop(boards[dup_mask].index)
    stats["duplicates_removed"] = int(before - len(df))
    stats["after_dedupe"] = int(len(df))

    # 4. normalisation
    df["month"] = df.apply(_month, axis=1)
    # HN posts without a parsable header: look for a role phrase in the opening lines
    vague = df["title"].fillna("").str.contains(
        r"^(?:multiple|several|various|many|numerous|\w+)\s+(?:roles|positions|openings)|^hiring|^see below",
        case=False, regex=True) & ~df["title"].fillna("").str.contains(
        r"engineer|developer|scientist|designer|manager", case=False, regex=True)
    missing = df["title"].isna() | vague
    df.loc[missing, "title"] = df.loc[missing, "text"].map(guess_title).fillna(df.loc[missing, "title"])
    df["role_family"] = df["title"].map(roles.role_family)
    df["seniority"] = df["title"].map(roles.seniority)
    locs = df["location_raw"].fillna("").map(geo.normalise)
    df["city"] = [l["city"] for l in locs]
    df["country"] = [l["country"] for l in locs]
    df["region"] = [l["region"] for l in locs]

    def mode(row):
        rr = row["remote_raw"]
        flag = rr if isinstance(rr, bool) else None
        text = " ".join(str(x) for x in (rr if not isinstance(rr, bool) else "", row["location_raw"] or "") if x)
        m = geo.work_mode(text, flag)
        if m == "Unspecified":
            m = geo.work_mode(row["text"][:600])
        return m
    df["work_mode"] = df.apply(mode, axis=1)
    # remote-only boards: no location means anywhere
    remote_only = df["source"].isin(["remoteok", "jobicy", "himalayas"]) & df["region"].isna()
    df.loc[remote_only, "region"] = "Global / Anywhere"

    lo, hi = [], []
    for _, row in df.iterrows():
        a, b = (None, None)
        if pd.notna(row["salary_min"]) or pd.notna(row["salary_max"]):
            a, b = salary.to_usd_year(row["salary_min"], row["salary_max"],
                                      row["salary_currency"] or "USD", row["salary_period"] or "year")
        if a is None and row["source"] == "hn":
            a, b = salary.parse_text(row.get("salary_text") or "")
        lo.append(a)
        hi.append(b)
    df["salary_usd_min"], df["salary_usd_max"] = lo, hi
    df["salary_usd_mid"] = (pd.to_numeric(df["salary_usd_min"]) + pd.to_numeric(df["salary_usd_max"])) / 2

    # 5. language
    df["lang"] = df["text"].map(language)

    # skills and tokens
    print("[preprocess] extracting skills ...")
    df["skills"] = [extract(f"{t or ''}\n{x}") for t, x in zip(df["title"], df["text"])]
    df["n_skills"] = df["skills"].map(len)
    df["tokens"] = df["text"].map(lambda t: " ".join(tokens(t)))
    df["source_label"] = df["source"].map(SOURCE_LABEL)

    keep = ["source", "source_label", "source_id", "url", "month", "company", "title",
            "role_family", "seniority", "location_raw", "city", "country", "region", "work_mode",
            "salary_usd_min", "salary_usd_max", "salary_usd_mid", "visa", "header_ok", "lang",
            "tags", "skills", "n_skills", "text", "tokens", "n_chars"]
    df = df[[c for c in keep if c in df.columns]].reset_index(drop=True)
    df["tags"] = df["tags"].map(lambda x: list(x) if isinstance(x, (list, tuple)) else [])
    df["visa"] = df["visa"].astype("boolean")
    df["header_ok"] = df["header_ok"].astype("boolean")

    stats.update({
        "final_postings": int(len(df)),
        "by_source": df["source"].value_counts().to_dict(),
        "with_skills": int((df["n_skills"] > 0).sum()),
        "mean_skills_per_posting": round(float(df["n_skills"].mean()), 2),
        "with_salary": int(df["salary_usd_mid"].notna().sum()),
        "hn_header_parsed": int(df.loc[df["source"] == "hn", "header_ok"].fillna(False).sum()),
        "hn_posts": int((df["source"] == "hn").sum()),
        "german_language": int((df["lang"] == "de").sum()),
        "months_covered": sorted(df.loc[df["source"] == "hn", "month"].dropna().unique().tolist()),
    })
    df.to_parquet(config.PROCESSED / "postings.parquet", index=False)
    (config.PROCESSED / "preprocess_stats.json").write_text(json.dumps(stats, indent=2, default=str))
    print("[preprocess] done:", {k: v for k, v in stats.items() if k != "months_covered"})
    return df


if __name__ == "__main__":
    run()
