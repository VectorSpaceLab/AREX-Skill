#!/usr/bin/env python3
"""Compare two Helios YAML config files.

Adapted from the repo's config-comparison helper, with a CLI and no repo-local
path assumptions.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


def compare_dict(a: Any, b: Any, path: str, missing: list[str], different: list[str]) -> None:
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            child = f"{path}.{key}" if path else str(key)
            if key not in b:
                missing.append(f"[{child}] only in first: {a[key]!r}")
            elif key not in a:
                missing.append(f"[{child}] only in second: {b[key]!r}")
            else:
                compare_dict(a[key], b[key], child, missing, different)
        return

    if a != b:
        different.append(f"[{path}]\n  first:  {a!r}\n  second: {b!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two Helios YAML configs")
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    args = parser.parse_args()

    first = yaml.safe_load(args.first.read_text())
    second = yaml.safe_load(args.second.read_text())

    missing: list[str] = []
    different: list[str] = []
    compare_dict(first, second, "", missing, different)

    print("Missing keys")
    print("============")
    print("None" if not missing else "\n".join(missing))
    print("\nDifferent values")
    print("================")
    print("None" if not different else "\n".join(different))
    print(f"\nTotal: {len(missing)} missing, {len(different)} different")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
