"""Stage 4: static figures (PNG) for the report and slides.

Style: light surface, recessive grid, one blue for single-series bars, an
orange accent only for the bar that carries the point, direct labels instead of
legends where possible. Colours come from a CVD-validated categorical order.
"""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402
import pandas as pd  # noqa: E402

from . import config  # noqa: E402

SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
BLUE, ORANGE = SERIES[0], SERIES[1]

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 10.5, "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.titlepad": 14, "legend.frameon": False,
})
T = config.TABLES


def _save(fig, name):
    fig.tight_layout()
    fig.savefig(config.FIGURES / f"{name}.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def _source(ax, text):
    ax.annotate(text, xy=(0, -0.01), xycoords="figure fraction", fontsize=8, color=MUTED, va="bottom")


def hbar(labels, values, title, name, fmt="{:.1f}%", highlight=None, xlabel=None, src=None, color=BLUE):
    labels, values = list(labels)[::-1], list(values)[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.32 * len(labels) + 1.4))
    colors = [ORANGE if highlight and l in highlight else color for l in labels]
    bars = ax.barh(labels, values, color=colors, height=0.68)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    for b, v in zip(bars, values):
        ax.text(b.get_width() + max(values) * 0.01, b.get_y() + b.get_height() / 2, fmt.format(v),
                va="center", fontsize=9, color=INK2)
    ax.set_xlim(0, max(values) * 1.12)
    ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if src:
        _source(ax, src)
    _save(fig, name)


def run():
    ins = json.loads((config.OUTPUTS / "insights.json").read_text())
    n = ins["postings"]
    SRC = f"Source: HireSignal dataset, {n:,} postings from 6 public sources (2023-2026)"

    sk = pd.read_csv(T / "skill_demand.csv")
    tech = sk[sk["category"] != "Soft Skills & Languages"].head(25)
    hbar(tech["skill"], tech["share_pct"], "Top 25 technical skills, % of postings that name a skill",
         "01_top_skills", highlight={"Python"}, src=SRC)

    cat = pd.read_csv(T / "category_demand.csv")
    hbar(cat["category"], cat["share_pct"], "Skill categories, % of postings", "02_categories", src=SRC)

    roles = pd.read_csv(T / "role_families.csv")
    roles = roles[roles["role_family"] != "Other"]
    hbar(roles["role_family"], roles["postings"], "Postings by role family", "03_roles", fmt="{:,.0f}", src=SRC)

    c = pd.read_csv(T / "top_countries.csv").head(12)
    hbar(c["country"], c["postings"], "Top countries named in postings", "04_countries", fmt="{:,.0f}",
         highlight={"India"}, src=SRC)
    ci = pd.read_csv(T / "top_cities.csv").head(15)
    hbar(ci["city"], ci["postings"], "Top cities named in postings", "05_cities", fmt="{:,.0f}", src=SRC)

    # work mode by region, 100% stacked
    wm = pd.read_csv(T / "work_mode_by_region.csv").set_index("region")
    wm = wm.drop(index=[i for i in ["Unknown"] if i in wm.index])
    cols = [c for c in ["Remote", "Hybrid", "Onsite", "Unspecified"] if c in wm.columns]
    colors = {"Remote": SERIES[0], "Hybrid": SERIES[2], "Onsite": SERIES[1], "Unspecified": "#c9c8c2"}
    wm = wm[cols].sort_values("Remote")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    left = pd.Series(0.0, index=wm.index)
    for col in cols:
        ax.barh(wm.index, wm[col], left=left, color=colors[col], label=col, height=0.66,
                edgecolor=SURFACE, linewidth=1.5)
        left += wm[col]
    ax.set_xlim(0, 100)
    ax.grid(axis="y", visible=False)
    ax.legend(ncol=4, loc="upper left", bbox_to_anchor=(0, -0.08))
    ax.set_title("Work mode by region, % of postings")
    _save(fig, "06_work_mode_by_region")

    # HN monthly: three small multiples, one measure each
    act = pd.read_csv(T / "hn_monthly_activity.csv")
    x = pd.to_datetime(act["month"])
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
    for ax, col, title, colr in zip(axes, ["postings", "remote_pct", "genai_pct"],
                                    ["HN job posts per month", "Remote share of HN posts (%)",
                                     "HN posts naming a GenAI skill (%)"], [INK2, BLUE, ORANGE]):
        ax.plot(x, act[col], color=colr, linewidth=2)
        ax.set_title(title, fontsize=11.5)
        ax.set_ylim(0, act[col].max() * 1.15)
        ax.annotate(f"{act[col].iloc[-1]:.0f}", (x.iloc[-1], act[col].iloc[-1]), xytext=(4, 0),
                    textcoords="offset points", fontsize=9, color=INK)
        ax.annotate(f"{act[col].iloc[0]:.0f}", (x.iloc[0], act[col].iloc[0]), xytext=(-4, 6),
                    textcoords="offset points", fontsize=9, color=INK, ha="right")
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    _save(fig, "07_hn_monthly")

    # risers and fallers: dumbbell first 6 months vs last 6 months
    g = pd.read_csv(T / "hn_skill_growth.csv")
    sel = pd.concat([g.head(10), g.tail(8)]).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 6.4))
    for i, r in enumerate(sel.itertuples()):
        up = r.last6_pct >= r.first6_pct
        ax.plot([r.first6_pct, r.last6_pct], [i, i], color=BLUE if up else ORANGE, linewidth=2)
        ax.scatter([r.first6_pct], [i], color=MUTED, s=28, zorder=3)
        ax.scatter([r.last6_pct], [i], color=BLUE if up else ORANGE, s=40, zorder=3)
    ax.set_yticks(range(len(sel)), sel["skill"])
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("% of HN posts: grey = Jan-Jun 2023, colour = May-Oct 2026")
    ax.set_title("Fastest rising (blue) and falling (orange) skills on HN")
    _save(fig, "08_risers_fallers")

    # selected skill trends, small multiples
    share = pd.read_csv(T / "hn_skill_share_by_month.csv", index_col=0)
    xs = pd.to_datetime(share.columns)
    pick = ["AI agents", "LLMs", "Anthropic/Claude", "TypeScript", "JavaScript", "Vue.js",
            "Rust", "Kubernetes", "Django"]
    pick = [p for p in pick if p in share.index]
    fig, axes = plt.subplots(3, 3, figsize=(12, 7.5), sharex=True)
    for ax, s in zip(axes.flat, pick):
        y = share.loc[s].rolling(3, min_periods=1).mean()
        up = y.iloc[-1] >= y.iloc[0]
        ax.plot(xs, y, color=BLUE if up else ORANGE, linewidth=2)
        ax.set_title(s, fontsize=11)
        ax.set_ylim(0, max(1, y.max() * 1.2))
        ax.tick_params(axis="x", labelsize=8)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.suptitle("Monthly share of HN posts (%), 3-month rolling mean", x=0.01, ha="left",
                 fontweight="bold", fontsize=13)
    _save(fig, "09_skill_trends")

    # skill network
    G = nx.read_gexf(T / "skill_network.gexf")
    comms = json.loads((T / "network_communities.json").read_text())
    pos = nx.spring_layout(G, weight="lift", k=0.55, seed=7, iterations=200)
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.axis("off")
    w = [d["lift"] for _, _, d in G.edges(data=True)]
    nx.draw_networkx_edges(G, pos, ax=ax, width=[0.3 + min(x, 6) * 0.25 for x in w], edge_color="#d6d5cf", alpha=0.8)
    for i, cm in enumerate(comms):
        nodes = [m for m in cm["members"] if m in G]
        sizes = [40 + int(G.nodes[m]["count"]) * 0.45 for m in nodes]
        nx.draw_networkx_nodes(G, pos, nodelist=nodes, node_size=sizes, ax=ax,
                               node_color=SERIES[i % len(SERIES)], edgecolors=SURFACE, linewidths=1.5,
                               label=f"Cluster {i + 1}: " + ", ".join(cm["members"][:3]))
    nx.draw_networkx_labels(G, pos, font_size=8, ax=ax, font_color=INK)
    ax.legend(loc="lower left", fontsize=9, markerscale=0.4, bbox_to_anchor=(0, -0.06))
    ax.set_title("Skill co-occurrence network: node size = demand, edges = lift > 1.3, colour = Louvain community")
    _save(fig, "10_skill_network")

    # association rules
    r = pd.read_csv(T / "association_rules.csv")
    r = r[r["size"] == 2].sort_values("lift", ascending=False)
    r = r.drop_duplicates(subset=["support_pct"]).head(15)
    labels = [f"{a}  ->  {c}" for a, c in zip(r["antecedent"], r["consequent"])]
    hbar(labels, r["confidence"] * 100, "Strongest two-skill rules (confidence %, lift shown in table)",
         "11_rules", fmt="{:.0f}%")

    # salary premium, diverging
    p = pd.read_csv(T / "salary_premium_by_skill.csv")
    p = pd.concat([p.head(12), p.tail(8)]).drop_duplicates("skill").iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 6.6))
    ax.barh(p["skill"], p["premium_pct"], color=[BLUE if v >= 0 else ORANGE for v in p["premium_pct"]], height=0.66)
    ax.axvline(0, color=INK2, linewidth=1)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    for yi, (v, nn) in enumerate(zip(p["premium_pct"], p["n"])):
        ax.text(v + (1 if v >= 0 else -1), yi, f"{v:+.0f}%  (n={nn})", va="center",
                ha="left" if v >= 0 else "right", fontsize=8.5, color=INK2)
    lim = p["premium_pct"].abs().max() * 1.45
    ax.set_xlim(-lim, lim)
    ax.set_title(f"Median salary premium vs all US postings (${ins['salary']['median_us']/1000:.0f}k)")
    _save(fig, "12_salary_premium")

    sr = pd.read_csv(T / "salary_by_role.csv")
    hbar(sr["role_family"], sr["median"] / 1000, "Median advertised salary by role family (USD thousands)",
         "13_salary_by_role", fmt="${:.0f}k")

    em = pd.read_csv(T / "emerging_terms_rising.csv").head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 5.6))
    for i, rr in enumerate(em.itertuples()):
        ax.plot([rr.share_2023_pct, rr.share_2026_pct], [i, i], color=BLUE, linewidth=2)
        ax.scatter([rr.share_2023_pct], [i], color=MUTED, s=26, zorder=3)
        ax.scatter([rr.share_2026_pct], [i], color=BLUE, s=40, zorder=3)
        ax.text(rr.share_2026_pct + 0.2, i, f"x{rr.growth_x:.0f}", va="center", fontsize=8.5, color=INK2)
    ax.set_yticks(range(len(em)), em["term"])
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("% of HN posts: grey = 2023, blue = 2026")
    ax.set_title("Emerging vocabulary found outside the taxonomy")
    _save(fig, "14_emerging_terms")

    ex = pd.read_csv(T / "extc_top_skills.csv").head(14)
    hbar(ex["skill"], ex["postings"], "EXTC lens: most requested embedded, hardware and telecom skills",
         "15_extc_skills", fmt="{:,.0f}", color=SERIES[2])
    comp = pd.read_csv(T / "extc_companion_skills.csv").head(12)
    hbar(comp["skill"], comp["share_of_hw_posts_pct"], "Software skills that appear alongside hardware skills",
         "16_extc_companions", color=SERIES[2])

    sil = pd.read_csv(T / "cluster_silhouette.csv")
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    ax.plot(sil["k"], sil["silhouette"], color=BLUE, linewidth=2, marker="o", markersize=6)
    best = sil.loc[sil["silhouette"].idxmax()]
    ax.scatter([best["k"]], [best["silhouette"]], color=ORANGE, s=70, zorder=3)
    ax.set_xlabel("k (number of clusters)")
    ax.set_title("k-means silhouette score by k")
    _save(fig, "17_silhouette")
    print(f"[viz] figures written to {config.FIGURES}")


if __name__ == "__main__":
    run()
