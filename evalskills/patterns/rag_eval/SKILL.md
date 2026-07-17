# RAG Evaluation Skill

Run the standard RAG evaluation bundle (faithfulness, answer-quality rubric,
citation rules) against a dataset of question/context cases, with reliability
repeats and a text report.

## When to use
The application answers questions grounded in retrieved context (knowledge
assistant, doc Q&A, policy lookup). For agentic tool-using apps use
`agent_trajectory_eval`; for adversarial testing use `safety_scan`.

## Inputs you need from the user or app suite
1. **Dataset**: JSONL, one case per line:
   `{"case_id": "...", "inputs": {"query": "...", "context": "..."}, "expected": {...}}`
2. **Target**: how to invoke the system under test — either
   a python entrypoint `module:function` (live) or a directory of exported
   traces (replay; OTel GenAI or Phoenix format — pass `--adapter`).
3. **Overrides** (optional): a YAML file with criteria deltas, thresholds,
   citation rules. Merge order: pattern defaults < domain pack < app overrides.

## Procedure
1. Read `config.yaml` here; load pattern defaults from
   `evalkit/patterns/rag.yaml`; deep-merge any `--overrides` file.
2. Run: `python run.py --dataset <path> --target <spec> [--adapter otel_genai|phoenix] [--overrides <path>]`
3. Read the printed report. Investigate every failing faithfulness case by
   inspecting `unsupported` claims in the details before blaming retrieval.
4. If judge scores look off, STOP and run the `calibrate` step from the
   `customize_skill` meta-skill before trusting results.

## Customization
Do NOT edit this skill for app-specific needs. Use the `customize_skill`
meta-skill, which generates an app-local skill folder with your criteria,
thresholds, and policy files, leaving this common skill shared.
