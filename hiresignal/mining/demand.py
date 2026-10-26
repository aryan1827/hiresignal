"""Descriptive demand analysis: top skills, roles, locations and salaries."""
from __future__ import annotations

import pandas as pd

from ..taxonomy import CATEGORY
from .common import SOFT, save


def skill_table(df: pd.DataFrame) -> pd.DataFrame:
    base = (df["n_skills"] > 0).sum()
    counts = df["skills"].explode().value_counts()
    t = pd.DataFrame({"skill": counts.index, "postings": counts.values})
    t["share_pct"] = (100 * t["postings"] / base).round(2)
    t["category"] = t["skill"].map(CATEGORY)
    return save(t, "skill_demand")


def category_table(df: pd.DataFrame) -> pd.DataFrame:
    cats = df["skills"].map(lambda L: sorted({CATEGORY[s] for s in L}))
    base = (df["n_skills"] > 0).sum()
    c = cats.explode().dropna().value_counts()
    t = pd.DataFrame({"category": c.index, "postings": c.values,
                      "share_pct": (100 * c.values / base).round(1)})
    return save(t, "category_demand")


def by_group(df: pd.DataFrame, group: str, top=10, min_group=100) -> pd.DataFrame:
    rows = []
    for g, sub in df.groupby(group):
        if len(sub) < min_group:
            continue
        vc = sub["tech_skills"].explode().dropna().value_counts().head(top)
        for rank, (s, c) in enumerate(vc.items(), 1):
            rows.append({group: g, "rank": rank, "skill": s, "postings": int(c),
                         "share_pct": round(100 * c / len(sub), 1), "group_size": len(sub)})
    return save(pd.DataFrame(rows), f"top_skills_by_{group}")


def roles_locations(df: pd.DataFrame) -> dict:
    def vc(col, name, head=None):
        s = df[col].value_counts()
        s = s.head(head) if head else s
        return save(s.rename_axis(col).reset_index(name="postings"), name)

    out = {"roles": vc("role_family", "role_families"),
           "seniority": vc("seniority", "seniority"),
           "countries": vc("country", "top_countries", 25),
           "cities": vc("city", "top_cities", 25),
           "work_mode": vc("work_mode", "work_mode")}
    wm = (pd.crosstab(df["region"].fillna("Unknown"), df["work_mode"], normalize="index") * 100).round(1)
    out["work_mode_by_region"] = save(wm.reset_index(), "work_mode_by_region")
    return out


def salary_analysis(df: pd.DataFrame, min_n=30) -> dict:
    s = df[df["salary_usd_mid"].notna()].copy()
    # The skill premium uses US-based or US-remote posts only, so that location
    # differences are not mistaken for skill effects.
    us = s[(s["country"] == "United States") |
           ((s["source"] == "hn") & s["country"].isna() & (s["work_mode"] == "Remote"))]
    by_role = (s.groupby("role_family")["salary_usd_mid"].agg(["count", "median"])
               .query("count >= 15").sort_values("median", ascending=False).round(0).reset_index())
    save(by_role, "salary_by_role")
    median_us = us["salary_usd_mid"].median()
    e = us[["salary_usd_mid", "tech_skills"]].explode("tech_skills").dropna()
    rows = []
    for skill, g in e.groupby("tech_skills"):
        if len(g) >= min_n:
            med = g["salary_usd_mid"].median()
            rows.append({"skill": skill, "n": len(g), "median_usd": round(med),
                         "premium_pct": round(100 * (med / median_us - 1), 1),
                         "category": CATEGORY[skill]})
    prem = save(pd.DataFrame(rows).sort_values("premium_pct", ascending=False), "salary_premium_by_skill")
    by_sen = save(s.groupby("seniority")["salary_usd_mid"].agg(["count", "median"]).round(0).reset_index(),
                  "salary_by_seniority")
    return {"n_salary": int(len(s)), "n_us_salary": int(len(us)), "median_us": float(median_us),
            "by_role": by_role, "premium": prem, "by_seniority": by_sen}


def soft_skills(df: pd.DataFrame) -> pd.DataFrame:
    base = (df["n_skills"] > 0).sum()
    e = df["skills"].explode().dropna()
    vc = e[e.map(lambda s: CATEGORY.get(s) == SOFT)].value_counts()
    t = pd.DataFrame({"skill": vc.index, "postings": vc.values,
                      "share_pct": (100 * vc.values / base).round(1)})
    return save(t, "soft_skills")
