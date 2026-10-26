"""Hacker News "Ask HN: Who is hiring?" threads.

Each month a bot account posts a thread where companies reply with one
top-level comment per job. We use the official, documented HN Search API run
by Algolia (https://hn.algolia.com/api), which returns a whole thread in a
single request, so 46 months cost 47 requests in total.

Personal data: the comment author's username is dropped here and never stored.
"""
from __future__ import annotations

import re

from .. import config
from ..polite import PoliteSession

SEARCH = ("https://hn.algolia.com/api/v1/search_by_date?"
          "tags=story,author_whoishiring&hitsPerPage=1000")
ITEM = "https://hn.algolia.com/api/v1/items/{id}"
TITLE_RE = re.compile(r"Who is hiring\? \((\w+) (\d{4})\)", re.I)
MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}


def find_threads(s: PoliteSession) -> list[dict]:
    hits = s.get(SEARCH)["hits"]
    threads = []
    for h in hits:
        m = TITLE_RE.search(h.get("title") or "")
        if not m:
            continue            # skips "Who wants to be hired?" and "Freelancer?" threads
        month, year = MONTHS[m.group(1).lower()], int(m.group(2))
        if config.HN_START <= (year, month) <= config.HN_END:
            threads.append({"id": h["objectID"], "year": year, "month": month})
    return sorted(threads, key=lambda t: (t["year"], t["month"]))


def collect(s: PoliteSession) -> list[dict]:
    rows = []
    threads = find_threads(s)
    print(f"  HN: {len(threads)} monthly threads found")
    for t in threads:
        item = s.get(ITEM.format(id=t["id"]))
        n = 0
        for c in item.get("children", []):          # top-level comments = job posts
            text = c.get("text")
            if not text or len(text) < 80:          # deleted, flagged or one-line replies
                continue
            rows.append({
                "source": "hn",
                "source_id": f"hn-{c['id']}",
                "url": f"https://news.ycombinator.com/item?id={c['id']}",
                "title": None, "company": None, "location_raw": None,
                "remote_raw": None, "tags": [],
                "description_html": text,
                "posted_at": c.get("created_at"),
                "thread_month": f"{t['year']}-{t['month']:02d}",
                "salary_min": None, "salary_max": None,
                "salary_currency": None, "salary_period": None,
            })
            n += 1
        print(f"    {t['year']}-{t['month']:02d}: {n} posts")
    return rows


if __name__ == "__main__":
    print(len(collect(PoliteSession())))
