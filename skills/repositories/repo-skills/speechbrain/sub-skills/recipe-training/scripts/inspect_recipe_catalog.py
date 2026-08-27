#!/usr/bin/env python3
"""Inspect a SpeechBrain tests/recipes CSV and print safe debug commands.

This helper reads catalog metadata only; it does not run training or data prep.
"""

from __future__ import annotations

import argparse
import csv
import json
import shlex
from pathlib import Path


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=",", skipinitialspace=True))


def build_command(row: dict, device: str | None = None) -> list[str]:
    script = row.get("Script_file", "").strip()
    hparam = row.get("Hparam_file", "").strip()
    flags = row.get("test_debug_flags", "").strip()
    if not script or not hparam:
        raise ValueError("Row is missing Script_file or Hparam_file")
    cmd = ["python", script, hparam]
    if flags:
        cmd.extend(shlex.split(flags))
    if device:
        cmd.extend(["--device", device])
    return cmd


def summarize(row: dict, idx: int, device: str | None) -> dict:
    command = build_command(row, device)
    return {
        "row": idx,
        "task": row.get("Task", ""),
        "dataset": row.get("Dataset", ""),
        "script": row.get("Script_file", ""),
        "hparams": row.get("Hparam_file", ""),
        "data_prep": row.get("Data_prep_file", ""),
        "readme": row.get("Readme_file", ""),
        "debug_flags": row.get("test_debug_flags", ""),
        "debug_checks": row.get("test_debug_checks", ""),
        "has_result_url": bool(row.get("Result_url", "").strip()),
        "has_hf_repo": bool(row.get("HF_repo", "").strip()),
        "command": command,
        "shell_command": " ".join(shlex.quote(part) for part in command),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path, help="Path to a tests/recipes/*.csv file")
    parser.add_argument("--row", type=int, help="1-based data row to inspect (header excluded)")
    parser.add_argument("--task", help="Filter rows by exact Task value")
    parser.add_argument("--dataset", help="Filter rows by exact Dataset value")
    parser.add_argument("--device", help="Append --device VALUE to printed command")
    parser.add_argument("--print-command", action="store_true", help="Print only the shell command for a selected row")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    args = parser.parse_args()

    rows = read_rows(args.csv)
    indexed = list(enumerate(rows, start=1))
    if args.task:
        indexed = [(i, r) for i, r in indexed if r.get("Task") == args.task]
    if args.dataset:
        indexed = [(i, r) for i, r in indexed if r.get("Dataset") == args.dataset]
    if args.row is not None:
        indexed = [(i, r) for i, r in indexed if i == args.row]
    if not indexed:
        raise SystemExit("No matching rows found")

    summaries = [summarize(row, idx, args.device) for idx, row in indexed]
    if args.print_command:
        if len(summaries) != 1:
            raise SystemExit("--print-command requires exactly one matching row")
        print(summaries[0]["shell_command"])
    elif args.json:
        print(json.dumps(summaries, indent=2, sort_keys=True))
    else:
        for item in summaries:
            print(f"#{item['row']} {item['dataset']} {item['task']}")
            print(f"  script: {item['script']}")
            print(f"  hparams: {item['hparams']}")
            print(f"  command: {item['shell_command']}")
            if item["debug_checks"]:
                print(f"  checks: {item['debug_checks']}")


if __name__ == "__main__":
    main()
