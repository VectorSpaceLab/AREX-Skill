#!/usr/bin/env python3
"""Safe Autodistill CLI smoke check.

Runs `autodistill --help` and validates that expected option names appear. It
can also validate an ontology JSON string. This helper never labels images,
installs plugins, downloads weights, trains models, or contacts Roboflow.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys

EXPECTED_OPTIONS = [
    "--models",
    "--base",
    "--target",
    "--model_type",
    "--ontology",
    "--epochs",
    "--output",
    "--upload-to-roboflow",
    "--project_name",
    "--project_license",
    "--dataset_format",
    "--test",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--executable",
        default="autodistill",
        help="Autodistill executable to inspect; default: autodistill on PATH.",
    )
    parser.add_argument(
        "--ontology-json",
        default=None,
        help="Optional ontology JSON string to validate without running the CLI.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Seconds to wait for --help output.",
    )
    return parser.parse_args()


def validate_ontology(raw: str) -> None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Ontology is not valid JSON: {exc}") from exc
    if not isinstance(data, dict) or not data:
        raise SystemExit("Ontology must be a non-empty JSON object mapping prompts to classes")
    bad = [key for key, value in data.items() if not isinstance(key, str) or not isinstance(value, str)]
    if bad:
        raise SystemExit("Ontology prompts and classes must be strings")
    print(f"Ontology JSON valid with {len(data)} mapping(s): {list(data.values())}")


def main() -> int:
    args = parse_args()
    executable = shutil.which(args.executable) or args.executable
    try:
        proc = subprocess.run(
            [executable, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=args.timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SystemExit(f"Could not find Autodistill executable: {args.executable}") from exc
    if proc.returncode != 0:
        raise SystemExit(f"`{args.executable} --help` failed with code {proc.returncode}: {proc.stderr.strip()}")
    missing = [option for option in EXPECTED_OPTIONS if option not in proc.stdout]
    if missing:
        raise SystemExit("Help output missing expected options: " + ", ".join(missing))
    print("Autodistill CLI help smoke passed.")
    if args.ontology_json is not None:
        validate_ontology(args.ontology_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
