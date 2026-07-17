# research_assistant :: mas_eval (app example)

Worked L4 example: a research-assistant MAS composing TWO MAS patterns —
orchestrator-worker fan-out (researcher_web + researcher_kb, each running
the single-agent tool-use pattern in its scope) followed by maker-checker
(writer drafts, checker issues a verdict, rejected drafts loop back once).

This folder carries ONLY use-case data: composition.json (topology + per-
agent expectations + budgets), the app dataset, and a thin wrapper.
Logic lives in patterns/mas_eval and evalkit.

Run: `python run.py --dataset cases.jsonl --target mock_app:research_mas --attempts 4`

Interpretation for THIS app:
- outcome `scenario` must pass with not_contains "TBD" — proves the
  checker loop bites (a passing draft path AND a caught-flaw path both
  end clean).
- `handoff_subset` verifies both fan-out edges and the writer->checker
  edge exist regardless of interleaving.
- coordination_efficiency budget = 1 redundant call: one revision loop is
  paid for; two means the checker is thrashing.
- component: researcher_web.tool_correctness / researcher_kb.tool_correctness
  use per-agent expected tools from composition.json; checker.regex_rules
  requires an explicit verdict token.
