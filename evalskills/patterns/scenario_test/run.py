#!/usr/bin/env python3
import argparse, importlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "evalkit"))
import evalkit
from evalkit.metrics.scenario import scenario_assertions

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--target", required=True)
    args = ap.parse_args()
    cases = [evalkit.EvalCase(**json.loads(l))
             for l in Path(args.dataset).read_text().splitlines() if l.strip()]
    mod, fn = args.target.split(":")
    target = evalkit.resolve("target", "callable")(
        getattr(importlib.import_module(mod), fn))
    rep = evalkit.run_suite("scenario_test", cases, target, [scenario_assertions()],
                            manifest={"skill": "scenario_test/1.0.0"})
    fams = {}
    for cr in rep.case_results:
        fam = next((c.tags[0] for c in cases if c.case_id == cr.case_id and c.tags), "?")
        m = cr.metrics[0] if cr.metrics else None
        fams.setdefault(fam, []).append(m.passed if m else False)
        if m and m.passed is False:
            print(f"FAIL {cr.case_id} [{fam}]: {m.details['failed_assertions']}")
    print(f"Scenario test  run={rep.run_id}")
    for fam, oks in sorted(fams.items()):
        print(f"  pass[{fam:22s}] = {sum(bool(o) for o in oks)}/{len(oks)}")

if __name__ == "__main__":
    main()
