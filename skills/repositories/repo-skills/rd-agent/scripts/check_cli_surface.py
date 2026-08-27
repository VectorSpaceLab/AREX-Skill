#!/usr/bin/env python3
"""Run deterministic, low-cost RD-Agent import and CLI surface checks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Sequence


COMMANDS: tuple[tuple[str, ...], ...] = (
    ("rdagent", "--help"),
    ("rdagent", "health_check", "--no-check-env", "--no-check-docker"),
    ("rdagent", "data_science", "--help"),
    ("rdagent", "fin_quant", "--help"),
    ("rdagent", "fin_factor_report", "--help"),
    ("rdagent", "llm_finetune", "--help"),
    ("rdagent", "general_model", "--help"),
    ("rdagent", "ui", "--help"),
    ("rdagent", "server_ui", "--help"),
    ("rdagent", "ds_user_interact", "--help"),
    (sys.executable, "-m", "rdagent.scenarios.rl.autorl_bench.run", "--help"),
)


def run(command: Sequence[str], timeout: float) -> dict[str, object]:
    try:
        proc = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return {"command": list(command), "status": "missing", "error": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "command": list(command),
            "status": "timeout",
            "stdout": (exc.stdout or "")[-2000:],
            "stderr": (exc.stderr or "")[-2000:],
        }
    return {
        "command": list(command),
        "status": "pass" if proc.returncode == 0 else "fail",
        "returncode": proc.returncode,
        "stdout": proc.stdout[-2000:],
        "stderr": proc.stderr[-2000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a readable summary")
    args = parser.parse_args()
    results = [run(command, args.timeout) for command in COMMANDS]
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            print(f"{result['status']:>7}  {' '.join(result['command'])}")
            if result.get("error"):
                print(f"         {result['error']}")
    return 0 if all(result["status"] == "pass" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
