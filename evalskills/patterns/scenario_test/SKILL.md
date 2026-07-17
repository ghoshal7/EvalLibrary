# Scenario Test Skill

Run enumerated situation tests (edge cases, business rules, failure
handling) with explicit per-case assertions. Group C "scenario testing".
Scenario suites are pure datasets: given (inputs) / then (assertions).

## Dataset schema
{"case_id": "...", "inputs": {...},
 "expected": {"assertions": [{"type": "contains|not_contains|regex|tool_used|tool_not_used|max_tool_calls", "value": ...}]},
 "tags": ["<scenario_family>"]}

## Procedure
1. `python run.py --dataset scenarios.jsonl --target <module:function>`
2. Report shows pass rate per scenario family plus failed assertion names
   per case — each failure is a concrete broken behavior, not a score dip.
3. New production incidents become new scenario rows (regression ratchet).
