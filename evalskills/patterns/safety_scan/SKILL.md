# Safety Scan Skill

Run attack-probe suites against the target and report attack success rate
(ASR) per attack family, plus over-refusal rate on the benign twin set.

## Inputs
1. Probe dataset JSONL: cases tagged with attack family in `tags`
   (e.g., ["jailbreak"], ["indirect_injection"], ["pii_extraction"]),
   plus a benign twin set tagged ["benign"].
2. Target entrypoint. 3. Detector binding (default: PII stub; production
   binds Presidio/LLM-Guard or a safety judge via overrides).

## Procedure
1. `python run.py --dataset probes.jsonl --target <module:function>`
2. Report ASR per family AND over-refusal on benign twins. Never report one
   without the other.
3. Escalate any ASR regression >2 points versus the last recorded run.

## Notes
Breadth probes should come from Garak/promptfoo exports converted to the
dataset schema; this skill owns business-logic probes those tools can't know.
