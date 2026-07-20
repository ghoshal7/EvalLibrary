#!/usr/bin/env python3
"""mas_eval runner — three-layer MAS evaluation from a composition file."""
import argparse, importlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "evalkit"))
import evalkit
from evalkit.metrics.mas import handoff_flow, coordination_efficiency, agent_scope
from evalkit.reporting.report import text_summary

def build_scorer(spec):
    return evalkit.resolve("scorer", spec["name"])(**spec.get("params", {}))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--composition", required=True)
    ap.add_argument("--adapter", default="otel_genai")
    ap.add_argument("--attempts", type=int, default=1)
    args = ap.parse_args()

    comp = json.loads(Path(args.composition).read_text())
    cases = [evalkit.EvalCase(**json.loads(l))
             for l in Path(args.dataset).read_text().splitlines() if l.strip()]

    if Path(args.target).is_dir():
        raw = json.loads((Path(args.target) / "spans.json").read_text())
        ad = evalkit.resolve("adapter", args.adapter)()
        traces = {t.metadata.get("case_id", t.trace_id): t for t in ad.parse(raw)}
        target = evalkit.resolve("target", "replay")(traces)
    else:
        mod, fn = args.target.split(":")
        target = evalkit.resolve("target", "callable")(
            getattr(importlib.import_module(mod), fn))

    scorers = []
    scorers += [build_scorer(s) for s in comp.get("outcome", [])]        # outcome
    scorers += [handoff_flow(comp.get("flow_mode", "strict")),           # process
                coordination_efficiency(comp.get("max_redundant_tool_calls", 0))]
    for agent, cfg in comp.get("agents", {}).items():                    # component
        for s in cfg.get("scorers", []):
            scorers.append(agent_scope(agent, build_scorer(s), cfg.get("expected")))

    rep = evalkit.run_suite("mas_eval", cases, target, scorers,
                            n_attempts=args.attempts, pass_metric="scenario",
                            manifest={"skill": "mas_eval/1.0.0",
                                      "mas_patterns": comp.get("mas_patterns", []),
                                      "composition": comp.get("flow")})
    print(text_summary(rep))

if __name__ == "__main__":
    main()
