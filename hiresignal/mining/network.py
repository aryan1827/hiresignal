"""Skill co-occurrence network: lift-weighted graph, Louvain communities, centrality."""
from __future__ import annotations

import itertools
import json
from collections import Counter

import networkx as nx
import pandas as pd

from .. import config
from ..taxonomy import CATEGORY
from .common import PRACTICE, save


def transactions(df: pd.DataFrame) -> list[frozenset]:
    tx = [frozenset(s for s in L if CATEGORY[s] != PRACTICE) for L in df["tech_skills"]]
    return [t for t in tx if len(t) >= 2]


def build(df: pd.DataFrame, top_n=70, min_count=25, min_lift=1.3) -> dict:
    tx = transactions(df)
    N = len(tx)
    freq = Counter(s for t in tx for s in t)
    nodes = [s for s, _ in freq.most_common(top_n)]
    keep = set(nodes)
    pair = Counter()
    for t in tx:
        for a, b in itertools.combinations(sorted(t & keep), 2):
            pair[(a, b)] += 1

    G = nx.Graph()
    for s in nodes:
        G.add_node(s, count=freq[s], category=CATEGORY[s])
    for (a, b), c in pair.items():
        lift = c * N / (freq[a] * freq[b])
        if c >= min_count and lift >= min_lift:
            G.add_edge(a, b, count=c, lift=round(lift, 3))
    G.remove_nodes_from([n for n in list(G) if G.degree(n) == 0])

    comms = nx.community.louvain_communities(G, weight="lift", seed=config.RANDOM_STATE)
    comms = sorted(comms, key=lambda c: -sum(freq[s] for s in c))
    member = {s: i for i, c in enumerate(comms) for s in c}
    pr = nx.pagerank(G, weight="count")
    btw = nx.betweenness_centrality(G)
    for s in G:
        G.nodes[s].update(community=member[s], pagerank=round(pr[s], 5),
                          betweenness=round(btw[s], 5), degree=G.degree(s))

    nodes_df = save(pd.DataFrame([{"skill": s, **G.nodes[s]} for s in G])
                    .sort_values("pagerank", ascending=False), "network_nodes")
    edges_df = save(pd.DataFrame([{"a": a, "b": b, **d} for a, b, d in G.edges(data=True)])
                    .sort_values("lift", ascending=False), "network_edges")
    comm_list = [{"id": i, "size": len(c), "members": sorted(c, key=lambda s: -freq[s])}
                 for i, c in enumerate(comms)]
    (config.TABLES / "network_communities.json").write_text(json.dumps(comm_list, indent=2))
    nx.write_gexf(G, config.TABLES / "skill_network.gexf")
    return {"graph": G, "nodes": nodes_df, "edges": edges_df, "communities": comm_list,
            "modularity": round(nx.community.modularity(G, comms, weight="lift"), 3),
            "n_transactions": N}
