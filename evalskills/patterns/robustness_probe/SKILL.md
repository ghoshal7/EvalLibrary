# Robustness Probe Skill

Score output stability under semantics-preserving input perturbations
(typo, case, whitespace, distractor). Group A "robustness" from the
white paper. Score 1.0 = identical behavior across perturbations.

## Inputs
1. Dataset JSONL: same schema as the pattern's normal cases (perturbations
   are generated, not authored). 2. LIVE target `module:function` (replay
   is impossible — perturbed inputs must be re-inferred).
3. Optional: --field (which input field to perturb), --threshold.

## Procedure
1. `python run.py --dataset <path> --target <module:function> [--field query]`
2. Read per-perturbation similarity in details. A low single family
   (e.g., distractor) is a targeted weakness; uniformly low = brittle.
3. Robustness complements, never replaces, quality metrics: run alongside
   the pattern skill and compare score drop, not absolute values.
