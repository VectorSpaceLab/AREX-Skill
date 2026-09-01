#!/usr/bin/env python3
"""Check reduced recovery artifact presence before running Distiller validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = [
    "recovery/experiment_plan.md",
    "recovery/run_recovery.py",
    "recovery/recovery_result.json",
    "recovery/source_manifest.json",
    "recovery/logs/generated_data_item.json",
    "recovery/logs/training_trace.json",
    "recovery/logs/experiment_command_log.json",
    "recovery/logs/generated_skill_invocations.json",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    attempt_dir = Path(args.attempt_dir).expanduser().resolve()
    missing = [rel for rel in REQUIRED if not (attempt_dir / rel).exists()]
    result = {"ok": not missing, "attempt_dir": str(attempt_dir), "missing": missing}
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

