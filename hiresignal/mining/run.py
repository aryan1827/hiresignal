"""Stage 3: run every mining step and write outputs/insights.json with headline numbers."""
from __future__ import annotations

import json

from .. import config
from . import advisor, clusters, demand, emerging, extc, network, rules, trends
from .common import load, unique_roles


def run() -> dict:
    df = load()
    uq = unique_roles(df)
    print(f"[mine] {len(df)} postings, {len(uq)} after collapsing HN reposts")
    skills = demand.skill_table(df)
    cats = demand.category_table(df)
    demand.by_group(df, "role_family")
    demand.by_group(df, "region")
    demand.by_group(df, "source_label", top=8, min_group=90)
    rl = demand.roles_locations(df)
    sal = demand.salary_analysis(uq)
    soft = demand.soft_skills(df)
    print("[mine] trends")
    tr = trends.monthly(df)
    print("[mine] network")
    net = network.build(uq)
    print("[mine] association rules")
    ar = rules.run(uq)
    print("[mine] clustering")
    cl = clusters.run(uq)
    print("[mine] emerging terms")
    em = emerging.run(df)
    ex = extc.run(df)
    prof = advisor.profiles(uq)
    fits, recs = advisor.advise(advisor.EXTC_STUDENT, prof, ar["rules"])
    fits.to_csv(config.TABLES / "advisor_extc_student_fit.csv", index=False)
    recs.to_csv(config.TABLES / "advisor_extc_student_next.csv", index=False)

    tech = skills[skills["category"] != "Soft Skills & Languages"]
    act = tr["activity"]
    g = tr["growth"]
    insights = {
        "postings": int(len(df)),
        "unique_roles": int(len(uq)),
        "sources": df["source_label"].value_counts().to_dict(),
        "hn_months": len(tr["months"]),
        "skills_in_taxonomy": int(len(__import__("hiresignal.taxonomy", fromlist=["x"]).SKILLS)),
        "distinct_skills_found": int(len(skills)),
        "top10_tech_skills": tech.head(10)[["skill", "share_pct"]].to_dict("records"),
        "top_categories": cats.head(6).to_dict("records"),
        "top_roles": rl["roles"].head(8).to_dict("records"),
        "top_countries": rl["countries"].head(8).to_dict("records"),
        "top_cities": rl["cities"].head(8).to_dict("records"),
        "work_mode": rl["work_mode"].to_dict("records"),
        "salary": {"n": sal["n_salary"], "n_us": sal["n_us_salary"], "median_us": sal["median_us"],
                   "top_premium": sal["premium"].head(8)[["skill", "premium_pct", "n"]].to_dict("records"),
                   "bottom_premium": sal["premium"].tail(5)[["skill", "premium_pct", "n"]].to_dict("records")},
        "hn_volume_first_last": [int(act["postings"].iloc[0]), int(act["postings"].iloc[-1])],
        "genai_share_first_last": [float(act["genai_pct"].iloc[0]), float(act["genai_pct"].iloc[-1])],
        "remote_share_first_last": [float(act["remote_pct"].iloc[0]), float(act["remote_pct"].iloc[-1])],
        "fastest_rising": g.head(8)[["skill", "first6_pct", "last6_pct", "slope_pp_per_year"]].to_dict("records"),
        "fastest_falling": g.tail(8)[["skill", "first6_pct", "last6_pct", "slope_pp_per_year"]].to_dict("records"),
        "network": {"nodes": net["graph"].number_of_nodes(), "edges": net["graph"].number_of_edges(),
                    "modularity": net["modularity"],
                    "communities": [c["members"][:6] for c in net["communities"]],
                    "top_pagerank": net["nodes"].head(8)["skill"].tolist(),
                    "top_betweenness": net["nodes"].sort_values("betweenness", ascending=False).head(6)["skill"].tolist()},
        "rules": {"n_rules": int(len(ar["rules"])), "transactions": ar["n_transactions"],
                  "itemsets_by_size": ar["itemsets_by_size"],
                  "top": ar["rules"].head(10)[["antecedent", "consequent", "confidence", "lift"]].to_dict("records")},
        "clusters": {"best_k": cl["best_k"], "ari_vs_roles": cl["ari"], "n": cl["n"],
                     "profiles": cl["profiles"][["label", "size", "most_common_role"]].to_dict("records")},
        "emerging_terms": em.head(12)[["term", "share_2023_pct", "share_2026_pct", "growth_x"]].to_dict("records"),
        "extc": {"n": ex["n_hw"], "share_pct": ex["share_pct"],
                 "top": ex["top"].head(8).to_dict("records"),
                 "companions": ex["companions"].head(8).to_dict("records"),
                 "trend": ex["trend"].to_dict("records"),
                 "median_salary_hw": ex["median_salary_hw"], "median_salary_all": ex["median_salary_all"]},
        "advisor_extc": {"fit": fits.head(5).to_dict("records"), "next": recs.to_dict("records")},
        "soft_skills": soft.head(6).to_dict("records"),
    }
    (config.OUTPUTS / "insights.json").write_text(json.dumps(insights, indent=2, default=str))
    print("[mine] done, insights written to outputs/insights.json")
    return insights


if __name__ == "__main__":
    run()
