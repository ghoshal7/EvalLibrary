# Agent Trajectory Evaluation Skill

Evaluate single-agent tool-use runs: tool/argument correctness, trajectory
match (strict/unordered/subset/superset), step efficiency, and declarative
action-policy adherence, with pass^k reliability over repeated attempts.

## Inputs
1. Dataset JSONL: cases with `expected.tools`, `expected.trajectory`,
   `expected.min_steps` as available.
2. Target: live entrypoint `module:function` returning (output, CanonicalTrace),
   or a directory of exported traces (`--adapter otel_genai|phoenix`).
3. Policy file (optional): YAML/JSON list of policy rules
   (forbidden_tool / arg_max / require_before) — the config-driven surface.

## Procedure
1. `python run.py --dataset <path> --target <spec> [--policies <path>] [--attempts 4]`
2. Report pass^k alongside means. A large pass@1 vs pass^4 gap = reliability
   problem even when quality means look fine.
3. For failing policy checks, quote the violation strings verbatim in your
   analysis; they are audit evidence.

## Customization
Use `customize_skill` to generate an app-local variant carrying your policy
file, expected trajectories, and thresholds.
