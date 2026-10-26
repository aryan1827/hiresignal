"""Source-by-source compliance record (the Experiment 2 two-part test).

Test 1: does robots.txt allow the path we fetch?
Test 2: do the terms of service / API terms allow this use?
A source is used only if it passes both and we can avoid personal data.
The robots.txt files fetched during collection are saved in data/compliance/robots/.
"""
from __future__ import annotations

import pandas as pd

from . import config

SOURCES = [
    {"source": "Hacker News 'Who is hiring?' (via HN Search API by Algolia)",
     "endpoint": "hn.algolia.com/api/v1/items/{thread}", "access": "Official public JSON API",
     "robots": "No robots.txt on the API host (404 = no restriction); news.ycombinator.com pages not fetched",
     "terms": "Public API offered for programmatic use; 1 request per monthly thread",
     "personal_data": "Author usernames dropped at collection; e-mails/phones/links scrubbed",
     "verdict": "Used (fully compliant)"},
    {"source": "Arbeitnow", "endpoint": "arbeitnow.com/api/job-board-api", "access": "Free public API",
     "robots": "User-agent: * Disallow: (nothing) -> allowed",
     "terms": "'Free public API, please do not abuse'; attribution requested -> credited",
     "personal_data": "Company job ads only", "verdict": "Used (fully compliant)"},
    {"source": "Remote OK", "endpoint": "remoteok.com/api", "access": "Free public API",
     "robots": "Allow: /, Crawl-delay: 1 -> allowed (we wait >= 2 s)",
     "terms": "Must link back and name Remote OK as a source -> credited",
     "personal_data": "Company job ads only", "verdict": "Used (fully compliant)"},
    {"source": "Jobicy", "endpoint": "jobicy.com/api/v2/remote-jobs", "access": "Free public API",
     "robots": "/api/ not disallowed -> allowed",
     "terms": "Credit Jobicy with a link; keep original job URLs -> done",
     "personal_data": "Company job ads only", "verdict": "Used (fully compliant)"},
    {"source": "Himalayas", "endpoint": "himalayas.app/jobs/api", "access": "Free public API",
     "robots": "Allow: / (only ?page= listing paths disallowed) -> allowed",
     "terms": "Public API with documented cursor pagination; attribution given",
     "personal_data": "Company job ads only", "verdict": "Used (fully compliant)"},
    {"source": "Python.org Jobs", "endpoint": "python.org/jobs/ (HTML)", "access": "HTML crawl + BeautifulSoup",
     "robots": "Only /~guido/orlijn/ and /webstats/ disallowed -> /jobs/ allowed",
     "terms": "Public community job board; 2 s delay, 22 requests in total",
     "personal_data": "Contact names/e-mails in ads scrubbed", "verdict": "Used (fully compliant)"},
    {"source": "Remotive", "endpoint": "remotive.com/api/remote-jobs", "access": "Public API exists",
     "robots": "Disallow: /api/* -> FAILS test 1",
     "terms": "API documented, but robots.txt forbids crawlers on /api/",
     "personal_data": "-", "verdict": "Excluded: robots.txt and API docs conflict, so we take the safe side"},
    {"source": "LinkedIn Jobs", "endpoint": "linkedin.com/jobs", "access": "-",
     "robots": "Automated access 'strictly prohibited' without express permission",
     "terms": "User Agreement forbids scraping", "personal_data": "Profiles = personal data",
     "verdict": "Excluded (unsuitable)"},
    {"source": "Naukri.com", "endpoint": "naukri.com", "access": "-",
     "robots": "Disallow: / for AI and automated agents", "terms": "Terms forbid scraping",
     "personal_data": "-", "verdict": "Excluded (unsuitable)"},
    {"source": "Indeed India", "endpoint": "in.indeed.com", "access": "-",
     "robots": "Search pages partly allowed for search engines", "terms": "Terms of Service prohibit scraping",
     "personal_data": "-", "verdict": "Excluded (fails test 2)"},
]


def table() -> pd.DataFrame:
    t = pd.DataFrame(SOURCES)
    t.to_csv(config.COMPLIANCE / "source_compliance.csv", index=False)
    return t
