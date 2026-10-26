"""EXTC lens: where do Electronics & Telecommunication skills stand in this market?"""
from __future__ import annotations

import pandas as pd

from ..taxonomy import CATEGORY
from .common import save

HW = "Embedded, Hardware & Telecom"


def run(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["has_hw"] = df["skills"].map(lambda L: any(CATEGORY[s] == HW for s in L))
    hw = df[df["has_hw"]]
    hw_skills = hw["skills"].explode().dropna()
    top_hw = hw_skills[hw_skills.map(lambda s: CATEGORY[s] == HW)].value_counts()
    top_hw = save(top_hw.rename_axis("skill").reset_index(name="postings"), "extc_top_skills")
    # Software skills that accompany hardware skills: the bridge from EXTC into software jobs.
    companions = hw_skills[hw_skills.map(lambda s: CATEGORY[s] not in (HW, "Soft Skills & Languages",
                                                                        "Practices & Architecture"))]
    comp = companions.value_counts().head(20) / len(hw) * 100
    comp = save(comp.round(1).rename_axis("skill").reset_index(name="share_of_hw_posts_pct"), "extc_companion_skills")
    roles = save(hw["role_family"].value_counts().rename_axis("role_family").reset_index(name="postings"),
                 "extc_roles")
    hn = df[(df["source"] == "hn") & df["month"].notna()]
    trend = (hn.groupby(hn["month"].str[:4])["has_hw"].mean() * 100).round(2)
    trend = save(trend.rename_axis("year").reset_index(name="hw_share_pct"), "extc_trend_by_year")
    sal = df[df["salary_usd_mid"].notna()]
    return {"n_hw": int(len(hw)), "share_pct": round(100 * len(hw) / len(df), 1),
            "top": top_hw, "companions": comp, "roles": roles, "trend": trend,
            "median_salary_hw": float(sal.loc[sal["has_hw"], "salary_usd_mid"].median()),
            "median_salary_all": float(sal["salary_usd_mid"].median())}
