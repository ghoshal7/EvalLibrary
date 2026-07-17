#!/usr/bin/env python3
import argparse, importlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "evalkit"))
import evalkit
from evalkit.metrics.robustness import robustness
from evalkit.reporting.report import text_summary

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--field", default="query")
    ap.add_argument("--threshold", type=float, default=0.7)
    args = ap.parse_args()
    cases = [evalkit.EvalCase(**json.loads(l))
             for l in Path(args.dataset).read_text().splitlines() if l.strip()]
    mod, fn = args.target.split(":")
    target = evalkit.resolve("target", "callable")(
        getattr(importlib.import_module(mod), fn))
    scorers = [robustness(target, field=args.field, pass_threshold=args.threshold)]
    rep = evalkit.run_suite("robustness_probe", cases, target, scorers,
                            manifest={"skill": "robustness_probe/1.0.0"})
    print(text_summary(rep))

if __name__ == "__main__":
    main()
