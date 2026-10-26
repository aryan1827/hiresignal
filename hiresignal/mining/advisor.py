"""Skill-gap advisor: given the skills you have, which role fits and what to learn next.

For each role family we know P(skill | role), the share of that role's postings
asking for each skill. For a person with skill set S:

* fit(role)   = sum of P(s | role) for s in S, over the sum for that role's top 15 skills;
* next skill  = skills not in S, scored by P(skill | role) plus a bonus from the
                association rules whose antecedent is already inside S.
"""
from __future__ import annotations

import pandas as pd

from .. import config

EXTC_STUDENT = ["C", "C++", "Python", "MATLAB", "Embedded systems", "Microcontrollers",
                "Verilog/SystemVerilog", "Signal processing", "Linux", "Git", "IoT"]

SKIP_ROLES = {"Other", "Business & Operations"}


def profiles(df: pd.DataFrame, min_size=60) -> pd.DataFrame:
    rows = []
    for role, sub in df.groupby("role_family"):
        if role in SKIP_ROLES or len(sub) < min_size:
            continue
        vc = sub["tech_skills"].explode().dropna().value_counts() / len(sub)
        for s, p in vc.head(40).items():
            rows.append({"role_family": role, "skill": s, "p": round(p, 4)})
    t = pd.DataFrame(rows)
    t.to_csv(config.TABLES / "role_profiles.csv", index=False)
    return t


def advise(my_skills: list[str], prof: pd.DataFrame, rules: pd.DataFrame | None = None, top=8):
    mine = set(my_skills)
    fits = []
    for role, g in prof.groupby("role_family"):
        g = g.sort_values("p", ascending=False).head(15)
        fits.append({"role_family": role,
                     "fit_pct": round(100 * g.loc[g["skill"].isin(mine), "p"].sum() / g["p"].sum(), 1),
                     "missing_top": ", ".join(g.loc[~g["skill"].isin(mine), "skill"].head(4))})
    fits = pd.DataFrame(fits).sort_values("fit_pct", ascending=False)

    bonus = {}
    if rules is not None and len(rules):
        for _, r in rules.iterrows():
            ante = set(r["antecedent"].split(" + "))
            if ante <= mine and r["consequent"] not in mine:
                bonus[r["consequent"]] = max(bonus.get(r["consequent"], 0), r["confidence"])
    best_roles = fits.head(3)["role_family"].tolist()
    cand = prof[prof["role_family"].isin(best_roles) & ~prof["skill"].isin(mine)]
    score = cand.groupby("skill")["p"].mean()
    recs = pd.DataFrame({"skill": score.index, "demand_in_best_roles": score.values})
    recs["rule_bonus"] = recs["skill"].map(bonus).fillna(0)
    recs["score"] = (recs["demand_in_best_roles"] + 0.3 * recs["rule_bonus"]).round(3)
    return fits, recs.sort_values("score", ascending=False).head(top)
