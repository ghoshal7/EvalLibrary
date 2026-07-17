# Calibration gate for support_bot/rag_eval
1. Sample 30-50 representative cases; collect human labels for every
   judge-based metric in overrides.yaml.
2. Run the judge on the same cases; compute Cohen's kappa
   (evalkit.core.stats.cohen_kappa). Requirement: kappa >= 0.7.
3. On pass, set "calibrated": true in config.yaml and record the
   kappa, judge model id, and prompt versions here.
Judge-gated release decisions are FORBIDDEN while calibrated=false.
