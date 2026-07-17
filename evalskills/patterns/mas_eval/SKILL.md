# Multi-Agent System Evaluation Skill

Evaluate a multi-agent use case across all three MAS layers with ONE
system trace: outcome (end-to-end final output), process (handoff flow +
coordination efficiency across patterns), and component (per-agent
pattern metrics via scope projection).

## Composition file (the use-case topology as data)
Each use case declares how patterns work together in composition.json:
{
  "flow": ["orchestrator->researcher", "researcher->writer"],
  "flow_mode": "strict",
  "max_redundant_tool_calls": 0,
  "agents": {
    "researcher": {"pattern": "agent_tool_use",
                    "scorers": [{"name": "tool_correctness", "params": {}}]},
    "writer":     {"pattern": "rag",
                    "scorers": [{"name": "regex_rules",
                                 "params": {"forbidden": ["cheese"]}}]}
  },
  "outcome": [{"name": "scenario_assertions", "params": {}}]
}
Agents may implement ANY pattern from the survey; their scorers are the
same L1 names used by single-pattern skills — scope projection makes the
system trace look like a single-agent trace to each of them.

## Dataset schema
Cases carry expected.flow (process), expected.assertions (outcome), and
whatever each agent's scorers need (e.g., expected.tools).

## Procedure
1. `python run.py --dataset cases.jsonl --target <module:function|trace_dir> --composition composition.json [--attempts 4]`
2. Read the three blocks: outcome metrics, process metrics
   (handoff_*, coordination_efficiency with redundancy stats), and
   per-agent component metrics (named <agent>.<metric>).
3. Diagnose in layer order: outcome fail + process pass => look at
   component scores; process fail => topology/handoff bug regardless of
   outcome (silent-success risk per the MAS survey).

## Customization
customize_skill works on this skill too: app deltas carry the composition
file, per-agent criteria, and thresholds.
