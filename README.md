# HireSignal: Job Market Skill Demand Analyzer

Web Data Mining (R5CO4201T) mini project · B.Tech, Semester VII · VJTI
Group 12: Kartik Bulusu (231010030), Aniket Desai (231090005), Aryan Bendre (231090010), Tirth Khona (231090032)

HireSignal collects public job postings, extracts the skills they ask for, and
mines the result for the most requested skills, roles and locations. It also tracks
how demand changed over 46 months, which skills cluster together, which skills pay
more, and where Electronics & Telecommunication (EXTC) skills fit in.

## Results at a glance

| | |
|---|---|
| Postings analysed | **17,677** from 6 sources (14,941 HN posts across 46 monthly threads, Jan 2023 to Oct 2026) |
| Live HTTP requests needed | **121** (one per HN thread, cached, robots.txt-checked, ≥2 s apart) |
| Skill taxonomy | **258** skills in 16 categories, with context rules for ambiguous names (Go, R, C, Swift, Spring) |
| Top skills | Python 26%, React 23%, TypeScript 22%, Machine Learning 17%, AWS 17%, PostgreSQL 15% |
| Biggest shift | Posts naming a GenAI skill: **2.5% → 32%**; "AI agents": 0.4% → 16% |
| Remote work | Remote share of HN posts fell from **68% to 51%** |
| Emerging terms (not in taxonomy) | "agentic" (×41), "AI-native", "Claude Code", "forward deployed", "Cursor", "evals" |
| Salary premium (US) | Distributed systems +18%, AI agents +12%, Rust +12%; Excel −39%, Salesforce −24% |
| Network | 70 skills, 560 lift-weighted links, 6 Louvain communities (modularity 0.38) |
| Association rules | 739 rules, e.g. Grafana + Kubernetes → Prometheus (confidence 0.81, lift 58) |
| EXTC lens | 8.5% of postings name an embedded/hardware/telecom skill; Python, C++ and Linux are the bridge skills |

## How to run

```bash
pip install -r requirements.txt
streamlit run app.py                 # dashboard at http://localhost:8501
python run_pipeline.py all           # rebuild everything (collect is served from cache)
python -m pytest -q tests            # unit tests for the skill extractor
```

Stages can be run on their own: `python run_pipeline.py collect | preprocess | mine | viz`.
A fresh collection (empty `data/raw/cache/`) takes about 6 minutes because of the polite delays.

## Pipeline

```
collect ──► preprocess ──► extract skills ──► mine ──► visualise
(6 sources)  (clean, PII    (taxonomy +       (demand, trends,   (17 PNG figures,
 robots.txt   scrub, parse,  context rules)    network, rules,    Streamlit dashboard)
 + cache)     de-dup, norm.)                   clusters, salary)
```

| Stage | Module | What it does |
|---|---|---|
| Collection | `hiresignal/polite.py` | One HTTP client for everything: reads and saves robots.txt, refuses disallowed URLs, waits ≥2 s per host (or the site's Crawl-delay), caches responses, logs every request to `data/compliance/request_log.csv` |
| | `collect/hn.py` | HN "Who is hiring?" threads through the HN Search API (one request returns a whole month) |
| | `collect/apis.py` | Arbeitnow, Remote OK, Jobicy, Himalayas public APIs with pagination/cursors |
| | `collect/pyjobs.py` | HTML crawl of python.org/jobs with BeautifulSoup: listing cards, then each detail page |
| Preprocessing | `preprocess.py` | HTML → text, PII scrubbing (5,109 e-mails, 380 phones, 30,379 links), HN header parsing (`Company \| Role \| Location \| Remote \| $`), language detection, de-duplication, Porter-stemmed tokens |
| | `geo.py`, `roles.py`, `salary.py` | Location → city/country/region/work mode; title → 15 role families + seniority; salary text → annual USD |
| Extraction | `taxonomy.py`, `extract.py` | 258 skills, regex patterns, exclusion windows ("Series C" is not C) and context rules |
| Mining | `mining/demand.py` | Top skills overall, by role, region and source; roles; locations; salaries |
| | `mining/trends.py` | Monthly skill share, least-squares growth slope, risers and fallers |
| | `mining/network.py` | Co-occurrence graph weighted by lift, Louvain communities, PageRank, betweenness |
| | `mining/rules.py` | Apriori written from scratch, support / confidence / lift |
| | `mining/clusters.py` | TF-IDF skill vectors → SVD → k-means (k by silhouette), compared with role families (ARI) |
| | `mining/emerging.py` | Unigram/bigram growth 2023 → 2026 outside the taxonomy |
| | `mining/extc.py`, `mining/advisor.py` | EXTC lens; skill-gap advisor (role fit + what to learn next) |
| Visualisation | `viz.py`, `app.py` | 17 static figures; 10-tab interactive dashboard |

## Outputs

* `data/processed/postings.parquet`: the clean dataset (one row per posting)
* `outputs/tables/*.csv`: every mined table (skill demand, growth, rules, network, clusters, salary …)
* `outputs/figures/*.png`: report-ready charts
* `outputs/insights.json`: headline numbers used in the report and slides
* `data/compliance/`: robots.txt snapshots, source compliance table, request audit log

## Ethics

See [docs/ETHICS.md](docs/ETHICS.md). In short: only public job ads; every source passed a
robots.txt test and a terms test (Remotive, LinkedIn, Naukri and Indeed were excluded);
an honest user agent; at least 2 s between requests; a local cache so re-runs cost nothing;
no usernames stored; e-mails, phone numbers, links and handles scrubbed; sources credited.

## Data credits

Hacker News (via the HN Search API by Algolia) · [Arbeitnow](https://www.arbeitnow.com) ·
[Remote OK](https://remoteok.com) · [Jobicy](https://jobicy.com) · [Himalayas](https://himalayas.app) ·
[Python.org Jobs](https://www.python.org/jobs/)
