#!/usr/bin/env python3
"""Run all bundled numpy-ml repo-skill smoke helpers with the current Python."""
import argparse
import json
import subprocess
import sys
from pathlib import Path


SCRIPT_RELATIVE_PATHS = [
    "sub-skills/supervised-and-tabular-models/scripts/tabular_smoke.py",
    "sub-skills/probabilistic-and-sequence-models/scripts/probabilistic_sequence_smoke.py",
    "sub-skills/neural-network-components/scripts/neural_component_smoke.py",
    "sub-skills/preprocessing-and-utilities/scripts/preprocessing_utils_smoke.py",
    "sub-skills/bandits-and-reinforcement-learning/scripts/bandit_rl_smoke.py",
]


def run_one(root, rel, timeout):
    path = root / rel
    cmd = [sys.executable, str(path), "--json"]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    parsed = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except Exception:
            parsed = proc.stdout.strip()
    return {
        "script": rel,
        "exit_code": proc.returncode,
        "stdout": parsed,
        "stderr_tail": proc.stderr.strip()[-1000:],
        "status": "passed" if proc.returncode == 0 else "failed",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=30.0, help="per-script timeout in seconds")
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    results = [run_one(root, rel, args.timeout) for rel in SCRIPT_RELATIVE_PATHS]
    report = {"status": "passed" if all(r["exit_code"] == 0 for r in results) else "failed", "results": results}
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
