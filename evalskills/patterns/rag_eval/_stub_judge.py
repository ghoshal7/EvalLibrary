"""Deterministic stub judge for demos/CI — replace via EVAL_JUDGE_MODEL."""
import json, re

def stub_model(prompt: str) -> str:
    if "atomic factual claims" in prompt:
        text = prompt.split("Text:")[-1]
        sents = [s.strip() for s in re.split(r"[.!?]\s+", text) if len(s.strip()) > 12]
        return json.dumps(sents[:6] or ["(no claims)"])
    if "is the CLAIM fully supported" in prompt:
        claim = prompt.split("CLAIM:")[1].split("CONTEXT:")[0]
        ctx = prompt.split("CONTEXT:")[1]
        words = [w.lower()[:5] for w in re.findall(r"\w{5,}", claim)]
        hit = sum(1 for w in words if w in ctx.lower())
        return "yes" if words and hit / len(words) >= 0.6 else "no"
    if '"scores"' in prompt:
        resp = prompt.split("[RESPONSE TO EVALUATE]")[1].split("[")[0]
        names = re.findall(r"^- (\w+):", prompt.split("[CRITERIA]")[1], re.M)
        base = 5 if len(resp.split()) > 8 else 2
        return json.dumps({"scores": {n: base for n in names}, "rationale": "stub"})
    return "{}"
