"""Stage 1: run every collector and save one raw JSON file per source."""
from __future__ import annotations

import json

from .. import config
from ..polite import PoliteSession
from . import apis, hn, pyjobs


def run() -> dict[str, int]:
    s = PoliteSession()
    counts = {}
    jobs = {"hn": hn.collect, "apis": apis.collect, "pyjobs": pyjobs.collect}
    for name, fn in jobs.items():
        print(f"[collect] {name}")
        rows = fn(s)
        by_source: dict[str, list] = {}
        for r in rows:
            by_source.setdefault(r["source"], []).append(r)
        for src, items in by_source.items():
            (config.RAW / f"{src}.json").write_text(json.dumps(items))
            counts[src] = len(items)
    (config.RAW / "collection_summary.json").write_text(json.dumps(counts, indent=2))
    print("[collect] done:", counts)
    return counts


if __name__ == "__main__":
    run()
