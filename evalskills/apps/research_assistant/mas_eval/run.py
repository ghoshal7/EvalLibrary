#!/usr/bin/env python3
"""App wrapper: research_assistant/mas_eval — data only; logic in patterns/mas_eval."""
import subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
BASE = HERE.parents[2] / "patterns" / "mas_eval"
cmd = [sys.executable, str(BASE / "run.py"),
       "--composition", str(HERE / "composition.json"), *sys.argv[1:]]
raise SystemExit(subprocess.call(cmd))
