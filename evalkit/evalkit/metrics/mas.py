"""evalkit.metrics.mas — multi-agent outcome & process scorers (L1).

MAS eval layers map to evalkit as: outcome (end-to-end) = existing output
scorers on the system's final output; process (trajectory) = the scorers
here, over the whole cross-pattern trace; component (per-agent pattern) =
agent_scope() delegating any existing L1 scorer to one agent's sub-trace.
"""
from __future__ import annotations
from typing import Any, Callable, Optional
from ..core.registry import register
from ..core.types import CanonicalTrace, EvalCase, MetricResult
from ..tracing.graph import agent_scopes, coordination_stats, handoff_sequence


@register("scorer", "handoff_flow")
def handoff_flow(mode: str = "strict"):
    """Process layer: compare the realized handoff sequence to
    expected.flow (['orchestrator->researcher', ...]). Modes as in
    trajectory_match: strict | unordered | subset."""
    def scorer(case: EvalCase, output: Any, trace: Optional[CanonicalTrace]) -> MetricResult:
        ref = case.expected.get("flow", [])
        act = handoff_sequence(trace) if trace else []
        ok = (act == ref if mode == "strict" else
              sorted(act) == sorted(ref) if mode == "unordered" else
              all(r in act for r in ref))
        return MetricResult(f"handoff_{mode}", 1.0 if ok else 0.0, ok,
                            {"expected": ref, "actual": act}, "1.0")
    return scorer


@register("scorer", "coordination_efficiency")
def coordination_efficiency(max_redundant: int = 0):
    """Process layer: penalize duplicated work across agents
    (same tool + identical args anywhere in the system trace)."""
    def scorer(case, output, trace) -> MetricResult:
        st = coordination_stats(trace) if trace else {}
        red = st.get("redundant_tool_calls", 0)
        score = 1.0 - st.get("redundant_ratio", 1.0)
        return MetricResult("coordination_efficiency", round(score, 4),
                            red <= max_redundant, st, "1.0")
    return scorer


@register("scorer", "agent_scope")
def agent_scope(agent: str, inner: Callable, expected: Optional[dict] = None):
    """Component layer: run ANY configured L1 scorer against one agent's
    sub-trace — per-pattern metrics inside a MAS without new code.
    `expected` (from the composition file) overrides case.expected for this
    agent, so each agent carries its own tools/trajectory/rules."""
    def scorer(case: EvalCase, output: Any, trace: Optional[CanonicalTrace]) -> MetricResult:
        if expected is not None:
            case = EvalCase(case.case_id, case.inputs, {**case.expected, **expected}, case.tags)
        sub = agent_scopes(trace).get(agent) if trace else None
        if sub is None:
            return MetricResult(f"{agent}.scoped", 0.0, False,
                                {"error": f"no scope for agent '{agent}'"}, "1.0")
        agent_out = next((s.outputs.get("completion") or s.outputs.get("result")
                          for s in sub.spans if s.name == agent), output)
        r = inner(case, agent_out, sub)
        return MetricResult(f"{agent}.{r.metric}", r.score, r.passed, r.details, r.metric_version)
    return scorer
