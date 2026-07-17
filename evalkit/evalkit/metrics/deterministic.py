"""evalkit.metrics.deterministic — exact-ground-truth scorers (L1).

Each factory returns a Scorer: (case, output, trace) -> MetricResult.
All are pure functions of canonical types; zero domain content.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from ..core.registry import register
from ..core.types import CanonicalTrace, EvalCase, MetricResult

V = "1.0"


@register("scorer", "exact_match")
def exact_match(field: str = "answer", normalize: bool = True):
    def scorer(case: EvalCase, output: Any, trace: Optional[CanonicalTrace]) -> MetricResult:
        exp = str(case.expected.get(field, ""))
        got = str(output if not isinstance(output, dict) else output.get(field, ""))
        if normalize:
            exp, got = exp.strip().lower(), got.strip().lower()
        ok = exp == got
        return MetricResult("exact_match", 1.0 if ok else 0.0, ok,
                            {"expected": exp, "got": got[:200]}, V)
    return scorer


@register("scorer", "regex_rules")
def regex_rules(required: list[str] = (), forbidden: list[str] = ()):
    def scorer(case, output, trace) -> MetricResult:
        text = json.dumps(output) if isinstance(output, (dict, list)) else str(output)
        miss = [p for p in required if not re.search(p, text, re.I)]
        hit = [p for p in forbidden if re.search(p, text, re.I)]
        ok = not miss and not hit
        return MetricResult("regex_rules", 1.0 if ok else 0.0, ok,
                            {"missing_required": miss, "forbidden_found": hit}, V)
    return scorer


@register("scorer", "json_schema_lite")
def json_schema_lite(required_fields: dict[str, type] | None = None):
    """Lightweight schema gate: valid JSON + required field presence/type.
    With no required_fields configured, acts as a JSON-validity gate."""
    required_fields = required_fields or {}
    def scorer(case, output, trace) -> MetricResult:
        obj = output
        if isinstance(output, str):
            try:
                obj = json.loads(output)
            except json.JSONDecodeError:
                return MetricResult("json_schema", 0.0, False, {"error": "not json"}, V)
        problems = [
            f for f, t in required_fields.items()
            if f not in obj or not isinstance(obj[f], t)
        ]
        ok = not problems
        return MetricResult("json_schema", 1.0 if ok else 0.0, ok,
                            {"problems": problems}, V)
    return scorer


@register("scorer", "tool_correctness")
def tool_correctness(check_args: bool = False):
    """|called ∩ expected| / |expected| over trace tool spans."""
    def scorer(case, output, trace) -> MetricResult:
        expected = case.expected.get("tools", [])          # [{name, arguments?}]
        if not trace or not expected:
            return MetricResult("tool_correctness", 0.0, False, {"error": "no trace/expected"}, V)
        called = trace.tool_calls()
        exp_names = [t["name"] for t in expected]
        hit = 0
        for t in expected:
            for name, args in called:
                if name != t["name"]:
                    continue
                if check_args and t.get("arguments") and not _args_subset(t["arguments"], args):
                    continue
                hit += 1
                break
        score = hit / len(exp_names)
        return MetricResult("tool_correctness", round(score, 4), score == 1.0,
                            {"expected": exp_names, "called": [n for n, _ in called]}, V)
    return scorer


@register("scorer", "trajectory_match")
def trajectory_match(mode: str = "unordered"):
    """Modes: strict (exact order), unordered (same multiset),
    subset (reference ⊆ actual), superset (actual ⊆ reference)."""
    def scorer(case, output, trace) -> MetricResult:
        ref = case.expected.get("trajectory", [])
        act = [n for n, _ in trace.tool_calls()] if trace else []
        if mode == "strict":
            ok = act == ref
        elif mode == "unordered":
            ok = sorted(act) == sorted(ref)
        elif mode == "subset":
            ok = all(_count_ok(r, ref, act) for r in set(ref))
        elif mode == "superset":
            ok = all(_count_ok(a, act, ref) for a in set(act))
        else:
            raise ValueError(f"unknown mode {mode}")
        return MetricResult(f"trajectory_{mode}", 1.0 if ok else 0.0, ok,
                            {"reference": ref, "actual": act}, V)
    return scorer


@register("scorer", "step_efficiency")
def step_efficiency():
    def scorer(case, output, trace) -> MetricResult:
        minimal = case.expected.get("min_steps")
        actual = len(trace.tool_calls()) if trace else 0
        if not minimal or not actual:
            return MetricResult("step_efficiency", 0.0, None, {"actual": actual}, V)
        score = min(1.0, minimal / actual)
        return MetricResult("step_efficiency", round(score, 4), None,
                            {"minimal": minimal, "actual": actual}, V)
    return scorer


@register("scorer", "policy_engine")
def policy_engine(policies: list[dict[str, Any]]):
    """Declarative trace policies (the config-driven customization surface).

    policy examples:
      {"rule": "forbidden_tool", "tool": "delete_account"}
      {"rule": "arg_max",  "tool": "refund", "arg": "amount", "max": 500}
      {"rule": "require_before", "first": "verify_identity", "then": "update_address"}
    """
    def scorer(case, output, trace) -> MetricResult:
        violations: list[str] = []
        calls = trace.tool_calls() if trace else []
        order = [n for n, _ in calls]
        for p in policies:
            r = p["rule"]
            if r == "forbidden_tool" and p["tool"] in order:
                violations.append(f"forbidden tool used: {p['tool']}")
            elif r == "arg_max":
                for name, args in calls:
                    if name == p["tool"] and float(args.get(p["arg"], 0)) > p["max"]:
                        violations.append(f"{p['tool']}.{p['arg']} exceeds {p['max']}")
            elif r == "require_before" and p["then"] in order:
                if p["first"] not in order or order.index(p["first"]) > order.index(p["then"]):
                    violations.append(f"{p['then']} without prior {p['first']}")
        ok = not violations
        return MetricResult("policy_adherence", 1.0 if ok else 0.0, ok,
                            {"violations": violations}, V)
    return scorer


def _args_subset(expected: dict, actual: dict) -> bool:
    return all(str(actual.get(k)) == str(v) for k, v in expected.items())


def _count_ok(item: str, sub: list, sup: list) -> bool:
    return sub.count(item) <= sup.count(item)
