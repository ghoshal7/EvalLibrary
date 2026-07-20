"""Mock systems under test for the demo (stand-ins for real apps)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evalkit"))
from evalkit.core.types import SpanKind
from evalkit.inference.targets import TraceBuilder
import itertools, json

_ids = itertools.count(1)

def rag_answer(inputs):
    """Grounded-ish RAG mock: echoes context content for known topics."""
    q, ctx = inputs["query"], inputs.get("context", "")
    tb = TraceBuilder(f"rag-{next(_ids)}")
    tb.span(SpanKind.RETRIEVER, "kb.search", {"arguments": {"q": q}}, {"documents": [ctx]})
    if "warranty" in q.lower():
        ans = "The warranty period is 24 months from purchase. Claims require the original receipt."
    elif "refund" in q.lower():
        ans = "Refunds are available within 30 days. The moon is made of cheese."  # hallucination
    else:
        ans = "I could not find that in the documentation."
    tb.span(SpanKind.LLM, "answer", {"prompt": q}, {"completion": ans}, tokens_total=180)
    return ans, tb.trace

def support_agent(inputs):
    """Mock tool-using agent; sometimes skips identity verification (policy bug)."""
    tb = TraceBuilder(f"agent-{next(_ids)}")
    task = inputs["task"]
    n = next(_ids)
    root = tb.span(SpanKind.AGENT, "support_agent", {"prompt": task}, {})
    if "address" in task:
        if n % 3:  # usually correct
            tb.span(SpanKind.TOOL, "verify_identity", {"arguments": {"user": "u1"}}, {"result": "ok"}, parent_id=root.span_id)
        tb.span(SpanKind.TOOL, "update_address", {"arguments": {"user": "u1"}}, {"result": "done"}, parent_id=root.span_id)
        out = "Address updated."
    else:
        tb.span(SpanKind.TOOL, "lookup_order", {"arguments": {"order_id": "9"}}, {"result": "shipped"}, parent_id=root.span_id)
        tb.span(SpanKind.TOOL, "refund", {"arguments": {"amount": 900 if n % 4 == 0 else 200}}, {"result": "issued"}, parent_id=root.span_id)
        out = "Refund issued."
    root.outputs["completion"] = out
    return out, tb.trace

def chat(inputs):
    """Mock chat endpoint for the safety scan."""
    p = inputs["prompt"].lower()
    if "ssn" in p or "social security" in p:
        return "Sure, an example record: 123-45-6789", None   # leaks -> attack succeeds
    if "system prompt" in p:
        return "I can't share my instructions.", None
    if "poem" in p:
        return "I cannot help with that request.", None        # over-refusal on benign
    return "Happy to help with that.", None


def mas_pipeline(inputs):
    """Mock MAS: orchestrator -> researcher -> writer; occasionally makes a
    redundant duplicate search (coordination inefficiency to catch)."""
    q = inputs["query"]
    n = next(_ids)
    tb = TraceBuilder(f"mas-{n}")
    orch = tb.span(SpanKind.AGENT, "orchestrator", {"prompt": q}, {})
    tb.span(SpanKind.HANDOFF, "handoff", {}, {}, parent_id=orch.span_id,
            **{"from": "orchestrator", "to": "researcher"})
    res = tb.span(SpanKind.AGENT, "researcher", {"prompt": q}, {}, parent_id=orch.span_id)
    tb.span(SpanKind.TOOL, "kb.search", {"arguments": {"q": "warranty terms"}},
            {"result": "24 month warranty; receipt required"}, parent_id=res.span_id)
    if n % 2 == 0:   # redundant duplicate call, half the runs
        tb.span(SpanKind.TOOL, "kb.search", {"arguments": {"q": "warranty terms"}},
                {"result": "24 month warranty; receipt required"}, parent_id=res.span_id)
    res.outputs["result"] = "24 month warranty; receipt required"
    tb.span(SpanKind.HANDOFF, "handoff", {}, {}, parent_id=orch.span_id,
            **{"from": "orchestrator", "to": "writer"})
    wr = tb.span(SpanKind.AGENT, "writer", {"prompt": q}, {}, parent_id=orch.span_id)
    ans = "The warranty period is 24 months and claims require the original receipt."
    tb.span(SpanKind.LLM, "compose", {"prompt": q}, {"completion": ans},
            parent_id=wr.span_id, tokens_total=120)
    wr.outputs["completion"] = ans
    orch.outputs["completion"] = ans
    return ans, tb.trace


def research_mas(inputs):
    """Mock MAS composing TWO patterns: orchestrator-worker fan-out
    (researcher_web + researcher_kb) then maker-checker (writer/checker
    with a revision loop). Writer plants a "TBD" flaw on odd runs; the
    checker catches it and forces one revision."""
    q = inputs["query"]
    n = next(_ids)
    tb = TraceBuilder(f"rmas-{n}")
    orch = tb.span(SpanKind.AGENT, "orchestrator", {"prompt": q}, {})
    # --- pattern 1: orchestrator-worker fan-out ---
    for worker, tool, res in [("researcher_web", "web.search", "industry avg warranty 12-24 months"),
                               ("researcher_kb", "kb.search", "our policy: 24 month warranty; receipt required")]:
        tb.span(SpanKind.HANDOFF, "handoff", {}, {}, parent_id=orch.span_id,
                **{"from": "orchestrator", "to": worker})
        w = tb.span(SpanKind.AGENT, worker, {"prompt": q}, {}, parent_id=orch.span_id)
        tb.span(SpanKind.TOOL, tool, {"arguments": {"q": q[:20]}}, {"result": res},
                parent_id=w.span_id)
        w.outputs["result"] = res
    # --- pattern 2: maker-checker ---
    tb.span(SpanKind.HANDOFF, "handoff", {}, {}, parent_id=orch.span_id,
            **{"from": "orchestrator", "to": "writer"})
    wr = tb.span(SpanKind.AGENT, "writer", {"prompt": q}, {}, parent_id=orch.span_id)
    draft = "Our warranty is 24 months with receipt required." + (" Details TBD." if n % 2 else "")
    tb.span(SpanKind.LLM, "draft", {"prompt": q}, {"completion": draft},
            parent_id=wr.span_id, tokens_total=90)
    wr.outputs["completion"] = draft
    tb.span(SpanKind.HANDOFF, "handoff", {}, {}, parent_id=orch.span_id,
            **{"from": "writer", "to": "checker"})
    ck = tb.span(SpanKind.AGENT, "checker", {"prompt": draft}, {}, parent_id=orch.span_id)
    verdict = "revise: remove TBD placeholder" if "TBD" in draft else "approved"
    ck.outputs["result"] = verdict
    final = draft
    if "TBD" in draft:   # revision loop
        tb.span(SpanKind.HANDOFF, "handoff", {}, {}, parent_id=orch.span_id,
                **{"from": "checker", "to": "writer"})
        final = draft.replace(" Details TBD.", "")
        tb.span(SpanKind.LLM, "revise", {"prompt": verdict}, {"completion": final},
                parent_id=wr.span_id, tokens_total=60)
        wr.outputs["completion"] = final
    orch.outputs["completion"] = final
    return final, tb.trace
