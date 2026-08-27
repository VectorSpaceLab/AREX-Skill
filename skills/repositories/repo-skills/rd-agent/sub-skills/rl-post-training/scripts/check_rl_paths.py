#!/usr/bin/env python3
"""Inspect RL resource roots without downloading models or benchmark data."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file-root", default=os.environ.get("AUTORL_FILE_PATH", "git_ignore_folder/rl_files"))
    parser.add_argument("--smith-root", default=os.environ.get("SMITH_BENCH_DIR", ""))
    args = parser.parse_args()
    roots = {"autorl_file_root": Path(args.file_root).expanduser(), "smith_bench_root": Path(args.smith_root).expanduser() if args.smith_root else None}
    result = {}
    for name, path in roots.items():
        result[name] = None if path is None else {"path": str(path), "exists": path.exists(), "is_directory": path.is_dir()}
    print(json.dumps(result, indent=2))
    return 0 if result["autorl_file_root"]["is_directory"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
