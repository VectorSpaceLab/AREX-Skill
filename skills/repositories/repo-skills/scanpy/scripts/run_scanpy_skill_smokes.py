#!/usr/bin/env python3
"""Run safe bundled Scanpy skill smoke helpers in the current Python."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


HELPERS = [
    ("io-data-access", ["--exercise-obs-df", "--exercise-backed"]),
    ("preprocessing-qc", ["--mode", "normalize-log-hvg-pca"]),
    ("graph-embedding-analysis", []),
    ("plotting-reporting", []),
    ("external-integrations", ["--feature", "leiden", "--feature", "skmisc", "--json"]),
]

SCRIPT_NAMES = {
    "io-data-access": "scanpy_io_roundtrip.py",
    "preprocessing-qc": "scanpy_preprocess_qc_smoke.py",
    "graph-embedding-analysis": "scanpy_analysis_smoke.py",
    "plotting-reporting": "scanpy_headless_plot_smoke.py",
    "external-integrations": "check_scanpy_optional_deps.py",
}


def run_helper(skill_root: Path, subskill: str, extra_args: list[str], timeout: int) -> dict[str, object]:
    script = skill_root / "sub-skills" / subskill / "scripts" / SCRIPT_NAMES[subskill]
    completed = subprocess.run(
        [sys.executable, str(script), *extra_args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return {
        "subskill": subskill,
        "script": str(script.relative_to(skill_root)),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--timeout", type=int, default=180, help="Timeout in seconds for each helper.")
    args = parser.parse_args()

    results = [run_helper(args.skill_root, subskill, extra_args, args.timeout) for subskill, extra_args in HELPERS]
    print(json.dumps(results, indent=2))
    return 0 if all(result["returncode"] == 0 for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
