"""Collectors for the four public job-board APIs.

Each source documents a free public API and asks for attribution, which the
project gives in the report, the slides and the dashboard footer:

* Arbeitnow   https://www.arbeitnow.com/api/job-board-api   (robots.txt: allow all)
* Remote OK   https://remoteok.com/api                      (robots.txt: allow, Crawl-delay 1)
* Jobicy      https://jobicy.com/api/v2/remote-jobs         (robots.txt: /api not disallowed)
* Himalayas   https://himalayas.app/jobs/api                (robots.txt: allow)

Remotive also offers an API, but its robots.txt disallows /api/*, so it fails
the robots test and is not used (see docs/ETHICS.md).

All four return one common raw record shape so preprocessing can treat them alike.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .. import config
from ..polite import PoliteSession, RobotsDisallowed


def _record(**kw) -> dict:
    base = {"source": None, "source_id": None, "url": None, "title": None,
            "company": None, "location_raw": None, "remote_raw": None,
            "tags": [], "description_html": "", "posted_at": None,
            "thread_month": None, "salary_min": None, "salary_max": None,
            "salary_currency": None, "salary_period": None}
    base.update(kw)
    return base


def _iso(epoch) -> str | None:
    try:
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).isoformat()
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- Arbeitnow
def arbeitnow(s: PoliteSession) -> list[dict]:
    rows = []
    for page in range(1, config.LIMITS["arbeitnow_pages"] + 1):
        d = s.get(f"https://www.arbeitnow.com/api/job-board-api?page={page}")
        for j in d.get("data", []):
            rows.append(_record(
                source="arbeitnow", source_id=f"arbeitnow-{j['slug']}", url=j.get("url"),
                title=j.get("title"), company=j.get("company_name"),
                location_raw=j.get("location"), remote_raw=j.get("remote"),
                tags=(j.get("tags") or []) + (j.get("job_types") or []),
                description_html=j.get("description") or "",
                posted_at=_iso(j.get("created_at"))))
        if not d.get("links", {}).get("next"):
            break
    return rows


# ---------------------------------------------------------------- Remote OK
def remoteok(s: PoliteSession) -> list[dict]:
    d = s.get("https://remoteok.com/api")
    rows = []
    for j in d[1:]:                       # element 0 is the API's legal notice
        rows.append(_record(
            source="remoteok", source_id=f"remoteok-{j.get('id')}", url=j.get("url"),
            title=j.get("position"), company=j.get("company"),
            location_raw=j.get("location"), remote_raw=True,
            tags=j.get("tags") or [], description_html=j.get("description") or "",
            posted_at=_iso(j.get("epoch")),
            salary_min=j.get("salary_min") or None, salary_max=j.get("salary_max") or None,
            salary_currency="USD" if j.get("salary_min") else None,
            salary_period="year" if j.get("salary_min") else None))
    return rows


# ------------------------------------------------------------------- Jobicy
def jobicy(s: PoliteSession) -> list[dict]:
    rows, cursor = [], None
    for _ in range(config.LIMITS["jobicy_pages"]):
        url = "https://jobicy.com/api/v2/remote-jobs?count=50"
        if cursor:
            url += f"&cursor={cursor}"
        d = s.get(url)
        for j in d.get("jobs", []):
            ind = j.get("jobIndustry") or []
            rows.append(_record(
                source="jobicy", source_id=f"jobicy-{j.get('id')}", url=j.get("url"),
                title=j.get("jobTitle"), company=j.get("companyName"),
                location_raw=j.get("jobGeo"), remote_raw=True,
                tags=ind if isinstance(ind, list) else [ind],
                description_html=j.get("jobDescription") or "",
                posted_at=j.get("pubDate"),
                salary_min=j.get("salaryMin"), salary_max=j.get("salaryMax"),
                salary_currency=j.get("salaryCurrency"),
                salary_period=(j.get("salaryPeriod") or "").lower() or None))
        cursor = d.get("nextCursor")
        if not d.get("hasMore") or not cursor:
            break
    return rows


# ---------------------------------------------------------------- Himalayas
def himalayas(s: PoliteSession) -> list[dict]:
    rows, cursor = [], None
    for _ in range(config.LIMITS["himalayas_pages"]):
        url = "https://himalayas.app/jobs/api?limit=20"
        if cursor:
            url += f"&cursor={cursor}"
        d = s.get(url)
        for j in d.get("jobs", []):
            locs = j.get("locationRestrictions") or []
            rows.append(_record(
                source="himalayas", source_id=f"himalayas-{j.get('guid')}",
                url=j.get("applicationLink"), title=j.get("title"),
                company=j.get("companyName"),
                location_raw=", ".join(locs) if locs else "Worldwide",
                remote_raw=True,
                tags=(j.get("categories") or []) + (j.get("parentCategories") or []),
                description_html=j.get("description") or "",
                posted_at=_iso(j.get("pubDate")),
                salary_min=j.get("minSalary"), salary_max=j.get("maxSalary"),
                salary_currency=j.get("currency"),
                salary_period=(j.get("salaryPeriod") or "year").lower()
                if j.get("minSalary") else None))
        cursor = d.get("nextCursor")
        if not cursor:
            break
    return rows


ALL = {"arbeitnow": arbeitnow, "remoteok": remoteok,
       "jobicy": jobicy, "himalayas": himalayas}


def collect(s: PoliteSession) -> list[dict]:
    rows = []
    for name, fn in ALL.items():
        try:
            got = fn(s)
            print(f"  {name}: {len(got)} jobs")
            rows += got
        except RobotsDisallowed as e:
            print(f"  {name}: skipped, robots.txt disallows {e}")
    return rows
