"""Unsupervised role discovery: cluster postings by their skill profiles.

Each posting becomes a TF-IDF-weighted binary skill vector, reduced with
truncated SVD and clustered with k-means. The number of clusters is chosen by
silhouette score. We then compare the discovered clusters with the rule-based
role families using the adjusted Rand index (ARI).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import MultiLabelBinarizer, normalize

from .. import config
from .common import save


def run(df: pd.DataFrame, k_range=range(6, 15)) -> dict:
    sub = df[df["tech_skills"].map(len) >= 3].reset_index(drop=True)
    mlb = MultiLabelBinarizer(sparse_output=True)
    X = mlb.fit_transform(sub["tech_skills"])
    Xt = TfidfTransformer().fit_transform(X)
    Z = normalize(TruncatedSVD(40, random_state=config.RANDOM_STATE).fit_transform(Xt))

    rng = np.random.RandomState(config.RANDOM_STATE)
    sample = rng.choice(len(Z), min(4000, len(Z)), replace=False)
    scores = []
    for k in k_range:
        km = KMeans(k, n_init=5, random_state=config.RANDOM_STATE).fit(Z)
        scores.append({"k": k, "silhouette": round(silhouette_score(Z[sample], km.labels_[sample]), 4),
                       "inertia": round(km.inertia_, 1)})
    sil = save(pd.DataFrame(scores), "cluster_silhouette")
    best_k = int(sil.loc[sil["silhouette"].idxmax(), "k"])
    km = KMeans(best_k, n_init=10, random_state=config.RANDOM_STATE).fit(Z)
    sub["cluster"] = km.labels_

    # Name each cluster after the skills most over-represented in it.
    dense = pd.DataFrame(X.toarray(), columns=mlb.classes_)
    overall = dense.mean()
    rows = []
    for c in range(best_k):
        m = dense[sub["cluster"] == c].mean()
        lift = (m / overall).where(m >= 0.15, 0)
        top = lift.sort_values(ascending=False).head(5).index.tolist()
        dominant = sub.loc[sub["cluster"] == c, "role_family"].value_counts()
        rows.append({"cluster": c, "size": int((sub["cluster"] == c).sum()),
                     "label": " / ".join(top[:3]), "signature_skills": ", ".join(top),
                     "most_common_role": dominant.index[0],
                     "role_purity_pct": round(100 * dominant.iloc[0] / dominant.sum(), 1)})
    prof = save(pd.DataFrame(rows).sort_values("size", ascending=False), "cluster_profiles")
    ari = adjusted_rand_score(sub["role_family"], sub["cluster"])
    xy = TruncatedSVD(2, random_state=config.RANDOM_STATE).fit_transform(Xt)
    proj = pd.DataFrame({"x": xy[:, 0], "y": xy[:, 1], "cluster": sub["cluster"],
                         "role_family": sub["role_family"], "title": sub["title"]})
    proj.sample(min(3000, len(proj)), random_state=1).to_csv(config.TABLES / "cluster_projection.csv", index=False)
    save(pd.crosstab(sub["cluster"], sub["role_family"]).reset_index(), "cluster_vs_role")
    return {"best_k": best_k, "silhouette": sil, "profiles": prof, "ari": round(ari, 3), "n": len(sub)}
