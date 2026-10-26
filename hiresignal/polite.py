"""A polite HTTP client: robots.txt checks, rate limiting, caching and an audit log.

Every network request in the project goes through ``PoliteSession.get``. Before
fetching a URL it:

1. downloads and stores the host's robots.txt (once per run) and refuses any
   path that robots.txt disallows for our user agent;
2. waits so that requests to one host are at least ``delay`` seconds apart,
   using the larger of our default and the site's own Crawl-delay;
3. serves the response from the local disk cache if we already have it, so a
   re-run of the pipeline does not hit the site again;
4. writes one row to ``data/compliance/request_log.csv`` describing the request.
"""
from __future__ import annotations

import csv
import hashlib
import json
import time
import urllib.robotparser
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

from . import config

LOG_PATH = config.COMPLIANCE / "request_log.csv"
LOG_FIELDS = ["timestamp_utc", "host", "url", "robots_allowed", "crawl_delay_s",
              "status", "bytes", "from_cache"]


class RobotsDisallowed(Exception):
    """Raised when robots.txt does not allow the requested URL."""


class PoliteSession:
    def __init__(self, delay: float = config.DEFAULT_DELAY, use_cache: bool = True):
        self.delay = delay
        self.use_cache = use_cache
        self.http = requests.Session()
        self.http.headers.update({"User-Agent": config.USER_AGENT,
                                  "Accept-Encoding": "gzip, deflate"})
        self._robots: dict[str, urllib.robotparser.RobotFileParser] = {}
        self._last_hit: dict[str, float] = {}
        if not LOG_PATH.exists():
            with LOG_PATH.open("w", newline="") as f:
                csv.writer(f).writerow(LOG_FIELDS)

    # ------------------------------------------------------------------ robots
    def robots_for(self, url: str) -> urllib.robotparser.RobotFileParser:
        parts = urlparse(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base in self._robots:
            return self._robots[base]
        rp = urllib.robotparser.RobotFileParser()
        robots_url = base + "/robots.txt"
        try:
            r = self.http.get(robots_url, timeout=20)
            text = r.text if r.status_code == 200 else ""
            # A missing robots.txt (404) means no restrictions, per the standard.
            rp.parse(text.splitlines())
            snap = config.COMPLIANCE / "robots" / f"{parts.netloc}.txt"
            snap.write_text(f"# fetched {datetime.now(timezone.utc).isoformat()} "
                            f"status={r.status_code}\n{text}")
        except requests.RequestException:
            # If robots.txt cannot be read at all, stay on the safe side.
            rp.parse(["User-agent: *", "Disallow: /"])
        self._robots[base] = rp
        return rp

    def allowed(self, url: str) -> bool:
        return self.robots_for(url).can_fetch(config.USER_AGENT, url)

    def crawl_delay(self, url: str) -> float:
        cd = self.robots_for(url).crawl_delay(config.USER_AGENT)
        return max(self.delay, float(cd) if cd else 0.0)

    # ------------------------------------------------------------------- cache
    @staticmethod
    def _cache_path(url: str):
        return config.CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".json")

    # --------------------------------------------------------------------- get
    def get(self, url: str, kind: str = "json"):
        """Fetch ``url`` politely. ``kind`` is "json" or "text"."""
        host = urlparse(url).netloc
        cache_file = self._cache_path(url)
        if self.use_cache and cache_file.exists():
            payload = json.loads(cache_file.read_text())
            self._log(host, url, True, 0, payload.get("status", 200),
                      len(payload.get("body", "")), True)
            body = payload["body"]
            return json.loads(body) if kind == "json" else body

        if not self.allowed(url):
            self._log(host, url, False, 0, "skipped", 0, False)
            raise RobotsDisallowed(url)

        wait = self.crawl_delay(url)
        since = time.time() - self._last_hit.get(host, 0)
        if since < wait:
            time.sleep(wait - since)

        for attempt in range(3):
            try:
                r = self.http.get(url, timeout=40)
            except requests.RequestException:
                time.sleep(5 * (attempt + 1))
                continue
            self._last_hit[host] = time.time()
            if r.status_code == 429:          # the server asks us to slow down
                time.sleep(int(r.headers.get("Retry-After", 30)))
                continue
            break
        else:
            raise RuntimeError(f"failed to fetch {url}")

        self._log(host, url, True, wait, r.status_code, len(r.content), False)
        r.raise_for_status()
        if self.use_cache:
            cache_file.write_text(json.dumps({"url": url, "status": r.status_code,
                                              "fetched": datetime.now(timezone.utc).isoformat(),
                                              "body": r.text}))
        return r.json() if kind == "json" else r.text

    def _log(self, host, url, allowed, delay, status, nbytes, cached):
        with LOG_PATH.open("a", newline="") as f:
            csv.writer(f).writerow([datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                    host, url, allowed, delay, status, nbytes, cached])
