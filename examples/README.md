# Demo walkthrough
export PYTHONPATH=$PWD/examples

# Common skills against mock apps
python3 evalskills/patterns/rag_eval/run.py --dataset examples/data/rag_cases.jsonl --target mock_app:rag_answer --attempts 2
python3 evalskills/patterns/agent_trajectory_eval/run.py --dataset examples/data/agent_cases.jsonl --target mock_app:support_agent --policies evalskills/domains/finance/policies/complaints_handling.json --attempts 4
python3 evalskills/patterns/safety_scan/run.py --dataset examples/data/safety_probes.jsonl --target mock_app:chat
python3 evalskills/patterns/robustness_probe/run.py --dataset examples/data/rag_cases.jsonl --target mock_app:rag_answer
python3 evalskills/patterns/scenario_test/run.py --dataset examples/data/scenarios.jsonl --target mock_app:support_agent

# Multi-agent: single-composition demo, then the two-pattern app example
python3 evalskills/patterns/mas_eval/run.py --dataset examples/data/mas_cases.jsonl --target mock_app:mas_pipeline --composition evalskills/patterns/mas_eval/composition.json --attempts 4
python3 evalskills/apps/research_assistant/mas_eval/run.py --dataset evalskills/apps/research_assistant/mas_eval/cases.jsonl --target mock_app:research_mas --attempts 4

# Meta-skills
python3 evalskills/_meta/customize_skill/customize.py --base patterns/rag_eval --app support_bot --overrides-json '{"criteria": [...]}'
python3 evalskills/_meta/generate_skill/generate.py --name extraction_eval --pattern extraction --scorers json_schema_lite,exact_match

# Production judge binding (skills use the stub when unset)
export EVAL_JUDGE_MODEL="my_clients:claude_judge"   # any module:function str->str
