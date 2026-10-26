"""HTML crawler and parser for the Python.org community job board.

This is the classic web-scraping part of the project (Experiments 1 and 3):
there is no API, so we crawl the paginated listing pages, parse each job card
with BeautifulSoup, then follow the link to each job's detail page and parse
the description. robots.txt for www.python.org allows /jobs/.

Listing card structure (October 2026):

    <ol class="list-recent-jobs"><li>
      <h2 class="listing-company">
        <span class="listing-company-name"><a href="/jobs/8184/">AI Engineer</a><br/>Company</span>
        <span class="listing-location"><a ...>London, UK</a></span>
      </h2>
      <span class="listing-job-type"><a>Back end</a>, <a>Cloud</a> ...</span>
      <span class="listing-posted">Posted: <time datetime="...">...</time></span>
    </li>...</ol>
"""
from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .. import config
from ..polite import PoliteSession, RobotsDisallowed

BASE = "https://www.python.org"


def parse_listing(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    jobs = []
    for li in soup.select("ol.list-recent-jobs > li"):
        name = li.select_one(".listing-company-name")
        link = name.select_one("a[href]") if name else None
        if not link:
            continue
        # company name is the text node after the <br/> inside listing-company-name
        for tag in name.select(".listing-new"):
            tag.decompose()
        parts = [t.strip() for t in name.stripped_strings]
        company = parts[-1] if len(parts) > 1 else None
        loc = li.select_one(".listing-location")
        posted = li.select_one(".listing-posted time")
        jobs.append({
            "url": urljoin(BASE, link["href"]),
            "title": link.get_text(strip=True),
            "company": company,
            "location_raw": loc.get_text(" ", strip=True) if loc else None,
            "tags": [a.get_text(strip=True) for a in li.select(".listing-job-type a")],
            "posted_at": posted.get("datetime") if posted else None,
        })
    return jobs


def parse_detail(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for bad in soup(["script", "style", "nav", "footer"]):
        bad.decompose()
    body = soup.select_one(".job-description") or soup.select_one("article") \
        or soup.select_one(".content-wrapper")
    return str(body) if body else ""


def collect(s: PoliteSession) -> list[dict]:
    rows, seen = [], set()
    for page in range(1, config.LIMITS["pyjobs_pages"] + 1):
        url = f"{BASE}/jobs/?page={page}"
        try:
            html = s.get(url, kind="text")
        except RobotsDisallowed:
            break
        except Exception:
            break                        # past the last page the site returns 404
        cards = parse_listing(html)
        new = [c for c in cards if c["url"] not in seen]
        if not new:
            break
        for c in new:
            seen.add(c["url"])
            try:
                desc = parse_detail(s.get(c["url"], kind="text"))
            except Exception:
                desc = ""
            rows.append({
                "source": "pyjobs", "source_id": "pyjobs-" + c["url"].rstrip("/").split("/")[-1],
                "url": c["url"], "title": c["title"], "company": c["company"],
                "location_raw": c["location_raw"], "remote_raw": None,
                "tags": c["tags"], "description_html": desc,
                "posted_at": c["posted_at"], "thread_month": None,
                "salary_min": None, "salary_max": None,
                "salary_currency": None, "salary_period": None,
            })
        print(f"    page {page}: {len(new)} jobs")
    return rows
