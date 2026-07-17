"""evalkit.tracing.adapters — vendor formats -> CanonicalTrace.

Input standardization layer. Each adapter accepts that vendor's native
export structure and emits CanonicalTrace; metrics never see vendor fields.

Implemented here:
  * OTelGenAIAdapter    — OpenTelemetry spans following GenAI semantic
                          conventions (gen_ai.* attributes), from an OTLP
                          JSON export or a list of span dicts.
  * PhoenixAdapter      — Arize Phoenix / OpenInference span export
                          (openinference.span.kind, input.value, ...).

Adding a vendor = one file implementing parse(raw) -> list[CanonicalTrace],
registered under registry kind 'adapter'. Nothing else changes.
"""
from __future__ import annotations

from typing import Any

from ...core.registry import register
from ...core.types import CanonicalSpan, CanonicalTrace, SpanKind

# ---------------------------------------------------------------------------

_OTEL_KIND_MAP = {
    # gen_ai.operation.name -> SpanKind
    "chat": SpanKind.LLM, "text_completion": SpanKind.LLM,
    "generate_content": SpanKind.LLM,
    "execute_tool": SpanKind.TOOL,
    "embeddings": SpanKind.RETRIEVER, "retrieve": SpanKind.RETRIEVER,
    "invoke_agent": SpanKind.AGENT, "create_agent": SpanKind.AGENT,
}

_OPENINFERENCE_KIND_MAP = {
    "LLM": SpanKind.LLM, "TOOL": SpanKind.TOOL, "RETRIEVER": SpanKind.RETRIEVER,
    "AGENT": SpanKind.AGENT, "CHAIN": SpanKind.CHAIN, "GUARDRAIL": SpanKind.GUARDRAIL,
    "EMBEDDING": SpanKind.RETRIEVER, "RERANKER": SpanKind.RETRIEVER,
}


@register("adapter", "otel_genai")
class OTelGenAIAdapter:
    """Parse OTel spans with GenAI semantic-convention attributes."""

    def parse(self, spans: list[dict[str, Any]]) -> list[CanonicalTrace]:
        traces: dict[str, CanonicalTrace] = {}
        for s in spans:
            attrs = s.get("attributes", {})
            op = attrs.get("gen_ai.operation.name", "")
            kind = _OTEL_KIND_MAP.get(op, SpanKind.OTHER)
            name = (
                attrs.get("gen_ai.tool.name")
                or attrs.get("gen_ai.agent.name")
                or attrs.get("gen_ai.request.model")
                or s.get("name", "span")
            )
            span = CanonicalSpan(
                span_id=s["span_id"],
                parent_id=s.get("parent_span_id"),
                kind=kind,
                name=name,
                start_ns=int(s.get("start_time_unix_nano", 0)),
                end_ns=int(s.get("end_time_unix_nano", 0)),
                inputs=_pick(attrs, {
                    "gen_ai.prompt": "prompt",
                    "gen_ai.input.messages": "messages",
                    "gen_ai.tool.call.arguments": "arguments",
                }),
                outputs=_pick(attrs, {
                    "gen_ai.completion": "completion",
                    "gen_ai.output.messages": "completion",
                    "gen_ai.tool.call.result": "result",
                }),
                attributes={
                    "model": attrs.get("gen_ai.request.model"),
                    "tokens_total": (
                        int(attrs.get("gen_ai.usage.input_tokens", 0))
                        + int(attrs.get("gen_ai.usage.output_tokens", 0))
                    ),
                },
                status=s.get("status", {}).get("code", "OK"),
                error=s.get("status", {}).get("description"),
            )
            tid = s["trace_id"]
            traces.setdefault(tid, CanonicalTrace(tid, metadata={"source": "otel_genai"}))
            traces[tid].spans.append(span)
        return list(traces.values())


@register("adapter", "phoenix")
class PhoenixAdapter:
    """Parse Arize Phoenix / OpenInference span exports."""

    def parse(self, spans: list[dict[str, Any]]) -> list[CanonicalTrace]:
        traces: dict[str, CanonicalTrace] = {}
        for s in spans:
            attrs = s.get("attributes", {})
            oi_kind = attrs.get("openinference.span.kind", "CHAIN")
            kind = _OPENINFERENCE_KIND_MAP.get(oi_kind, SpanKind.OTHER)
            inputs: dict[str, Any] = {}
            outputs: dict[str, Any] = {}
            if "input.value" in attrs:
                inputs["prompt" if kind == SpanKind.LLM else "arguments"] = attrs["input.value"]
            if "output.value" in attrs:
                outputs["completion" if kind == SpanKind.LLM else "result"] = attrs["output.value"]
            if "retrieval.documents" in attrs:
                outputs["documents"] = attrs["retrieval.documents"]
            span = CanonicalSpan(
                span_id=s["context"]["span_id"],
                parent_id=s.get("parent_id"),
                kind=kind,
                name=attrs.get("tool.name") or s.get("name", "span"),
                start_ns=int(s.get("start_time", 0)),
                end_ns=int(s.get("end_time", 0)),
                inputs=inputs,
                outputs=outputs,
                attributes={
                    "model": attrs.get("llm.model_name"),
                    "tokens_total": int(attrs.get("llm.token_count.total", 0)),
                },
                status=s.get("status_code", "OK"),
            )
            tid = s["context"]["trace_id"]
            traces.setdefault(tid, CanonicalTrace(tid, metadata={"source": "phoenix"}))
            traces[tid].spans.append(span)
        return list(traces.values())


def _pick(attrs: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    return {canon: attrs[src] for src, canon in mapping.items() if src in attrs}
