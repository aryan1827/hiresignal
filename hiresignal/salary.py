"""Salary parsing and normalisation to annual US dollars."""
from __future__ import annotations

import re

from .config import FX_TO_USD

SYMBOL = {"$": "USD", "€": "EUR", "£": "GBP", "₹": "INR", "¥": "JPY"}
CODE = re.compile(r"\b(USD|EUR|GBP|CAD|AUD|INR|CHF|SEK|PLN|SGD|NZD|JPY|BRL|DKK|NOK)\b", re.I)
NUM = r"(\d{1,3}(?:[,.\s]\d{3})+|\d+(?:\.\d+)?)"
RANGE = re.compile(
    rf"(?P<c1>[$€£₹]|\b(?:USD|EUR|GBP|CAD|AUD|INR|CHF)\s?)?\s?{NUM}\s?(?P<k1>[kK]\b|m\b)?"
    rf"\s?(?:-|–|—|to)\s?(?P<c2>[$€£₹]|\b(?:USD|EUR|GBP|CAD|AUD)\s?)?\s?{NUM}\s?(?P<k2>[kK]\b|m\b)?")
SINGLE = re.compile(rf"(?P<c1>[$€£₹])\s?{NUM}\s?(?P<k1>[kK]\b)?")
LPA = re.compile(r"(\d+(?:\.\d+)?)\s?(?:-|to)?\s?(\d+(?:\.\d+)?)?\s?(?:lpa|lakhs?|lacs?)\b", re.I)
HOURLY = re.compile(r"/\s?h(?:ou)?r|per hour|hourly|an hour|/h\b", re.I)
MONTHLY = re.compile(r"/\s?mo(?:nth)?|per month|monthly", re.I)
PERIOD_FACTOR = {"year": 1, "month": 12, "week": 52, "day": 220, "hour": 2080}


def _num(s: str) -> float:
    s = s.replace(" ", "")
    if re.fullmatch(r"\d{1,3}(?:[,.]\d{3})+", s):
        return float(re.sub(r"[,.]", "", s))
    return float(s.replace(",", ""))


def _period(p: str | None) -> str:
    p = (p or "year").lower()
    for key in PERIOD_FACTOR:
        if key in p or (key == "year" and p.startswith("annual")):
            return key
    return "year"


def to_usd_year(lo, hi, currency="USD", period="year"):
    """Convert a numeric range to annual USD; returns (lo, hi) or (None, None)."""
    def clean(v):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        return None if v != v or v <= 0 else v      # NaN or zero -> missing
    lo, hi = clean(lo), clean(hi)
    if lo is None and hi is None:
        return None, None
    lo = lo if lo is not None else hi
    hi = hi if hi is not None else lo
    fx = FX_TO_USD.get((currency or "USD").upper())
    if fx is None:
        return None, None
    f = PERIOD_FACTOR[_period(period)] * fx
    lo, hi = lo * f, hi * f
    if hi < lo:
        lo, hi = hi, lo
    # keep plausible full-time salaries only
    if lo < 12_000 or hi > 900_000 or hi > 4 * lo:
        return None, None
    return round(lo), round(hi)


def parse_text(text: str):
    """Find a salary range in free text. Returns (lo, hi) in annual USD or (None, None)."""
    if not text:
        return None, None
    m = LPA.search(text)
    if m:
        lo = float(m.group(1)) * 100_000
        hi = float(m.group(2)) * 100_000 if m.group(2) else lo
        return to_usd_year(lo, hi, "INR")
    m = RANGE.search(text)
    single = False
    if not m:
        m = SINGLE.search(text)
        single = True
    if not m:
        return None, None
    g = m.groupdict()
    nums = [x for x in m.groups() if x and re.fullmatch(r"[\d,.\s]+", x.strip()) and any(ch.isdigit() for ch in x)]
    if not nums:
        return None, None
    lo = _num(nums[0])
    hi = _num(nums[1]) if len(nums) > 1 and not single else lo
    k1, k2 = (g.get("k1") or "").lower(), (g.get("k2") or "").lower()
    if k2 == "k" or k1 == "k":
        if lo < 1000:
            lo *= 1000
        if hi < 1000:
            hi *= 1000
    if k1 == "m" or k2 == "m":
        return None, None
    sym = (g.get("c1") or g.get("c2") or "").strip()
    window = text[max(0, m.start() - 20): m.end() + 25]
    code = CODE.search(window)
    currency = code.group(1).upper() if code else SYMBOL.get(sym)
    if not currency:
        return None, None        # a bare number range is too ambiguous to call a salary
    period = "hour" if HOURLY.search(window) else "month" if MONTHLY.search(window) else "year"
    if period == "year" and hi < 1000:  # "$120-150" with no k almost always means thousands
        lo, hi = lo * 1000, hi * 1000
    return to_usd_year(lo, hi, currency, period)
