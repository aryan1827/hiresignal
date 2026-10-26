"""Emerging vocabulary: terms whose use grew fastest in HN posts, 2023 vs 2026.

This looks beyond the fixed taxonomy. Terms the taxonomy already covers are
flagged, so the output doubles as a list of candidates to add to it.
"""
from __future__ import annotations

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

from ..extract import extract
from .common import save

EXTRA_STOP = ["link", "email", "phone", "handle", "remote", "onsite", "hybrid", "time", "full",
              "san", "francisco", "york", "us", "usa", "com", "www", "https", "http", "ve", "ll", "re"]


def run(df: pd.DataFrame, min_df=25, top=30) -> pd.DataFrame:
    hn = df[(df["source"] == "hn") & df["month"].notna()]
    early = hn[hn["month"] < "2024-01"]["text"]
    late = hn[hn["month"] >= "2026-01"]["text"]
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    vec = CountVectorizer(ngram_range=(1, 2), min_df=min_df, binary=True, lowercase=True,
                          stop_words=list(ENGLISH_STOP_WORDS.union(EXTRA_STOP)),
                          token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z+#.\-]{1,}\b")
    vec.fit(pd.concat([early, late]))
    a = pd.Series(vec.transform(early).sum(0).A1, index=vec.get_feature_names_out()) / len(early) * 100
    b = pd.Series(vec.transform(late).sum(0).A1, index=vec.get_feature_names_out()) / len(late) * 100
    t = pd.DataFrame({"term": a.index, "share_2023_pct": a.values.round(2), "share_2026_pct": b.values.round(2)})
    t["growth_x"] = ((t["share_2026_pct"] + 0.2) / (t["share_2023_pct"] + 0.2)).round(2)
    t["in_taxonomy"] = t["term"].map(lambda w: bool(extract(f"{w} python docker")) and
                                     len(extract(f"{w} python docker")) > 2)
    rising = t[t["share_2026_pct"] >= 1.0].sort_values("growth_x", ascending=False).head(top)
    falling = t[t["share_2023_pct"] >= 1.0].sort_values("growth_x").head(top)
    save(rising, "emerging_terms_rising")
    save(falling, "emerging_terms_falling")
    return rising
