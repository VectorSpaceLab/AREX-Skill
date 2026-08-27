#!/usr/bin/env python3
"""Build a guarded Photo2Cartoon batch-preprocessing command.

This helper replaces ad-hoc instructions to run the source data_process.py
script. It validates the target checkout and input folder, prints the command,
and only executes it when --execute is explicitly supplied.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or execute a guarded Photo2Cartoon data preprocessing command.")
    parser.add_argument("--repo-root", required=True, type=Path, help="Target Photo2Cartoon checkout root.")
    parser.add_argument("--data-path", required=True, type=Path, help="Input folder of raw portrait photos.")
    parser.add_argument("--save-path", required=True, type=Path, help="Output folder for preprocessed white-background face crops.")
    parser.add_argument("--seg-model", type=Path, help="Optional explicit segmentation graph; default is <repo-root>/utils/seg_model_384.pb.")
    parser.add_argument("--python", default=sys.executable, help="Python executable for --execute.")
    parser.add_argument("--execute", action="store_true", help="Actually run the command. Default only prints and validates.")
    args = parser.parse_args()

    repo_root = args.repo_root.expanduser().resolve()
    data_script = repo_root / "data_process.py"
    seg_model = (args.seg_model or repo_root / "utils" / "seg_model_384.pb").expanduser()
    data_path = args.data_path.expanduser()
    save_path = args.save_path.expanduser()

    problems: List[str] = []
    warnings: List[str] = []
    if not repo_root.is_dir():
        problems.append(f"repo root is not a directory: {repo_root}")
    if not data_script.is_file():
        problems.append(f"missing source-compatible preprocessing entrypoint: {data_script}")
    if not data_path.is_dir():
        problems.append(f"input data folder is not a directory: {data_path}")
    if not seg_model.is_file():
        warnings.append(f"missing segmentation graph required for real preprocessing: {seg_model}")

    cmd = [args.python, str(data_script), "--data_path", str(data_path), "--save_path", str(save_path)]
    print("preprocess command:", " ".join(cmd))
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"- {warning}")
    if problems:
        print("problems:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    if not args.execute:
        print("dry-run only; add --execute after dependencies and assets are verified")
        return 0 if not warnings else 2

    if warnings:
        print("refusing to execute until warnings are resolved")
        return 2
    save_path.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(cmd, cwd=str(repo_root), check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
