#!/usr/bin/env python3
"""Print safe zi2zi smoke-check commands and optionally validate a checkout tree.

This helper does not execute zi2zi training or inference. It produces a concise
plan for parser checks, data-preparation fixture checks, and artifact
validation that a future agent can run after confirming the user's environment.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

REQUIRED_FILES = [
    "font2img.py",
    "package.py",
    "train.py",
    "infer.py",
    "export.py",
    "model/unet.py",
    "model/dataset.py",
    "model/ops.py",
    "model/utils.py",
    "charset/cjk.json",
]

HELP_COMMANDS = [
    "python font2img.py --help",
    "python package.py --help",
    "python train.py --help",
    "python infer.py --help",
    "python export.py --help",
]


def inspect_tree(repo_root: Path) -> Dict[str, object]:
    return {
        "repo_root": str(repo_root),
        "required_files": [
            {"path": path, "exists": (repo_root / path).exists()} for path in REQUIRED_FILES
        ],
        "suggested_help_commands": HELP_COMMANDS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan safe zi2zi smoke checks")
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Optional zi2zi checkout to inspect for expected script/source files.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of Markdown.",
    )
    args = parser.parse_args()

    if args.repo_root:
        report = inspect_tree(args.repo_root.resolve())
    else:
        report = {"required_files": REQUIRED_FILES, "suggested_help_commands": HELP_COMMANDS}

    report["notes"] = [
        "Run original zi2zi scripts in a Python 2.7 + TensorFlow 1.x environment.",
        "Parser --help checks are safe; full training and checkpoint inference need explicit data/checkpoint and runtime approval.",
        "Use the data-preparation sub-skill to create a tiny custom-charset render/package fixture.",
    ]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print("# zi2zi smoke-check plan\n")
    if args.repo_root:
        print(f"Checkout inspected: `{report['repo_root']}`\n")
        print("## Expected files")
        for item in report["required_files"]:  # type: ignore[index]
            mark = "OK" if item["exists"] else "MISSING"
            print(f"- {mark}: `{item['path']}`")
        print()
    else:
        print("Provide `--repo-root` to check whether a checkout has expected files.\n")

    print("## Safe parser checks")
    for command in HELP_COMMANDS:
        print(f"- `{command}`")
    print("\n## Notes")
    for note in report["notes"]:  # type: ignore[index]
        print(f"- {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
