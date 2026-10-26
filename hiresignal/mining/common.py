"""Shared helpers for the mining stage."""
from __future__ import annotations

import pandas as pd

from .. import config
from ..taxonomy import CATEGORY

SOFT = "Soft Skills & Languages"
PRACTICE = "Practices & Architecture"


def load() -> pd.DataFrame:
    df = pd.read_parquet(config.PROCESSED / "postings.parquet")
    df["skills"] = df["skills"].map(list)
    df["tech_skills"] = df["skills"].map(lambda L: [s for s in L if CATEGORY[s] != SOFT])
    return df


def save(df: pd.DataFrame, name: str, index=False) -> pd.DataFrame:
    df.to_csv(config.TABLES / f"{name}.csv", index=index)
    return df


def unique_roles(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse monthly HN reposts of the same job (same company and title) to the
    latest one. Trends keep every month; salary, rules, network and clustering use
    this view so frequent re-posters do not dominate."""
    key = (df["company"].fillna("").str.lower().str.replace(r"\W+", "", regex=True) + "|" +
           df["title"].fillna("").str.lower().str.replace(r"\W+", "", regex=True))
    has_key = df["company"].notna() & df["title"].notna()
    d = df.assign(_key=key).sort_values("month")
    dup = has_key.loc[d.index] & d.duplicated("_key", keep="last")
    return d[~dup].drop(columns="_key").sort_index()
