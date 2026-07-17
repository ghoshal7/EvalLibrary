#!/usr/bin/env python3
"""extraction_eval skill runner — composition only; metric logic lives in evalkit."""
import argparse, importlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "evalkit"))
import evalkit
from evalkit.reporting.report import text_summary

SCORER_NAMES = "json_schema_lite,exact_match".split(",")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--attempts", type=int, default=1)
    args = ap.parse_args()
    cases = [evalkit.EvalCase(**json.loads(l))
             for l in Path(args.dataset).read_text().splitlines() if l.strip()]
    mod, fn = args.target.split(":")
    target = evalkit.resolve("target", "callable")(
        getattr(importlib.import_module(mod), fn))
    scorers = [evalkit.resolve("scorer", n)() for n in SCORER_NAMES]
    rep = evalkit.run_suite("extraction_eval", cases, target, scorers,
                            n_attempts=args.attempts)
    print(text_summary(rep))

if __name__ == "__main__":
    main()
