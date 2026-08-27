#!/usr/bin/env python3
"""Run PyGAD repo-skill bundled smoke scripts.

This helper executes deterministic smoke scripts that live inside this skill
folder. By default it runs only core CPU checks and skips optional Keras/Torch
framework templates unless requested.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CORE_SCRIPTS = [
    ROOT / "scripts" / "pygad_quick_check.py",
    ROOT / "sub-skills" / "genetic-algorithm" / "scripts" / "core_ga_smoke.py",
    ROOT / "sub-skills" / "genetic-algorithm" / "scripts" / "multi_objective_template.py",
    ROOT / "sub-skills" / "benchmarks" / "scripts" / "benchmark_smoke.py",
    ROOT / "sub-skills" / "results-and-visuals" / "scripts" / "plot_report_smoke.py",
    ROOT / "sub-skills" / "neural-networks" / "scripts" / "neural_internal_smoke.py",
]

OPTIONAL_FRAMEWORK_SCRIPT = ROOT / "sub-skills" / "neural-networks" / "scripts" / "keras_torch_templates.py"


def run_script(path: Path, extra_args: list[str] | None = None) -> dict:
    env = os.environ.copy()
    env.setdefault("MPLBACKEND", "Agg")
    cmd = [sys.executable, str(path)]
    if extra_args:
        cmd.extend(extra_args)
    completed = subprocess.run(cmd, text=True, capture_output=True, env=env)
    return {
        "script": str(path.relative_to(ROOT)),
        "command": [Path(sys.executable).name, str(path.relative_to(ROOT)), *(extra_args or [])],
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-framework",
        action="store_true",
        help="Also run the optional Keras/Torch template with --backend auto.",
    )
    parser.add_argument(
        "--nsga3",
        action="store_true",
        help="Also run the multi-objective template once with NSGA-III.",
    )
    args = parser.parse_args()

    results = []
    for path in CORE_SCRIPTS:
        results.append(run_script(path))
        if results[-1]["returncode"] != 0:
            break

    if args.nsga3 and all(item["returncode"] == 0 for item in results):
        path = ROOT / "sub-skills" / "genetic-algorithm" / "scripts" / "multi_objective_template.py"
        results.append(run_script(path, ["--selector", "nsga3", "--nsga3-num-divisions", "4"]))

    if args.include_framework and all(item["returncode"] == 0 for item in results):
        results.append(run_script(OPTIONAL_FRAMEWORK_SCRIPT, ["--backend", "auto"]))

    summary = {
        "root": ROOT.name,
        "all_passed": all(item["returncode"] == 0 for item in results),
        "results": results,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))

    if not summary["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
