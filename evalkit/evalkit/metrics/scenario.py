"""evalkit.metrics.scenario — declarative scenario testing (L1).

Group C type 'scenario testing': enumerated situations with explicit
assertions per case (given/when/then style). Assertions are data in
case.expected["assertions"], so scenario suites are pure datasets.

Assertion types:
  {"type": "contains", "value": str}      output includes value (ci)
  {"type": "not_contains", "value": str}  output excludes value (ci)
  {"type": "regex", "value": pattern}     output matches pattern
  {"type": "tool_used", "value": name}    trace has a tool span `name`
  {"type": "tool_not_used", "value": name}
  {"type": "max_tool_calls", "value": n}
"""
from __future__ import annotations
import re
from typing import Any, Optional
from ..core.registry import register
from ..core.types import CanonicalTrace, EvalCase, MetricResult


@register("scorer", "scenario_assertions")
def scenario_assertions(strict: bool = True):
    """Pass requires all assertions to hold (strict) else score = fraction."""
    def scorer(case: EvalCase, output: Any, trace: Optional[CanonicalTrace]) -> MetricResult:
        checks = case.expected.get("assertions", [])
        if not checks:
            return MetricResult("scenario", 0.0, None, {"error": "no assertions"}, "1.0")
        text = str(output)
        tools = [n for n, _ in trace.tool_calls()] if trace else []
        fails: list[str] = []
        for a in checks:
            t, v = a["type"], a.get("value")
            ok = (
                v.lower() in text.lower() if t == "contains" else
                v.lower() not in text.lower() if t == "not_contains" else
                bool(re.search(v, text, re.I)) if t == "regex" else
                v in tools if t == "tool_used" else
                v not in tools if t == "tool_not_used" else
                len(tools) <= int(v) if t == "max_tool_calls" else
                False
            )
            if not ok:
                fails.append(f"{t}({v})")
        frac = 1 - len(fails) / len(checks)
        passed = not fails if strict else frac >= 0.999
        return MetricResult("scenario", round(frac, 4), passed,
                            {"failed_assertions": fails, "scenario": case.tags}, "1.0")
    return scorer
