"""evalkit.metrics.robustness — perturbation-based robustness (L1).

Group A type 'robustness' from the white paper: perturb the input in
semantics-preserving ways, re-invoke the target, and score output
stability. Perturbers are pluggable; similarity is jaccard or exact.
"""
from __future__ import annotations
import random, re
from typing import Any, Callable, Optional
from ..core.registry import register
from ..core.types import CanonicalTrace, EvalCase, MetricResult

Perturber = Callable[[dict], dict]


def _perturb_text(inputs: dict, field: str, fn: Callable[[str], str]) -> dict:
    out = dict(inputs)
    if field in out and isinstance(out[field], str):
        out[field] = fn(out[field])
    return out


def typo_swap(field: str = "query") -> Perturber:
    def fn(t: str) -> str:
        words = t.split()
        for i, w in enumerate(words):
            if len(w) >= 6:
                words[i] = w[:2] + w[3] + w[2] + w[4:]   # swap chars 3&4
                break
        return " ".join(words)
    return lambda inp: _perturb_text(inp, field, fn)


def case_scramble(field: str = "query") -> Perturber:
    rng = random.Random(7)
    return lambda inp: _perturb_text(
        inp, field, lambda t: "".join(c.upper() if rng.random() < .3 else c for c in t))


def whitespace_noise(field: str = "query") -> Perturber:
    return lambda inp: _perturb_text(inp, field, lambda t: "  " + t.replace(" ", "  ") + " ")


def distractor_suffix(field: str = "query",
                      text: str = " (note: unrelated aside, please ignore)") -> Perturber:
    return lambda inp: _perturb_text(inp, field, lambda t: t + text)


DEFAULT_PERTURBERS: dict[str, Perturber] = {}   # filled by factory below


def _jaccard(a: str, b: str) -> float:
    sa, sb = set(re.findall(r"\w+", a.lower())), set(re.findall(r"\w+", b.lower()))
    return len(sa & sb) / len(sa | sb) if (sa or sb) else 1.0


@register("scorer", "robustness")
def robustness(target, perturbers: Optional[dict[str, Perturber]] = None,
               field: str = "query", compare: str = "jaccard",
               pass_threshold: float = 0.7):
    """Re-invokes `target` on perturbed inputs; scores mean output similarity
    to the unperturbed output. Score 1.0 = fully stable."""
    perturbers = perturbers or {
        "typo": typo_swap(field), "case": case_scramble(field),
        "whitespace": whitespace_noise(field), "distractor": distractor_suffix(field),
    }
    def scorer(case: EvalCase, output: Any, trace: Optional[CanonicalTrace]) -> MetricResult:
        base = str(output)
        details, sims = {}, []
        for name, fn in perturbers.items():
            pert = EvalCase(f"{case.case_id}~{name}", fn(case.inputs), case.expected, case.tags)
            try:
                out2, _ = target(pert)
                s = (1.0 if str(out2) == base else 0.0) if compare == "exact" \
                    else _jaccard(base, str(out2))
            except Exception as e:                      # crash on perturbation = 0
                s, out2 = 0.0, f"ERROR {e}"
            sims.append(s)
            details[name] = round(s, 3)
        score = sum(sims) / len(sims) if sims else 0.0
        return MetricResult("robustness", round(score, 4), score >= pass_threshold,
                            {"per_perturbation": details}, "1.0")
    return scorer
