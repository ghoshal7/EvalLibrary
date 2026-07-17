#!/usr/bin/env python3
"""rag_eval skill runner — thin composition over evalkit (no metric logic here)."""
import argparse, importlib, json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]        # evallib/
sys.path.insert(0, str(ROOT / "evalkit"))

import evalkit
from evalkit.metrics.judges import Criterion, rubric_judge, faithfulness_qag
from evalkit.metrics.deterministic import regex_rules
from evalkit.reporting.report import text_summary

try:
    import yaml
    _load_yaml = lambda p: yaml.safe_load(Path(p).read_text())
except ImportError:                                # prototype fallback: JSON-ish yaml
    def _load_yaml(p):
        import json as _j
        txt = Path(p).read_text()
        raise SystemExit("pyyaml required for yaml configs; or supply JSON") 

def load_cases(path):
    return [evalkit.EvalCase(**json.loads(l)) for l in Path(path).read_text().splitlines() if l.strip()]

def load_target(spec, adapter=None):
    if os.path.isdir(spec):                        # replay from exported traces
        raw = json.loads(Path(spec, "spans.json").read_text())
        ad = evalkit.resolve("adapter", adapter or "otel_genai")()
        traces = {t.metadata.get("case_id", t.trace_id): t for t in ad.parse(raw)}
        return evalkit.resolve("target", "replay")(traces)
    mod, fn = spec.split(":")                      # live python entrypoint
    return evalkit.resolve("target", "callable")(getattr(importlib.import_module(mod), fn))

def judge_model():
    """Bind the judge LLM. Demo/CI uses the stub; production sets EVAL_JUDGE_MODEL."""
    spec = os.environ.get("EVAL_JUDGE_MODEL", "stub")
    if spec == "stub":
        from _stub_judge import stub_model
        return stub_model
    mod, fn = spec.split(":")
    return getattr(importlib.import_module(mod), fn)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--overrides", default=None)
    ap.add_argument("--attempts", type=int, default=1)
    args = ap.parse_args()

    crit_cfg = _load_yaml(Path(__file__).parent / "prompts/rag_default_criteria.yaml")
    if args.overrides:                             # app layer: deep-merge criteria
        ov = _load_yaml(args.overrides)
        crit_cfg["criteria"] = ov.get("criteria", crit_cfg["criteria"])
    criteria = [evalkit_criterion(c) for c in crit_cfg["criteria"]]

    model = judge_model()
    scorers = [
        faithfulness_qag(model),
        rubric_judge(criteria, model, name="answer_quality"),
        regex_rules(),                              # neutral defaults; apps override
    ]
    report = evalkit.run_suite(
        "rag_eval", load_cases(args.dataset), load_target(args.target, args.adapter),
        scorers, n_attempts=args.attempts, pass_metric="faithfulness",
        manifest={"skill": "rag_eval/1.0.0"},
    )
    print(text_summary(report))

def evalkit_criterion(c):
    return Criterion(c["name"], c["description"],
                     {int(k): v for k, v in c.get("anchors", {}).items()},
                     c.get("weight", 1.0))

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
