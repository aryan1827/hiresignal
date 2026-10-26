"""Skill extraction: turns a job description into a set of canonical skills."""
from __future__ import annotations

import re
from functools import lru_cache

from .taxonomy import T


def _compile(pattern: str) -> re.Pattern:
    if pattern.startswith("re:"):
        return re.compile(pattern[3:], re.I)
    if pattern.startswith("cs:"):
        return re.compile(pattern[3:])
    words = [re.escape(w) for w in pattern.split()]
    body = r"[\s\-]?".join(words)
    return re.compile(rf"(?<![\w]){body}(?![\w])", re.I)


@lru_cache(maxsize=1)
def compiled():
    out = []
    for name, cat, patterns, opts in T:
        exc = re.compile(opts["exclude"]) if "exclude" in opts else None
        out.append((name, [_compile(p) for p in patterns], exc, bool(opts.get("context"))))
    return out


def _hit(text: str, regs, exc) -> bool:
    for rg in regs:
        for m in rg.finditer(text):
            if exc is None:
                return True
            window = text[max(0, m.start() - 15): m.end() + 15]
            if not exc.search(window):
                return True
    return False


def extract(text: str) -> list[str]:
    """Return the canonical skills mentioned in ``text`` (original casing kept,
    because case-sensitive patterns need it)."""
    if not text:
        return []
    found, pending = [], []
    for name, regs, exc, needs_context in compiled():
        if _hit(text, regs, exc):
            (pending if needs_context else found).append(name)
    # context-only skills (C, R, Go, Julia, MCP) need two other skills alongside
    if len(found) >= 2:
        found += pending
    return found


def extract_with_spans(text: str) -> list[tuple[str, int, int, str]]:
    """For the dashboard's highlighter: every match with its position."""
    spans = []
    for name, regs, exc, _ in compiled():
        for rg in regs:
            for m in rg.finditer(text):
                window = text[max(0, m.start() - 15): m.end() + 15]
                if exc is None or not exc.search(window):
                    spans.append((name, m.start(), m.end(), m.group(0)))
    return sorted(spans, key=lambda s: s[1])
