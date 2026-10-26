"""Paths and project-wide settings."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
CACHE = RAW / "cache"
PROCESSED = DATA / "processed"
COMPLIANCE = DATA / "compliance"
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"
TABLES = OUTPUTS / "tables"

for _p in (RAW, CACHE, PROCESSED, COMPLIANCE / "robots", FIGURES, TABLES):
    _p.mkdir(parents=True, exist_ok=True)

# Every request identifies the project honestly instead of pretending to be a browser.
USER_AGENT = (
    "HireSignal/1.0 (VJTI Web Data Mining student project; "
    "non-commercial academic research; polite crawler)"
)

# Minimum seconds between two requests to the same host. A site's own
# Crawl-delay in robots.txt overrides this if it is larger.
DEFAULT_DELAY = 2.0

# Hacker News "Who is hiring?" window used for the trend analysis.
HN_START = (2023, 1)   # January 2023, two months after ChatGPT's release
HN_END = (2026, 10)    # October 2026, the latest complete thread

# Page limits per source keep the collection small and the load on each site low.
LIMITS = {
    "arbeitnow_pages": 6,      # 300 jobs per page
    "himalayas_pages": 40,     # 20 jobs per page
    "jobicy_pages": 4,         # 50 jobs per page
    "pyjobs_pages": 12,        # about 20 jobs per page
}

# Fixed reference exchange rates (to USD) used only to compare salaries.
FX_TO_USD = {
    "USD": 1.0, "EUR": 1.08, "GBP": 1.27, "CAD": 0.73, "AUD": 0.66,
    "INR": 0.012, "CHF": 1.13, "SEK": 0.095, "PLN": 0.25, "SGD": 0.74,
    "NZD": 0.60, "JPY": 0.0067, "BRL": 0.18, "DKK": 0.145, "NOK": 0.094,
}

RANDOM_STATE = 42
