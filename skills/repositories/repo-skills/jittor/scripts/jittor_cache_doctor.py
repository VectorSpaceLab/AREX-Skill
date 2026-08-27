#!/usr/bin/env python3
"""Inspect the Jittor cache layout without deleting anything.

This helper is intentionally non-destructive. It summarizes the cache root and
its common subdirectories so future agents can decide whether a cache reset is
worth considering.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict


COMMON_CATEGORIES = ["master", "default", "jt", "jtcuda", "cub", "cutt", "nccl", "dataset", "tmp", "obj_files", "gen", "checkpoints"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect the Jittor cache directory without mutating it.")
    parser.add_argument("--cache-root", default=str(Path.home() / ".cache" / "jittor"), help="Cache root to inspect (default: ~/.cache/jittor).")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args()


def summarize(cache_root: Path) -> Dict[str, object]:
    info: Dict[str, object] = {
        "cache_root": str(cache_root),
        "exists": cache_root.exists(),
        "categories": {},
    }
    categories: Dict[str, object] = {}
    if cache_root.exists():
        for name in COMMON_CATEGORIES:
            path = cache_root / name
            if path.exists():
                categories[name] = {
                    "path": str(path),
                    "kind": "dir" if path.is_dir() else "file",
                }
    info["categories"] = categories
    return info


def main() -> int:
    args = parse_args()
    cache_root = Path(args.cache_root).expanduser()
    info = summarize(cache_root)
    if args.json:
        print(json.dumps(info, sort_keys=True))
        return 0

    print(f"cache_root: {info['cache_root']}")
    print(f"exists: {info['exists']}")
    categories = info["categories"]
    if categories:
        for name, entry in sorted(categories.items()):
            print(f"{name}: {entry['path']} ({entry['kind']})")
    else:
        print("No common Jittor cache categories were found.")
    print("If you need a deletion command, use python -m jittor_utils.clean_cache help first, then choose a category intentionally.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
