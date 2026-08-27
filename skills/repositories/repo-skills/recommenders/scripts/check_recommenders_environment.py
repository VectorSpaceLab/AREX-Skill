#!/usr/bin/env python3
"""Check a Recommenders installation and optionally run bundled smoke helpers.

This helper is safe: it imports package modules, reports optional backend
availability, and can invoke the bundled tiny smoke scripts if they are present
in the installed skill tree. It performs no installs, downloads, cloud actions,
or destructive writes.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from importlib.metadata import PackageNotFoundError, version


def run(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    return {
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a Recommenders installation and bundled smoke helpers.")
    parser.add_argument("--check-optional", action="store_true", help="Report optional framework import availability.")
    parser.add_argument("--run-bundled-smokes", action="store_true", help="Run bundled CPU smoke helpers if the skill tree is installed at the current working directory.")
    args = parser.parse_args()

    report = {"status": "ok", "checks": []}

    try:
        report["recommenders_version"] = version("recommenders")
    except PackageNotFoundError:
        report["status"] = "fail"
        report["checks"].append({"name": "distribution metadata", "status": "fail", "error": "recommenders distribution not installed"})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    try:
        import recommenders  # noqa: F401
        report["checks"].append({"name": "base import", "status": "pass"})
    except Exception as exc:
        report["status"] = "fail"
        report["checks"].append({"name": "base import", "status": "fail", "error": str(exc)})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    if args.check_optional:
        optional = {}
        for name in ["pyspark", "torch", "tensorflow", "nni", "surprise", "lightfm", "vowpalwabbit"]:
            try:
                __import__(name)
                optional[name] = "ok"
            except Exception as exc:
                optional[name] = f"missing-or-failed: {type(exc).__name__}"
        report["optional"] = optional

    if args.run_bundled_smokes:
        root = Path.cwd()
        smoke_scripts = [
            root / "sub-skills" / "data-preparation" / "scripts" / "validate_interactions.py",
            root / "sub-skills" / "evaluation" / "scripts" / "metrics_tiny_smoke.py",
            root / "sub-skills" / "modeling" / "scripts" / "sar_tiny_smoke.py",
            root / "sub-skills" / "modeling" / "scripts" / "tfidf_tiny_smoke.py",
            root / "sub-skills" / "operations-and-tuning" / "scripts" / "environment_report.py",
        ]
        smoke_results = []
        for script in smoke_scripts:
            if not script.exists():
                smoke_results.append({"script": str(script), "status": "missing"})
                continue
            if script.name == "validate_interactions.py":
                cmd = [sys.executable, str(script), "--help"]
            else:
                cmd = [sys.executable, str(script)]
            result = run(cmd)
            result["script"] = str(script)
            result["status"] = "pass" if result["exit_code"] == 0 else "fail"
            smoke_results.append(result)
            if result["status"] == "fail":
                report["status"] = "fail"
        report["bundled_smokes"] = smoke_results

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
