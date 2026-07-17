#!/usr/bin/env python3
"""Materialize an app-specific skill as deltas over a common skill."""
import argparse, json, textwrap
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]

WRAPPER = '''#!/usr/bin/env python3
"""App wrapper: {app}/{base_name} — deltas only; logic lives in the common skill."""
import subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
BASE = Path("{base_rel}")
cmd = [sys.executable, str(HERE / BASE / "run.py"),
       "--overrides", str(HERE / "overrides.yaml"), *sys.argv[1:]]
raise SystemExit(subprocess.call(cmd))
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)           # e.g. patterns/rag_eval
    ap.add_argument("--app", required=True)
    ap.add_argument("--overrides-json", required=True) # criteria/policies/thresholds
    args = ap.parse_args()

    base = SKILLS_ROOT / args.base
    assert (base / "SKILL.md").exists(), f"base skill not found: {base}"
    ov = json.loads(args.overrides_json)

    dest = SKILLS_ROOT / "apps" / args.app / base.name
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "calibration").mkdir(exist_ok=True)

    # overrides.yaml (written as JSON — valid YAML subset, zero-dep)
    (dest / "overrides.yaml").write_text(json.dumps(ov, indent=2))

    depth = len(dest.relative_to(SKILLS_ROOT).parts)
    base_rel = "/".join([".."] * depth + list(Path(args.base).parts))
    (dest / "run.py").write_text(WRAPPER.format(
        app=args.app, base_name=base.name, base_rel=base_rel))

    (dest / "config.yaml").write_text(json.dumps({
        "skill": f"{args.app}/{base.name}", "version": "0.1.0",
        "base": args.base, "calibrated": False,
    }, indent=2))

    (dest / "calibration" / "README.md").write_text(textwrap.dedent(f"""\
        # Calibration gate for {args.app}/{base.name}
        1. Sample 30-50 representative cases; collect human labels for every
           judge-based metric in overrides.yaml.
        2. Run the judge on the same cases; compute Cohen's kappa
           (evalkit.core.stats.cohen_kappa). Requirement: kappa >= 0.7.
        3. On pass, set "calibrated": true in config.yaml and record the
           kappa, judge model id, and prompt versions here.
        Judge-gated release decisions are FORBIDDEN while calibrated=false.
        """))

    (dest / "SKILL.md").write_text(textwrap.dedent(f"""\
        # {args.app} :: {base.name} (app-customized)
        Deltas over `{args.base}` — see that skill for procedure.
        This folder carries ONLY: overrides.yaml (criteria/policies/thresholds),
        app prompts, calibration assets. Run: `python run.py --dataset ... --target ...`
        Status: calibrated = false (see calibration/README.md).
        """))

    print(f"created {dest}")
    for p in sorted(dest.rglob("*")):
        if p.is_file():
            print("  ", p.relative_to(SKILLS_ROOT))

if __name__ == "__main__":
    main()
