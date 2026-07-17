"""evalkit.inference — Target abstraction (L0/L1).

A Target is anything the runner can invoke on an EvalCase and get back
(output, CanonicalTrace|None). Three families:

  * LiveTarget     — call the system under test (LLM API, agent endpoint),
                     capturing a trace via the tracing layer.
  * ReplayTarget   — no inference at all: evaluate pre-collected traces
                     (e.g., exported from Phoenix or an OTel backend).
  * CallableTarget — wrap any python callable; used for local pipelines
                     and for the mock target in tests/demos.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Optional

from ..core.registry import register
from ..core.types import CanonicalSpan, CanonicalTrace, EvalCase, SpanKind


@register("target", "callable")
class CallableTarget:
    def __init__(self, fn: Callable[[dict[str, Any]], tuple[Any, Optional[CanonicalTrace]]]):
        self.fn = fn

    def __call__(self, case: EvalCase) -> tuple[Any, Optional[CanonicalTrace]]:
        return self.fn(case.inputs)


@register("target", "replay")
class ReplayTarget:
    """Evaluate pre-collected traces keyed by case_id."""

    def __init__(self, traces_by_case: dict[str, CanonicalTrace]):
        self.traces = traces_by_case

    def __call__(self, case: EvalCase) -> tuple[Any, Optional[CanonicalTrace]]:
        trace = self.traces[case.case_id]
        return trace.final_output(), trace


class TraceBuilder:
    """Minimal instrumentation helper for LiveTarget/CallableTarget authors."""

    def __init__(self, trace_id: str):
        self.trace = CanonicalTrace(trace_id)
        self._n = 0

    def span(self, kind: SpanKind, name: str, inputs: dict, outputs: dict,
             parent_id: str | None = None, **attrs: Any) -> CanonicalSpan:
        self._n += 1
        now = time.time_ns()
        s = CanonicalSpan(
            span_id=f"{self.trace.trace_id}-{self._n}", parent_id=parent_id,
            kind=kind, name=name, start_ns=now, end_ns=now + 1_000_000,
            inputs=inputs, outputs=outputs, attributes=attrs,
        )
        self.trace.spans.append(s)
        return s
