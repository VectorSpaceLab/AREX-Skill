#!/usr/bin/env python3
"""Safe local smoke checks for the Hugging Face Datasets skill."""

import argparse
import shutil
import subprocess
import sys


def run_core() -> None:
    from datasets import Dataset

    dataset = Dataset.from_dict({"text": ["hello", "datasets"], "label": [0, 1]})
    mapped = dataset.map(lambda row: {"length": len(row["text"])})
    filtered = mapped.filter(lambda row: row["length"] > 5)
    assert mapped.num_rows == 2
    assert filtered.num_rows == 1
    assert "length" in mapped.column_names
    print("core Dataset/from_dict/map/filter smoke passed")


def run_cli_help() -> None:
    exe = shutil.which("datasets-cli")
    if not exe:
        print("datasets-cli not found on PATH; package import smoke can still pass", file=sys.stderr)
        return
    result = subprocess.run([exe, "--help"], check=True, text=True, capture_output=True, timeout=20)
    if "env" not in result.stdout or "test" not in result.stdout:
        raise RuntimeError("datasets-cli help did not list expected commands")
    print("datasets-cli --help smoke passed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run safe local Datasets smoke checks.")
    parser.add_argument("--skip-cli", action="store_true", help="Skip datasets-cli --help check.")
    args = parser.parse_args()
    run_core()
    if not args.skip_cli:
        run_cli_help()


if __name__ == "__main__":
    main()
