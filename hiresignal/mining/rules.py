"""Association rule mining with a from-scratch Apriori implementation.

Transactions are the technical skill sets of individual postings. A rule A -> B
says "postings that ask for A also tend to ask for B":

* support(A -> B)    = P(A and B)
* confidence(A -> B) = P(B | A)
* lift(A -> B)       = P(B | A) / P(B), above 1 means A makes B more likely
"""
from __future__ import annotations

import itertools
from collections import Counter

import pandas as pd

from .common import save
from .network import transactions


def apriori(tx: list[frozenset], min_support: float, max_len=3) -> dict[frozenset, int]:
    min_count = min_support * len(tx)
    counts = Counter(i for t in tx for i in t)
    frequent = {frozenset([i]): c for i, c in counts.items() if c >= min_count}
    result = dict(frequent)
    k = 2
    while frequent and k <= max_len:
        prev = set(frequent)
        items = sorted({i for s in prev for i in s})
        # Apriori property: every (k-1)-subset of a candidate must itself be frequent.
        cands = {a | {i} for a in prev for i in items if i not in a}
        cands = {c for c in cands if len(c) == k and
                 all(frozenset(sub) in prev for sub in itertools.combinations(c, k - 1))}
        cc = Counter()
        for t in tx:
            if len(t) >= k:
                for c in cands:
                    if c <= t:
                        cc[c] += 1
        frequent = {c: v for c, v in cc.items() if v >= min_count}
        result.update(frequent)
        k += 1
    return result


def rules_from(freq: dict[frozenset, int], n: int, min_conf=0.35, min_lift=1.5) -> pd.DataFrame:
    rows = []
    for itemset, cnt in freq.items():
        if len(itemset) < 2:
            continue
        for cons in itemset:
            ante = itemset - {cons}
            conf = cnt / freq[ante]
            lift = conf / (freq[frozenset([cons])] / n)
            if conf >= min_conf and lift >= min_lift:
                rows.append({"antecedent": " + ".join(sorted(ante)), "consequent": cons,
                             "support_pct": round(100 * cnt / n, 2), "confidence": round(conf, 3),
                             "lift": round(lift, 2), "count": cnt, "size": len(itemset)})
    return pd.DataFrame(rows)


def run(df: pd.DataFrame, min_support=0.008) -> dict:
    tx = transactions(df)
    freq = apriori(tx, min_support)
    rules = rules_from(freq, len(tx))
    rules["score"] = (rules["confidence"] * rules["lift"]).round(3)
    rules = save(rules.sort_values(["score", "support_pct"], ascending=False), "association_rules")
    itemsets = pd.DataFrame([{"itemset": " + ".join(sorted(k)), "size": len(k),
                              "support_pct": round(100 * v / len(tx), 2)} for k, v in freq.items()])
    save(itemsets.sort_values("support_pct", ascending=False), "frequent_itemsets")
    return {"rules": rules, "n_transactions": len(tx),
            "itemsets_by_size": itemsets["size"].value_counts().sort_index().to_dict()}
