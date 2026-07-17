#!/usr/bin/env python3
"""App wrapper: support_bot/rag_eval — deltas only; logic lives in the common skill."""
import subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
BASE = Path("../../../patterns/rag_eval")
cmd = [sys.executable, str(HERE / BASE / "run.py"),
       "--overrides", str(HERE / "overrides.yaml"), *sys.argv[1:]]
raise SystemExit(subprocess.call(cmd))
