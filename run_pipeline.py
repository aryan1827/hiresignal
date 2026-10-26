"""HireSignal pipeline runner.

    python run_pipeline.py all          # collect -> preprocess -> mine -> figures
    python run_pipeline.py collect      # only (re)collect raw data (uses the cache)
    python run_pipeline.py preprocess   # clean, scrub PII, parse, extract skills
    python run_pipeline.py mine         # demand, trends, network, rules, clusters ...
    python run_pipeline.py viz          # static PNG figures in outputs/figures
"""
import sys
import time
import warnings

warnings.filterwarnings("ignore")

from hiresignal import compliance, preprocess, viz  # noqa: E402
from hiresignal.collect import run as collect  # noqa: E402
from hiresignal.mining import run as mine  # noqa: E402

STAGES = {"collect": collect.run, "preprocess": preprocess.run, "mine": mine.run, "viz": viz.run}


def main(args):
    stage = args[0] if args else "all"
    order = list(STAGES) if stage == "all" else [stage]
    compliance.table()
    for name in order:
        if name not in STAGES:
            sys.exit(f"unknown stage {name!r}; choose from all, {', '.join(STAGES)}")
        t = time.time()
        print(f"\n=== {name} ===")
        STAGES[name]()
        print(f"=== {name} finished in {time.time() - t:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
