"""HireSignal dashboard.  Run:  streamlit run app.py"""
from __future__ import annotations

import json

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from hiresignal import compliance, config
from hiresignal.extract import extract, extract_with_spans
from hiresignal.mining import advisor
from hiresignal.taxonomy import CATEGORY, SKILLS

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
BLUE, ORANGE, GREEN = SERIES[0], SERIES[1], SERIES[2]
INK2, GRID = "#52514e", "#e6e5e0"
T = config.TABLES

st.set_page_config(page_title="HireSignal: Job Market Skill Demand", page_icon="📡", layout="wide")
st.markdown("""
<style>
  .block-container {padding-top: 1.6rem; max-width: 1400px;}
  div[data-testid="stMetricValue"] {font-size: 1.7rem;}
  .hs-kicker {font-size: .78rem; letter-spacing: .14em; text-transform: uppercase; color: #8a8984;}
  .hs-title {font-size: 2.1rem; font-weight: 800; margin: 0 0 .2rem 0; line-height: 1.1;}
  .hs-sub {color: #52514e; margin-bottom: 1rem;}
  mark.sk {background: #d6e6fa; padding: 0 .2em; border-radius: 3px;}
  mark.hw {background: #c9efe0; padding: 0 .2em; border-radius: 3px;}
</style>""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data
@st.cache_data(show_spinner="Loading postings ...")
def load_postings():
    df = pd.read_parquet(config.PROCESSED / "postings.parquet")
    df["skills"] = df["skills"].map(list)
    df["tech_skills"] = df["skills"].map(lambda L: [s for s in L if CATEGORY[s] != "Soft Skills & Languages"])
    return df


@st.cache_data
def table(name, **kw):
    return pd.read_csv(T / f"{name}.csv", **kw)


@st.cache_data
def insights():
    return json.loads((config.OUTPUTS / "insights.json").read_text())


def style(fig, h=420, legend=False):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)", showlegend=legend, font=dict(size=13),
                      hoverlabel=dict(bgcolor="white"), legend=dict(orientation="h", y=-0.15))
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def hbar(d, x, y, title, color=BLUE, fmt=".1f", h=None, hover=None):
    d = d.iloc[::-1]
    fig = px.bar(d, x=x, y=y, orientation="h", title=title, text=x, hover_data=hover)
    fig.update_traces(marker_color=color, texttemplate=f"%{{text:{fmt}}}", textposition="outside", cliponaxis=False)
    fig.update_yaxes(title=None, showgrid=False)
    fig.update_xaxes(title=None)
    return style(fig, h or max(320, 26 * len(d) + 80))


df = load_postings()
ins = insights()

# ---------------------------------------------------------------- header
st.markdown('<div class="hs-kicker">Web Data Mining mini project · VJTI · R5CO4201T</div>', unsafe_allow_html=True)
st.markdown('<div class="hs-title">HireSignal: what the job market is asking for</div>', unsafe_allow_html=True)
st.markdown(f'<div class="hs-sub">{len(df):,} public job postings from six sources, '
            f'{ins["hn_months"]} months of Hacker News hiring threads (Jan 2023 to Oct 2026), '
            f'{len(SKILLS)} skills in the taxonomy.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- sidebar filters
with st.sidebar:
    st.header("Filters")
    st.caption("Apply to the Overview and Roles & Places tabs.")
    src = st.multiselect("Source", sorted(df["source_label"].unique()))
    role = st.multiselect("Role family", sorted(df["role_family"].unique()))
    region = st.multiselect("Region", sorted(df["region"].dropna().unique()))
    mode = st.multiselect("Work mode", sorted(df["work_mode"].unique()))
    sen = st.multiselect("Seniority", sorted(df["seniority"].unique()))
    yrs = sorted(df["month"].dropna().str[:4].unique())
    yr = st.select_slider("Years", options=yrs, value=(yrs[0], yrs[-1]))
    st.divider()
    st.caption("Data: Hacker News (HN Search API by Algolia), Arbeitnow, Remote OK, Jobicy, "
               "Himalayas and Python.org Jobs. Every source is credited and was checked against "
               "its robots.txt and terms before collection.")

f = df.copy()
for col, val in [("source_label", src), ("role_family", role), ("region", region),
                 ("work_mode", mode), ("seniority", sen)]:
    if val:
        f = f[f[col].isin(val)]
f = f[f["month"].isna() | f["month"].fillna("").str[:4].between(yr[0], yr[1])]

tabs = st.tabs(["Overview", "Trends", "Roles & Places", "Skill Network", "Association Rules",
                "Salaries", "Clusters", "EXTC Lens", "Skill-Gap Advisor", "Data & Ethics"])

# ================================================================ Overview
with tabs[0]:
    with_sk = f[f["n_skills"] > 0]
    c = st.columns(5)
    c[0].metric("Postings (filtered)", f"{len(f):,}")
    c[1].metric("With ≥1 skill", f"{100 * len(with_sk) / max(len(f), 1):.0f}%")
    c[2].metric("Skills per posting", f"{with_sk['n_skills'].mean():.1f}" if len(with_sk) else "-")
    c[3].metric("With salary", f"{f['salary_usd_mid'].notna().sum():,}")
    c[4].metric("Distinct skills seen", f"{f['skills'].explode().nunique():,}")
    if len(with_sk) == 0:
        st.info("No postings match these filters.")
    else:
        e = with_sk["skills"].explode()
        vc = e.value_counts()
        t = pd.DataFrame({"skill": vc.index, "postings": vc.values})
        t["share"] = 100 * t["postings"] / len(with_sk)
        t["category"] = t["skill"].map(CATEGORY)
        left, right = st.columns([3, 2])
        with left:
            n = st.slider("How many skills", 10, 40, 25, key="ov_n")
            soft_on = st.toggle("Include soft skills", value=False)
            cat_pick = st.selectbox("Category", ["All categories"] + sorted(set(CATEGORY.values())))
            tt = t if soft_on else t[t["category"] != "Soft Skills & Languages"]
            if cat_pick != "All categories":
                tt = t[t["category"] == cat_pick]
            tt = tt.head(n)
            st.plotly_chart(hbar(tt, "share", "skill", "Top skills, % of postings that name a skill",
                                 hover=["postings", "category"]), use_container_width=True)
        with right:
            cs = with_sk["skills"].map(lambda L: sorted({CATEGORY[s] for s in L})).explode().value_counts()
            cd = pd.DataFrame({"category": cs.index, "share": 100 * cs.values / len(with_sk)})
            st.plotly_chart(hbar(cd, "share", "category", "Skill categories, % of postings", color=INK2),
                            use_container_width=True)
            soft = t[t["category"] == "Soft Skills & Languages"].head(8)
            st.plotly_chart(hbar(soft, "share", "skill", "Soft skills and languages", color=GREEN, h=320),
                            use_container_width=True)

# ================================================================ Trends
with tabs[1]:
    act = table("hn_monthly_activity")
    a, b, c = st.columns(3)
    g0, g1 = ins["genai_share_first_last"]
    r0, r1 = ins["remote_share_first_last"]
    a.metric("HN posts naming a GenAI skill", f"{g1:.0f}%", f"{g1 - g0:+.0f} pts since Jan 2023")
    b.metric("Remote share of HN posts", f"{r1:.0f}%", f"{r1 - r0:+.0f} pts since Jan 2023")
    v0, v1 = ins["hn_volume_first_last"]
    c.metric("HN job posts per month", f"{v1}", f"{v1 - v0:+d} vs Jan 2023")
    cols = st.columns(3)
    for col, (m, title, colr) in zip(cols, [("postings", "Job posts per month", INK2),
                                            ("remote_pct", "Remote share (%)", BLUE),
                                            ("genai_pct", "Posts naming a GenAI skill (%)", ORANGE)]):
        fig = px.line(act, x="month", y=m, title=title)
        fig.update_traces(line_color=colr, line_width=2.5)
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None, rangemode="tozero")
        col.plotly_chart(style(fig, 280), use_container_width=True)

    share = table("hn_skill_share_by_month", index_col=0)
    default = [s for s in ["AI agents", "LLMs", "TypeScript", "JavaScript", "Rust"] if s in share.index]
    pick = st.multiselect("Compare skills over time (share of HN posts per month)", sorted(share.index), default=default)
    smooth = st.toggle("3-month rolling mean", value=True)
    if pick:
        d = share.loc[pick].T
        if smooth:
            d = d.rolling(3, min_periods=1).mean()
        d = d.reset_index(names="month").melt("month", var_name="skill", value_name="share")
        fig = px.line(d, x="month", y="share", color="skill", color_discrete_sequence=SERIES)
        fig.update_traces(line_width=2.5, hovertemplate="%{y:.1f}%")
        fig.update_layout(hovermode="x unified")
        fig.update_yaxes(title="% of posts", rangemode="tozero")
        fig.update_xaxes(title=None)
        st.plotly_chart(style(fig, 440, legend=True), use_container_width=True)
        if len(pick) > 8:
            st.caption("Showing more than 8 skills reuses colours; hover to identify lines.")
    g = table("hn_skill_growth")
    l, r = st.columns(2)
    l.subheader("Fastest rising")
    l.dataframe(g.head(15)[["skill", "first6_pct", "last6_pct", "slope_pp_per_year"]]
                .rename(columns={"first6_pct": "Jan–Jun 2023 %", "last6_pct": "last 6 months %",
                                 "slope_pp_per_year": "trend (pts/yr)"}), hide_index=True, use_container_width=True)
    r.subheader("Fastest falling")
    r.dataframe(g.tail(15).iloc[::-1][["skill", "first6_pct", "last6_pct", "slope_pp_per_year"]]
                .rename(columns={"first6_pct": "Jan–Jun 2023 %", "last6_pct": "last 6 months %",
                                 "slope_pp_per_year": "trend (pts/yr)"}), hide_index=True, use_container_width=True)
    st.subheader("Emerging vocabulary (terms found outside the taxonomy)")
    em = table("emerging_terms_rising").head(20)
    fig = go.Figure()
    for _, rr in em.iloc[::-1].iterrows():
        fig.add_trace(go.Scatter(x=[rr["share_2023_pct"], rr["share_2026_pct"]], y=[rr["term"]] * 2,
                                 mode="lines+markers", line=dict(color=BLUE, width=2),
                                 marker=dict(color=["#b0afa9", BLUE], size=[8, 11]),
                                 hovertemplate=f"{rr['term']}: 2023 {rr['share_2023_pct']}% → 2026 "
                                               f"{rr['share_2026_pct']}% (×{rr['growth_x']:.0f})<extra></extra>"))
    fig.update_xaxes(title="% of HN posts: grey = 2023, blue = 2026")
    st.plotly_chart(style(fig, 560), use_container_width=True)

# ================================================================ Roles & Places
with tabs[2]:
    l, r = st.columns(2)
    rv = f["role_family"].value_counts().drop("Other", errors="ignore").rename_axis("role").reset_index(name="postings")
    l.plotly_chart(hbar(rv, "postings", "role", "Postings by role family", fmt=",.0f"), use_container_width=True)
    sv = f["seniority"].value_counts().rename_axis("seniority").reset_index(name="postings")
    r.plotly_chart(hbar(sv, "postings", "seniority", "Seniority named in the title", fmt=",.0f", color=INK2, h=300),
                   use_container_width=True)
    wm = f["work_mode"].value_counts(normalize=True).mul(100).rename_axis("mode").reset_index(name="share")
    fig = px.pie(wm, names="mode", values="share", hole=0.6, title="Work mode", color="mode",
                 color_discrete_map={"Remote": BLUE, "Hybrid": GREEN, "Onsite": ORANGE, "Unspecified": "#c9c8c2"})
    fig.update_traces(textinfo="label+percent")
    r.plotly_chart(style(fig, 330), use_container_width=True)

    st.subheader("What does each role ask for?")
    roles_avail = [x for x in df["role_family"].value_counts().index if x != "Other"]
    pr = st.selectbox("Role family", roles_avail, index=roles_avail.index("ML / AI Engineering")
                      if "ML / AI Engineering" in roles_avail else 0)
    sub = f[f["role_family"] == pr]
    if len(sub):
        vc = sub["tech_skills"].explode().value_counts().head(20)
        d = pd.DataFrame({"skill": vc.index, "share": 100 * vc.values / len(sub)})
        st.plotly_chart(hbar(d, "share", "skill", f"Top skills in {pr} postings (n={len(sub):,})"),
                        use_container_width=True)

    st.subheader("Where are the jobs?")
    cc = f["country"].value_counts().rename_axis("country").reset_index(name="postings")
    fig = px.choropleth(cc, locations="country", locationmode="country names", color="postings",
                        color_continuous_scale=["#cde2fb", "#86b6ef", "#2a78d6", "#184f95", "#0d366b"],
                        title="Postings by country named in the location")
    fig.update_geos(showframe=False, showcoastlines=False, projection_type="natural earth")
    st.plotly_chart(style(fig, 460), use_container_width=True)
    l, r = st.columns(2)
    l.plotly_chart(hbar(cc.head(15), "postings", "country", "Top countries", fmt=",.0f"), use_container_width=True)
    ci = f["city"].value_counts().head(15).rename_axis("city").reset_index(name="postings")
    r.plotly_chart(hbar(ci, "postings", "city", "Top cities", fmt=",.0f"), use_container_width=True)
    reg = st.selectbox("Top skills by region", sorted(f["region"].dropna().unique()))
    rs = f[f["region"] == reg]
    vc = rs["tech_skills"].explode().value_counts().head(15)
    st.plotly_chart(hbar(pd.DataFrame({"skill": vc.index, "share": 100 * vc.values / max(len(rs), 1)}),
                         "share", "skill", f"{reg}: top skills (% of {len(rs):,} postings)"), use_container_width=True)

# ================================================================ Network
with tabs[3]:
    G = nx.read_gexf(T / "skill_network.gexf")
    comms = json.loads((T / "network_communities.json").read_text())
    st.markdown(f"**{G.number_of_nodes()} skills, {G.number_of_edges()} links.** A link means two skills appear "
                f"together more often than chance (lift > 1.3, at least 25 postings). Colours are Louvain "
                f"communities, modularity {ins['network']['modularity']}.")
    min_lift = st.slider("Show links with lift at least", 1.3, 6.0, 1.6, 0.1)
    pos = nx.spring_layout(G, weight="lift", k=0.55, seed=7, iterations=200)
    ex, ey = [], []
    for a_, b_, d_ in G.edges(data=True):
        if d_["lift"] >= min_lift:
            ex += [pos[a_][0], pos[b_][0], None]
            ey += [pos[a_][1], pos[b_][1], None]
    fig = go.Figure(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="#d6d5cf", width=0.8), hoverinfo="skip"))
    for i, cm in enumerate(comms):
        nodes = [m for m in cm["members"] if m in G]
        fig.add_trace(go.Scatter(
            x=[pos[m][0] for m in nodes], y=[pos[m][1] for m in nodes], mode="markers+text",
            text=nodes, textposition="top center", textfont=dict(size=11),
            name=f"Community {i + 1}: {', '.join(cm['members'][:3])}",
            marker=dict(size=[8 + int(G.nodes[m]['count']) ** 0.5 * 0.9 for m in nodes],
                        color=SERIES[i % 8], line=dict(color="white", width=1.5)),
            customdata=[[G.nodes[m]["count"], G.degree(m), G.nodes[m]["pagerank"]] for m in nodes],
            hovertemplate="<b>%{text}</b><br>postings %{customdata[0]}<br>links %{customdata[1]}"
                          "<br>PageRank %{customdata[2]:.4f}<extra></extra>"))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    st.plotly_chart(style(fig, 720, legend=True), use_container_width=True)
    l, r = st.columns(2)
    with l:
        s = st.selectbox("Explore a skill's neighbours", sorted(G.nodes), index=sorted(G.nodes).index("Python"))
        nb = pd.DataFrame([{"neighbour": n_, "together": G[s][n_]["count"], "lift": G[s][n_]["lift"]}
                           for n_ in G[s]]).sort_values("lift", ascending=False)
        st.dataframe(nb, hide_index=True, use_container_width=True, height=360)
    with r:
        nodes = table("network_nodes")
        st.markdown("**Most central skills**")
        st.dataframe(nodes[["skill", "count", "degree", "pagerank", "betweenness", "community"]].head(15),
                     hide_index=True, use_container_width=True, height=360)
        st.caption("PageRank: overall pull in the network. Betweenness: skills that connect communities.")

# ================================================================ Rules
with tabs[4]:
    rules = table("association_rules")
    st.markdown(f"Apriori (implemented from scratch) on **{ins['rules']['transactions']:,}** skill sets, "
                f"min support 0.8%. Itemsets found by size: {ins['rules']['itemsets_by_size']}. "
                f"**{len(rules):,} rules** with confidence ≥ 0.35 and lift ≥ 1.5.")
    c1, c2, c3 = st.columns(3)
    mc = c1.slider("Min confidence", 0.35, 1.0, 0.5, 0.05)
    ml = c2.slider("Min lift", 1.5, 30.0, 2.0, 0.5)
    q = c3.text_input("Contains skill (either side)", "")
    rr = rules[(rules["confidence"] >= mc) & (rules["lift"] >= ml)]
    if q:
        rr = rr[rr["antecedent"].str.contains(q, case=False, regex=False) |
                rr["consequent"].str.contains(q, case=False, regex=False)]
    st.dataframe(rr[["antecedent", "consequent", "support_pct", "confidence", "lift", "count"]],
                 hide_index=True, use_container_width=True, height=420)
    fig = px.scatter(rr.head(400), x="support_pct", y="confidence", size="lift", color="size",
                     color_discrete_sequence=SERIES, hover_data=["antecedent", "consequent", "lift"],
                     title="Rules: support vs confidence (bubble size = lift)")
    fig.update_traces(marker=dict(line=dict(color="white", width=1)))
    st.plotly_chart(style(fig, 420), use_container_width=True)
    st.caption("How to read: 'Grafana + Kubernetes → Prometheus, confidence 0.81' means 81% of postings that "
               "ask for Grafana and Kubernetes also ask for Prometheus.")

# ================================================================ Salaries
with tabs[5]:
    s = ins["salary"]
    c = st.columns(3)
    c[0].metric("Postings with a salary", f"{s['n']:,}")
    c[1].metric("US / US-remote with salary", f"{s['n_us']:,}")
    c[2].metric("US median (annual)", f"${s['median_us'] / 1000:.0f}k")
    p = table("salary_premium_by_skill")
    k = st.slider("Skills on each side", 5, 20, 12)
    pp = pd.concat([p.head(k), p.tail(k)]).drop_duplicates("skill").sort_values("premium_pct")
    fig = px.bar(pp, x="premium_pct", y="skill", orientation="h", hover_data=["n", "median_usd", "category"],
                 title="Median salary premium vs all US postings (%)")
    fig.update_traces(marker_color=[BLUE if v >= 0 else ORANGE for v in pp["premium_pct"]])
    fig.update_yaxes(title=None)
    fig.update_xaxes(title=None)
    st.plotly_chart(style(fig, 30 * len(pp) + 100), use_container_width=True)
    st.caption("Repeated monthly HN posts of the same job are collapsed to one before computing salaries. "
               "Only skills with at least 30 salaried US postings are shown. Correlation, not causation.")
    l, r = st.columns(2)
    sr = table("salary_by_role")
    l.plotly_chart(hbar(sr.assign(k=sr["median"] / 1000), "k", "role_family", "Median salary by role (USD k)",
                        fmt=".0f", hover=["count"]), use_container_width=True)
    sal = df[df["salary_usd_mid"].between(20000, 500000)]
    fig = px.histogram(sal, x="salary_usd_mid", nbins=50, title="Distribution of advertised salaries (USD/yr)")
    fig.update_traces(marker_color=BLUE, marker_line_color="white", marker_line_width=1)
    fig.update_xaxes(title=None)
    r.plotly_chart(style(fig, 420), use_container_width=True)

# ================================================================ Clusters
with tabs[6]:
    cl = ins["clusters"]
    st.markdown(f"k-means on TF-IDF-weighted skill vectors (40-dim SVD) of **{cl['n']:,}** postings with ≥3 "
                f"skills. Best k by silhouette = **{cl['best_k']}**. Adjusted Rand index against the title-based "
                f"role families = **{cl['ari_vs_roles']}**: what a job asks for cuts across what it is called "
                f"(most postings are titled just 'Software Engineer').")
    l, r = st.columns([1, 2])
    sil = table("cluster_silhouette")
    fig = px.line(sil, x="k", y="silhouette", markers=True, title="Silhouette by k")
    fig.update_traces(line_color=BLUE, marker_size=8)
    l.plotly_chart(style(fig, 330), use_container_width=True)
    prof = table("cluster_profiles")
    r.dataframe(prof[["cluster", "size", "signature_skills", "most_common_role", "role_purity_pct"]],
                hide_index=True, use_container_width=True, height=330)
    proj = table("cluster_projection")
    labels = dict(zip(prof["cluster"], prof["label"]))
    proj["cluster_label"] = proj["cluster"].map(lambda c_: f"{c_}: {labels.get(c_, '')}")
    top_c = prof.head(8)["cluster"].tolist()
    proj = proj[proj["cluster"].isin(top_c)]
    fig = px.scatter(proj, x="x", y="y", color="cluster_label", hover_data=["title", "role_family"],
                     color_discrete_sequence=SERIES, title="Postings in 2-D skill space (8 largest clusters)")
    fig.update_traces(marker=dict(size=6, opacity=0.7, line=dict(color="white", width=0.5)))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    st.plotly_chart(style(fig, 560, legend=True), use_container_width=True)

# ================================================================ EXTC Lens
with tabs[7]:
    x = ins["extc"]
    c = st.columns(3)
    c[0].metric("Postings with an embedded / hardware / telecom skill", f"{x['n']:,}", f"{x['share_pct']}% of all")
    c[1].metric("Median salary, hardware-skill postings", f"${x['median_salary_hw'] / 1000:.0f}k")
    c[2].metric("Median salary, all postings", f"${x['median_salary_all'] / 1000:.0f}k")
    l, r = st.columns(2)
    hs = table("extc_top_skills").head(20)
    l.plotly_chart(hbar(hs, "postings", "skill", "Most requested EXTC skills", color=GREEN, fmt=",.0f"),
                   use_container_width=True)
    cp = table("extc_companion_skills").head(15)
    r.plotly_chart(hbar(cp, "share_of_hw_posts_pct", "skill",
                        "Software skills that travel with hardware skills (% of those posts)", color=GREEN),
                   use_container_width=True)
    tr = table("extc_trend_by_year")
    tr["year"] = tr["year"].astype(str)
    fig = px.bar(tr, x="year", y="hw_share_pct", text="hw_share_pct",
                 title="Share of HN posts naming an EXTC skill, by year (%)")
    fig.update_traces(marker_color=GREEN, texttemplate="%{text:.1f}%", textposition="outside")
    st.plotly_chart(style(fig, 330), use_container_width=True)

# ================================================================ Advisor
with tabs[8]:
    st.markdown("Pick the skills you have. The advisor scores how well you fit each role family and suggests "
                "what to learn next, using role skill profiles plus association rules whose left side you "
                "already satisfy.")
    prof = table("role_profiles")
    rules = table("association_rules")
    mine = st.multiselect("Your skills", sorted(SKILLS), default=advisor.EXTC_STUDENT)
    st.caption("Default: a typical EXTC student's toolkit.")
    if mine:
        fits, recs = advisor.advise(mine, prof, rules, top=10)
        l, r = st.columns(2)
        l.plotly_chart(hbar(fits.head(10), "fit_pct", "role_family", "Role fit (%)", hover=["missing_top"]),
                       use_container_width=True)
        recs = recs.assign(why=recs["rule_bonus"].map(lambda b: "demand + rule" if b > 0 else "demand"))
        r.plotly_chart(hbar(recs, "score", "skill", "Learn next (score)", color=ORANGE, fmt=".2f",
                            hover=["demand_in_best_roles", "rule_bonus", "why"]), use_container_width=True)

    st.subheader("Try the skill extractor on any job description")
    sample = ("Embedded Software Engineer | Bengaluru | Hybrid\nWe build IoT gateways. You will write firmware in "
              "C and C++ on STM32 microcontrollers running FreeRTOS, bring up I2C/SPI sensors, and ship OTA updates "
              "over MQTT to our AWS backend. Python for test automation and Git/GitHub Actions for CI/CD. "
              "Experience with oscilloscopes and PCB bring-up is a plus. We raised our Series C last year.")
    txt = st.text_area("Paste a job description", sample, height=150)
    if txt:
        found = extract(txt)
        spans = [s_ for s_ in extract_with_spans(txt) if s_[0] in found]
        out, last = [], 0
        for name, a_, b_, m_ in spans:
            if a_ < last:
                continue
            cls = "hw" if CATEGORY[name] == "Embedded, Hardware & Telecom" else "sk"
            out.append(txt[last:a_].replace("\n", "<br>"))
            out.append(f'<mark class="{cls}" title="{name}">{m_}</mark>')
            last = b_
        out.append(txt[last:].replace("\n", "<br>"))
        st.markdown("".join(out), unsafe_allow_html=True)
        st.write(f"**{len(found)} skills found:** " + ", ".join(found))
        st.caption("Note how 'Series C' is not counted as the C language: the extractor checks the words around "
                   "short, ambiguous names.")

# ================================================================ Data & Ethics
with tabs[9]:
    stats = json.loads((config.PROCESSED / "preprocess_stats.json").read_text())
    st.subheader("Preprocessing funnel")
    funnel = pd.DataFrame({"stage": ["Raw records", "After id de-dup", "After empty filter", "After text/key de-dup",
                                     "With ≥1 skill"],
                           "records": [stats["raw_records"], stats["after_id_dedupe"], stats["after_empty_filter"],
                                       stats["after_dedupe"], stats["with_skills"]]})
    fig = px.funnel(funnel, x="records", y="stage")
    fig.update_traces(marker_color=BLUE)
    st.plotly_chart(style(fig, 320), use_container_width=True)
    c = st.columns(4)
    pii = stats["pii_replaced"]
    c[0].metric("E-mails scrubbed", f"{pii['email']:,}")
    c[1].metric("Links scrubbed", f"{pii['link']:,}")
    c[2].metric("Phone numbers scrubbed", f"{pii['phone']:,}")
    c[3].metric("@handles scrubbed", f"{pii['handle']:,}")
    st.caption(f"HN headers parsed into company / role / location / salary: "
               f"{stats['hn_header_parsed']:,} of {stats['hn_posts']:,} posts. German-language postings: "
               f"{stats['german_language']:,}.")
    st.subheader("Source compliance (robots.txt + terms of service)")
    st.dataframe(compliance.table(), hide_index=True, use_container_width=True)
    log = pd.read_csv(config.COMPLIANCE / "request_log.csv")
    live = log[log["from_cache"] == False]  # noqa: E712
    st.subheader("Request audit log")
    c = st.columns(3)
    c[0].metric("Live HTTP requests", f"{len(live):,}")
    c[1].metric("Served from cache", f"{(log['from_cache'] == True).sum():,}")  # noqa: E712
    c[2].metric("Blocked by robots.txt", f"{(log['robots_allowed'] == False).sum():,}")  # noqa: E712
    st.dataframe(live.groupby("host").agg(requests=("url", "count"), min_delay_s=("crawl_delay_s", "min"))
                 .reset_index(), hide_index=True, use_container_width=True)
    st.subheader("Browse the cleaned postings")
    q = st.text_input("Search title or company")
    view = df if not q else df[df["title"].fillna("").str.contains(q, case=False) |
                              df["company"].fillna("").str.contains(q, case=False)]
    st.dataframe(view[["source_label", "month", "company", "title", "role_family", "city", "country",
                       "work_mode", "salary_usd_mid", "skills"]].head(500), hide_index=True, use_container_width=True)
