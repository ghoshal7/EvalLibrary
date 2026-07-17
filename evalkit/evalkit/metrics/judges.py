"""evalkit.metrics.judges — LLM-as-judge scaffolding (L1).

Design: ONE rubric scaffold; criteria are data (the criteria-as-parameter
mechanism from the white paper §6.2). The judge model itself is pluggable:
any callable str -> str (an API client in production, a stub in tests).

Prompt layering: scaffold + criteria (pattern default, domain layer,
app overrides are merged upstream by the skill layer) + case content.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ..core.registry import register
from ..core.types import CanonicalTrace, EvalCase, MetricResult

JudgeModel = Callable[[str], str]

SCAFFOLD = """You are a strict evaluation judge. Evaluate the RESPONSE against
each criterion. Think step by step, then output ONLY JSON:
{{"scores": {{<criterion_name>: <1-5 integer>, ...}}, "rationale": "<brief>"}}

[TASK INPUT]
{task_input}

[RESPONSE TO EVALUATE]
{response}
{context_block}
[CRITERIA]
{criteria_block}
"""


@dataclass
class Criterion:
    name: str
    description: str
    anchors: dict[int, str] = field(default_factory=dict)   # score level -> meaning
    weight: float = 1.0

    def render(self) -> str:
        lines = [f"- {self.name}: {self.description}"]
        for lvl in sorted(self.anchors):
            lines.append(f"    {lvl} = {self.anchors[lvl]}")
        return "\n".join(lines)


@register("judge", "rubric")
def rubric_judge(criteria: list[Criterion], model: JudgeModel,
                 pass_threshold: float = 0.7, name: str = "rubric"):
    """Weighted-rubric judge. Score normalized to 0..1."""
    def scorer(case: EvalCase, output: Any, trace: Optional[CanonicalTrace]) -> MetricResult:
        ctx = case.inputs.get("context")
        prompt = SCAFFOLD.format(
            task_input=json.dumps(case.inputs.get("query", case.inputs))[:4000],
            response=str(output)[:6000],
            context_block=f"\n[CONTEXT]\n{str(ctx)[:6000]}\n" if ctx else "",
            criteria_block="\n".join(c.render() for c in criteria),
        )
        raw = model(prompt)
        scores = _parse_scores(raw, [c.name for c in criteria])
        total_w = sum(c.weight for c in criteria) or 1.0
        norm = sum(((scores.get(c.name, 1) - 1) / 4) * c.weight for c in criteria) / total_w
        return MetricResult(name, round(norm, 4), norm >= pass_threshold,
                            {"per_criterion": scores}, "1.0")
    return scorer


@register("judge", "faithfulness_qag")
def faithfulness_qag(model: JudgeModel, pass_threshold: float = 0.8):
    """QAG-lite faithfulness: decompose answer into claims, verify each
    against context. Reusable for RAG (retrieved context) and
    summarization (source-as-context) and fan-out synthesis (worker
    outputs as context)."""
    def scorer(case, output, trace) -> MetricResult:
        context = case.inputs.get("context", "")
        decomp = model(
            "List the atomic factual claims in the text as a JSON array of "
            f"strings. Text:\n{str(output)[:6000]}"
        )
        claims = _parse_list(decomp)
        if not claims:
            return MetricResult("faithfulness", 0.0, False, {"error": "no claims parsed"}, "1.0")
        verdicts = []
        for claim in claims[:20]:
            v = model(
                "Answer only yes or no: is the CLAIM fully supported by the CONTEXT?\n"
                f"CLAIM: {claim}\nCONTEXT: {str(context)[:8000]}"
            )
            verdicts.append(bool(re.search(r"\byes\b", v, re.I)))
        score = sum(verdicts) / len(verdicts)
        return MetricResult("faithfulness", round(score, 4), score >= pass_threshold,
                            {"claims": len(claims),
                             "unsupported": [c for c, ok in zip(claims, verdicts) if not ok]},
                            "1.0")
    return scorer


def _parse_scores(raw: str, names: list[str]) -> dict[str, int]:
    m = re.search(r"\{.*\}", raw, re.S)
    if m:
        try:
            data = json.loads(m.group())
            return {k: int(v) for k, v in data.get("scores", {}).items() if k in names}
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    return {}


def _parse_list(raw: str) -> list[str]:
    m = re.search(r"\[.*\]", raw, re.S)
    if m:
        try:
            return [str(x) for x in json.loads(m.group())]
        except json.JSONDecodeError:
            pass
    return [ln.strip("-* ") for ln in raw.splitlines() if ln.strip("-* ").strip()]
