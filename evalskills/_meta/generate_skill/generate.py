#!/usr/bin/env python3
"""Generate a new skill folder from the template."""
import argparse
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = SKILLS_ROOT / "templates" / "skill_template"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--pattern", required=True)
    ap.add_argument("--scorers", default="exact_match")
    args = ap.parse_args()

    dest = SKILLS_ROOT / "patterns" / args.name
    assert not dest.exists(), f"{dest} already exists"
    dest.mkdir(parents=True)
    subs = {"{{name}}": args.name, "{{pattern}}": args.pattern,
            "{{scorers}}": args.scorers}
    for src in TEMPLATE.rglob("*"):
        if src.is_file():
            rel = src.relative_to(TEMPLATE)
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            text = src.read_text()
            for k, v in subs.items():
                text = text.replace(k, v)
            out.write_text(text)
    print(f"created {dest}")
    for p in sorted(dest.rglob("*")):
        if p.is_file():
            print("  ", p.relative_to(SKILLS_ROOT))

if __name__ == "__main__":
    main()
