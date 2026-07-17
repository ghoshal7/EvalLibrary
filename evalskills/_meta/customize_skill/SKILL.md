# Meta-Skill: Customize a Common Skill

Generate an app-specific skill from a common pattern skill without touching
the shared skill. Output is a new skill folder under `apps/<app>/<skill>/`
containing only deltas: overrides YAML (criteria, thresholds, policies,
detector bindings), app prompts, and a thin run wrapper that calls the common
skill's runner with those deltas. The common skill stays shared and upgradable.

## Inputs to gather (ask the user if missing)
1. `--base`: which common skill to customize (e.g., patterns/rag_eval).
2. `--app`: application name (folder key).
3. Use-case context: domain, audience, hard policies, quality bar, known
   failure modes. Free text is fine; you will convert it into criteria.
4. Any existing domain pack to layer in (`domains/<name>/`).

## Procedure
1. Read the base skill's `SKILL.md`, `config.yaml`, and default prompts to
   learn its extension points (criteria file, policy file, thresholds).
2. Draft app criteria as Criterion entries (name, description, 1/3/5 anchors,
   weight). Rules: 3–6 criteria; each independently judgeable; anchors are
   behavioral, not adjectives ("cites clause numbers" not "very accurate").
   Convert every hard requirement into a deterministic rule (regex/policy),
   NOT a judge criterion — judges are for genuinely subjective qualities.
3. Run `python customize.py --base <skill> --app <name> --overrides-json '<json>'`
   to materialize the folder. Review the generated files with the user.
4. MANDATORY calibration gate: generate `calibration/README.md` instructions
   (30–50 items, human labels, kappa >= 0.7 vs the judge) and mark the skill
   `calibrated: false` in its config. The app skill must not gate releases
   until calibration flips to true.
5. If the customization looks broadly useful, open a promotion note to move
   it into the domain pack (never silently copy it around).

## Anti-patterns to refuse
- Editing the common skill in place for one app's needs.
- Putting compliance rules into judge criteria instead of the policy engine.
- Shipping judge-based gates with `calibrated: false`.
