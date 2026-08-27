#!/usr/bin/env python3
"""Run bundled ANTsPy repo-skill smoke checks with the current Python."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SMOKE_SCRIPTS = [
    "sub-skills/image-core/scripts/antspy_image_smoke.py",
    "sub-skills/image-ops-math/scripts/antspy_ops_smoke.py",
    "sub-skills/registration-transforms/scripts/antspy_registration_smoke.py",
    "sub-skills/segmentation-labels/scripts/antspy_segmentation_smoke.py",
    "sub-skills/visualization-interop/scripts/antspy_plotting_smoke.py",
    "sub-skills/learning-deeplearn/scripts/antspy_deeplearn_smoke.py",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run all bundled ANTsPy smoke scripts with the current Python.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON results.")
    parser.add_argument("--stop-on-fail", action="store_true", help="Stop after the first failing smoke script.")
    parser.add_argument("--skip-registration", action="store_true", help="Skip the bounded registration smoke check.")
    parser.add_argument("--skip-random-transform", action="store_true", help="Pass --skip-random-transform to the learning/deeplearn smoke script.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    results: list[dict[str, Any]] = []

    for rel_script in SMOKE_SCRIPTS:
        if args.skip_registration and "registration-transforms" in rel_script:
            results.append({"script": rel_script, "status": "SKIP"})
            continue
        script = root / rel_script
        command = [sys.executable, str(script)]
        if args.skip_random_transform and rel_script.endswith("antspy_deeplearn_smoke.py"):
            command.append("--skip-random-transform")
        proc = subprocess.run(command, text=True, capture_output=True, timeout=120)
        result = {
            "script": rel_script,
            "status": "PASS" if proc.returncode == 0 else "FAIL",
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip().splitlines()[-20:],
            "stderr": proc.stderr.strip().splitlines()[-20:],
        }
        results.append(result)
        if proc.returncode != 0 and args.stop_on_fail:
            break

    ok = all(row["status"] in {"PASS", "SKIP"} for row in results)
    payload = {"ok": ok, "python": sys.version.split()[0], "results": results}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for row in results:
            print(f"{row['status']}: {row['script']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
