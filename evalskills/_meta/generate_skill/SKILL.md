# Meta-Skill: Generate a New Skill

Create a brand-new eval skill (for a pattern or use case not covered by an
existing common skill) from the skill template, wired to evalkit primitives.

## Inputs to gather
1. Task pattern (one of the nine in the white paper, or "custom").
2. What the target looks like (live entrypoint vs. trace replay; which
   tracing vendor -> adapter).
3. Which evalkit scorers/judges apply (list `evalkit.available('scorer')`
   and `available('judge')` and select; only write a new scorer if nothing
   fits, and put it in evalkit L1 as generic code, never inside the skill).
4. Dataset schema: what `inputs`/`expected` fields cases will carry.

## Procedure
1. `python generate.py --name <skill_name> --pattern <pattern> --scorers a,b,c`
2. Fill the generated SKILL.md sections marked TODO: when-to-use, dataset
   schema, interpretation guidance. A skill an agent can't follow from its
   SKILL.md alone is not done.
3. Add default judge criteria under prompts/ if any judge is used, then run
   the customize_skill calibration gate before first real use.
4. Register the skill in the library index (`evalskills/INDEX.md`).

## Rules
- Skills contain composition and instructions only; metric logic belongs in
  evalkit. If you are writing scoring math in a skill, stop and move it down.
- Every generated skill declares its pattern pack and merge order explicitly.
