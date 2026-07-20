# Multi-Agent System Evaluation Skill

Evaluate a multi-agent use case across all three MAS layers with ONE
system trace: outcome (end-to-end final output), process (handoff flow +
coordination efficiency across patterns), and component (per-agent
pattern metrics via scope projection).

## Composition file (the use-case topology as data)
Two DISTINCT pattern concepts appear, by design:
- "mas_patterns": the MAS COORDINATION patterns this use case composes
  (must name evalkit packs: mas_orchestrator_worker, mas_maker_checker, ...).
- agents.<name>.task_pattern: the TASK pattern that agent runs inside its
  scope (rag, agent_tool_use, classification, ... from the GenAI survey).

{
  "mas_patterns": ["mas_orchestrator_worker"],
  "flow": ["orchestrator->researcher", "orchestrator->writer"],
  "flow_mode": "strict",
  "max_redundant_tool_calls": 0,
  "agents": {
    "researcher": {"task_pattern": "agent_tool_use",
                    "scorers": [{"name": "tool_correctness"}],
                    "expected": {"tools": [{"name": "kb.search"}]}},
    "writer":     {"task_pattern": "rag",
                    "scorers": [{"name": "regex_rules",
                                 "params": {"forbidden": ["cheese"]}}]}
  },
  "outcome": [{"name": "scenario_assertions", "params": {}}]
}
Agents may implement ANY task pattern from the survey; their scorers are
the same L1 names used by single-pattern skills — scope projection makes
the system trace look like a single-agent trace to each of them. The
composed mas_patterns are recorded in the run manifest for attribution.

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
