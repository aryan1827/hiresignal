"""Temporal mining on 46 monthly Hacker News threads (Jan 2023 to Oct 2026)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import config
from ..taxonomy import CATEGORY
from .common import SOFT, save

AI_SKILLS = {"LLMs", "Generative AI", "RAG", "LangChain", "LlamaIndex", "Prompt engineering",
             "Fine-tuning", "OpenAI/GPT", "Anthropic/Claude", "Hugging Face", "Vector databases",
             "AI agents", "Embeddings", "MCP", "LLM evals", "Diffusion models", "LLM inference"}


def monthly(df: pd.DataFrame) -> dict:
    hn = df[(df["source"] == "hn") & df["month"].notna()].copy()
    months = sorted(hn["month"].unique())
    vol = hn.groupby("month").size().reindex(months)
    remote = hn.groupby("month")["work_mode"].apply(lambda s: (s == "Remote").mean() * 100)
    ai = hn.groupby("month")["skills"].apply(lambda s: s.map(lambda L: bool(AI_SKILLS & set(L))).mean() * 100)
    activity = save(pd.DataFrame({"month": months, "postings": vol.values,
                                  "remote_pct": remote.reindex(months).round(1).values,
                                  "genai_pct": ai.reindex(months).round(1).values}), "hn_monthly_activity")

    # Share of posts that mention each skill, per month.
    e = hn[["month", "skills"]].explode("skills").dropna()
    counts = pd.crosstab(e["skills"], e["month"]).reindex(columns=months, fill_value=0)
    share = counts.div(vol.values, axis=1) * 100
    share.round(3).to_csv(config.TABLES / "hn_skill_share_by_month.csv")

    # Growth: least-squares slope in percentage points per year, and the ratio of
    # the last six months to the first six.
    x = np.arange(len(months)) / 12.0
    rows = []
    for skill, ys in share.iterrows():
        if CATEGORY[skill] == SOFT or ys.mean() < 0.8:
            continue
        first, last = ys.values[:6].mean(), ys.values[-6:].mean()
        rows.append({"skill": skill, "category": CATEGORY[skill],
                     "mean_share_pct": round(ys.mean(), 2), "first6_pct": round(first, 2),
                     "last6_pct": round(last, 2),
                     "slope_pp_per_year": round(np.polyfit(x, ys.values, 1)[0], 2),
                     "ratio_last_first": round((last + 0.1) / (first + 0.1), 2)})
    growth = save(pd.DataFrame(rows).sort_values("slope_pp_per_year", ascending=False), "hn_skill_growth")

    # Category share by half-year.
    hn["half"] = hn["month"].str[:4] + "-H" + ((hn["month"].str[5:7].astype(int) - 1) // 6 + 1).astype(str)
    hn["cats"] = hn["skills"].map(lambda L: sorted({CATEGORY[s] for s in L}))
    ce = hn[["half", "cats"]].explode("cats").dropna()
    cat_share = (pd.crosstab(ce["cats"], ce["half"]).div(hn.groupby("half").size(), axis=1) * 100).round(1)
    save(cat_share.reset_index(), "hn_category_share_by_half")
    return {"activity": activity, "share": share, "growth": growth, "months": months}
