"""Rebuild everything: hourly table, checks, analysis, models, charts."""
import runpy
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC))

for step in ["build_table", "checks", "explore", "step_changes", "models", "regime"]:
    print(f"\n=== {step}")
    runpy.run_path(str(SRC / f"{step}.py"), run_name="__main__")
