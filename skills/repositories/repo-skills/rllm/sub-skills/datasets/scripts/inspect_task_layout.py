#!/usr/bin/env python3
"""Read-only inspector for local rLLM benchmark/task layouts."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

DATA_EXTS = {".json", ".jsonl", ".csv", ".parquet", ".arrow"}


def load_toml(path: Path):
    try:
        return tomllib.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        return {"_error": f"{type(exc).__name__}: {exc}"}


def inspect(root: Path, max_tasks: int) -> dict:
    root = root.resolve()
    report = {"path": str(root), "exists": root.exists(), "is_dir": root.is_dir()}
    if not root.exists() or not root.is_dir():
        return report
    dataset_toml = root / "dataset.toml"
    report["dataset_toml"] = load_toml(dataset_toml) if dataset_toml.exists() else None
    report["data_files"] = [p.name for p in sorted(root.iterdir()) if p.is_file() and p.suffix.lower() in DATA_EXTS]
    task_dirs = [p for p in sorted(root.iterdir()) if p.is_dir() and (p / "task.toml").exists()]
    report["task_dir_count"] = len(task_dirs)
    report["task_dirs_sample"] = []
    for p in task_dirs[:max_tasks]:
        item = {
            "name": p.name,
            "task_toml": load_toml(p / "task.toml"),
            "has_tests": (p / "tests").exists(),
            "has_environment": (p / "environment").exists(),
        }
        report["task_dirs_sample"].append(item)
    report["shared_tests"] = (root / "tests").exists()
    report["shared_environment"] = (root / "environment").exists()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Local benchmark/dataset directory to inspect")
    parser.add_argument("--max-tasks", type=int, default=5, help="Maximum task directories to summarize")
    args = parser.parse_args()
    print(json.dumps(inspect(args.path, args.max_tasks), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
