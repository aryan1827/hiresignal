# Ethical considerations followed

This note covers how HireSignal collected and handled data. It applies the two-part
test from Experiment 2: a technical permission test (robots.txt) and a legal
permission test (terms of service). Only data that passes both, and contains no
personal information, is collected.

## 1. Source selection

| Source | robots.txt | Terms | Decision |
|---|---|---|---|
| Hacker News via HN Search API (Algolia) | API host has no robots.txt (no restriction); HN pages themselves were not fetched | Public API meant for programmatic use | Used |
| Arbeitnow API | Allows everything | "Free public API, please do not abuse", attribution requested | Used, credited |
| Remote OK API | Allow /, Crawl-delay 1 | Must link back and name Remote OK | Used, credited |
| Jobicy API | /api not disallowed | Credit Jobicy, keep original job links | Used, credited |
| Himalayas API | Allow / | Public, documented API | Used, credited |
| Python.org Jobs (HTML) | /jobs/ allowed | Public community board | Used, 2 s delay |
| Remotive API | **Disallow: /api/*** | API documented | **Excluded**: robots.txt and API docs conflict, so we treat it as off-limits |
| LinkedIn | Automated access prohibited | User Agreement forbids scraping | Excluded |
| Naukri.com | Disallows automated agents | Terms forbid scraping | Excluded |
| Indeed | Some paths allowed for search engines | Terms prohibit scraping | Excluded |

The robots.txt files fetched during collection are saved in `data/compliance/robots/`.
The full table is `data/compliance/source_compliance.csv`.

## 2. Polite collection

* The `PoliteSession` client checks robots.txt before **every** request and refuses
  disallowed URLs.
* It identifies itself honestly (`HireSignal/1.0 (VJTI Web Data Mining student project …)`)
  instead of pretending to be a browser.
* At least 2 seconds between requests to the same host, or the site's Crawl-delay if larger.
  It backs off when a server returns HTTP 429.
* Every response is cached on disk, so re-running the pipeline makes no new requests.
* The whole dataset needed **121 live requests**. Each one is logged in
  `data/compliance/request_log.csv` with its timestamp, robots verdict, delay and status.
* No logins, CAPTCHAs, paywalls or rate limits were bypassed.

## 3. Personal data

* Job ads describe companies and roles, not people. We still treated them carefully:
  * HN comment authors' usernames are dropped at collection and never stored.
  * Preprocessing replaces e-mail addresses (5,109), phone numbers (380), links (30,379)
    and @handles (239) with placeholders before anything is saved.
  * No profiles, CVs, or candidate posts ("Who wants to be hired?") were collected.
* Company names are kept because they are business information, published by the
  companies themselves.

## 4. Use and redistribution

* The data is used for non-commercial academic analysis only.
* The raw cache (`data/raw/`) is excluded from version control and is not redistributed.
  Published outputs are aggregates (counts, shares, rules, charts).
* Every source is credited in the README, the dashboard and the report.

## 5. Limitations and fairness

* The sample leans toward US tech and remote work (HN, remote boards) and German jobs
  (Arbeitnow). Indian job boards were excluded on ethical grounds, so India appears only
  through international postings. Results are shown per source so this bias stays visible.
* Salary figures come from the minority of ads that publish one. They are converted with
  fixed exchange rates, and the premium analysis is limited to US postings so that
  location is not mistaken for skill value.
* The skill extractor is rule-based. Ambiguous names (Go, R, C) are counted only with
  surrounding evidence, and unit tests check the known traps.
