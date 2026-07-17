"""evalkit.core.types — canonical data contracts (L0).

Every subsystem (tracing adapters, inference targets, metrics, runner,
reporting) speaks these types and nothing else. Vendor formats (OTel GenAI,
Arize/Phoenix, LangSmith, ...) are converted to CanonicalTrace at the edge.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Canonical trace schema (the standardization layer)
# ---------------------------------------------------------------------------

class SpanKind(str, Enum):
    LLM = "llm"                # a model call
    TOOL = "tool"              # a tool/function execution
    RETRIEVER = "retriever"    # a retrieval call
    AGENT = "agent"            # an agent step / sub-agent scope
    CHAIN = "chain"            # generic composite step
    HANDOFF = "handoff"        # control transfer between agents
    GUARDRAIL = "guardrail"    # filter / validator execution
    OTHER = "other"


@dataclass
class CanonicalSpan:
    span_id: str
    kind: SpanKind
    name: str
    parent_id: Optional[str] = None
    start_ns: int = 0
    end_ns: int = 0
    inputs: dict[str, Any] = field(default_factory=dict)    # prompt/messages/query/args
    outputs: dict[str, Any] = field(default_factory=dict)   # completion/result/documents
    attributes: dict[str, Any] = field(default_factory=dict)  # model, tokens, agent name...
    status: str = "OK"          # OK | ERROR
    error: Optional[str] = None

    @property
    def duration_ms(self) -> float:
        return (self.end_ns - self.start_ns) / 1e6


@dataclass
class CanonicalTrace:
    trace_id: str
    spans: list[CanonicalSpan] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)  # source vendor, app, session

    # -- convenience selectors used by metrics ------------------------------
    def spans_of(self, kind: SpanKind) -> list[CanonicalSpan]:
        return [s for s in self.spans if s.kind == kind]

    def tool_calls(self) -> list[tuple[str, dict[str, Any]]]:
        """(tool_name, arguments) in chronological order."""
        return [
            (s.name, s.inputs.get("arguments", {}))
            for s in sorted(self.spans_of(SpanKind.TOOL), key=lambda s: s.start_ns)
        ]

    def final_output(self) -> Any:
        roots = [s for s in self.spans if s.parent_id is None]
        if roots:
            root = sorted(roots, key=lambda s: s.end_ns)[-1]
            return root.outputs.get("completion") or root.outputs.get("result")
        return None

    def total_tokens(self) -> int:
        return sum(int(s.attributes.get("tokens_total", 0)) for s in self.spans)


# ---------------------------------------------------------------------------
# Eval contracts
# ---------------------------------------------------------------------------

@dataclass
class EvalCase:
    """One test item. `expected` fields are optional per metric needs."""
    case_id: str
    inputs: dict[str, Any]
    expected: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


@dataclass
class MetricResult:
    metric: str
    score: float                       # normalized 0..1 (or 0/1 for pass-fail)
    passed: Optional[bool] = None
    details: dict[str, Any] = field(default_factory=dict)
    metric_version: str = "0.0"


@dataclass
class CaseResult:
    case_id: str
    attempt: int
    output: Any
    trace: Optional[CanonicalTrace]
    metrics: list[MetricResult] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class RunReport:
    run_id: str
    suite: str
    n_cases: int
    n_attempts: int
    case_results: list[CaseResult]
    aggregates: dict[str, Any] = field(default_factory=dict)
    manifest: dict[str, Any] = field(default_factory=dict)  # versions, config hash
