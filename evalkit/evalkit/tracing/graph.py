"""evalkit.tracing.graph — multi-agent trace projection & coordination stats (L1).

A MAS trace is one CanonicalTrace spanning all agents and patterns. This
module provides the cross-pattern views the MAS survey's three eval layers
need: scope projection (per-agent sub-traces so single-pattern scorers run
unchanged inside a MAS) and the interaction graph (handoffs, redundancy).
"""
from __future__ import annotations
import json
from ..core.types import CanonicalSpan, CanonicalTrace, SpanKind


def agent_scopes(trace: CanonicalTrace) -> dict[str, CanonicalTrace]:
    """Project the system trace into per-agent sub-traces: every span is
    assigned to its nearest ancestor AGENT span. Pattern-level scorers
    (tool_correctness, trajectory_match, faithfulness...) then run on a
    scope exactly as on a single-agent trace — the component/pattern layer
    of MAS evaluation with zero new metric code."""
    by_id = {s.span_id: s for s in trace.spans}

    def owner(s: CanonicalSpan) -> str | None:
        cur = s
        while cur is not None:
            if cur.kind == SpanKind.AGENT:
                return cur.name
            cur = by_id.get(cur.parent_id) if cur.parent_id else None
        return None

    scopes: dict[str, CanonicalTrace] = {}
    for s in trace.spans:
        o = owner(s)
        if o is None:
            continue
        sub = scopes.setdefault(
            o, CanonicalTrace(f"{trace.trace_id}/{o}", metadata=dict(trace.metadata)))
        sub.spans.append(s)
    return scopes


def handoff_sequence(trace: CanonicalTrace) -> list[str]:
    """Chronological 'from->to' list from HANDOFF spans (attributes.from/to),
    falling back to AGENT span activation order when no handoff spans exist."""
    hs = sorted(trace.spans_of(SpanKind.HANDOFF), key=lambda s: s.start_ns)
    if hs:
        return [f"{s.attributes.get('from', '?')}->{s.attributes.get('to', '?')}" for s in hs]
    agents = sorted(trace.spans_of(SpanKind.AGENT), key=lambda s: s.start_ns)
    return [f"{a.name}->{b.name}" for a, b in zip(agents, agents[1:])]


def coordination_stats(trace: CanonicalTrace) -> dict:
    """Graph-level process statistics (GEMMAS-style proxies):
    redundant_ratio ~ unnecessary-path proxy; handoff overhead; fan-out."""
    calls = []
    for s in trace.spans_of(SpanKind.TOOL):
        calls.append((s.name, json.dumps(s.inputs.get("arguments", {}), sort_keys=True)))
    dup = len(calls) - len(set(calls))
    agents = trace.spans_of(SpanKind.AGENT)
    return {
        "n_agents": len(agents),
        "n_handoffs": len(handoff_sequence(trace)),
        "n_tool_calls": len(calls),
        "redundant_tool_calls": dup,
        "redundant_ratio": round(dup / len(calls), 4) if calls else 0.0,
    }
