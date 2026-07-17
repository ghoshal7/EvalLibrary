#!/usr/bin/env python3
import argparse, importlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "evalkit"))
import evalkit
from evalkit.metrics.deterministic import (tool_correctness, trajectory_match,
                                           step_efficiency, policy_engine)
from evalkit.reporting.report import text_summary

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--adapter", default="otel_genai")
    ap.add_argument("--policies", default=None)
    ap.add_argument("--attempts", type=int, default=4)
    ap.add_argument("--trajectory-mode", default="unordered")
    args = ap.parse_args()

    cases = [evalkit.EvalCase(**json.loads(l))
             for l in Path(args.dataset).read_text().splitlines() if l.strip()]
    policies = json.loads(Path(args.policies).read_text()) if args.policies else []

    if Path(args.target).is_dir():
        raw = json.loads((Path(args.target) / "spans.json").read_text())
        ad = evalkit.resolve("adapter", args.adapter)()
        traces = {t.metadata.get("case_id", t.trace_id): t for t in ad.parse(raw)}
        target = evalkit.resolve("target", "replay")(traces)
    else:
        mod, fn = args.target.split(":")
        target = evalkit.resolve("target", "callable")(
            getattr(importlib.import_module(mod), fn))

    scorers = [tool_correctness(check_args=True),
               trajectory_match(mode=args.trajectory_mode),
               step_efficiency(),
               policy_engine(policies)]
    report = evalkit.run_suite("agent_trajectory_eval", cases, target, scorers,
                               n_attempts=args.attempts, pass_metric="tool_correctness",
                               manifest={"skill": "agent_trajectory_eval/1.0.0"})
    print(text_summary(report))

if __name__ == "__main__":
    main()
