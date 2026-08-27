#!/usr/bin/env python3
"""List SimpleDet model-family/config mappings without importing mxnet.

The helper is intentionally lightweight:
- it only uses the standard library
- it never imports model code
- it can locate the repo from --repo-root or by walking upward from CWD
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def find_repo_root(start: Path) -> Path:
    start = start.resolve()
    for candidate in (start, *start.parents):
        if (candidate / "config").is_dir() and (candidate / "models").is_dir():
            return candidate
    raise SystemExit(
        f"Could not find a SimpleDet repo root from {start}. "
        "Pass --repo-root explicitly."
    )


def family_for_config(rel_path: Path) -> str:
    parts = rel_path.parts
    if len(parts) == 1:
        stem = rel_path.stem
        return stem.split("_", 1)[0]
    return parts[0]


def collect_configs(repo_root: Path) -> Dict[str, List[str]]:
    config_dir = repo_root / "config"
    if not config_dir.is_dir():
        raise SystemExit(f"{config_dir} does not exist")

    grouped: Dict[str, List[str]] = defaultdict(list)
    for path in sorted(config_dir.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(config_dir)
        family = family_for_config(rel)
        grouped[family].append(str(rel).replace("\\", "/"))
    return dict(sorted(grouped.items(), key=lambda item: item[0].lower()))


def format_text(repo_root: Path, groups: Dict[str, List[str]], max_items: int) -> str:
    lines: List[str] = []
    lines.append(f"repo_root: {repo_root}")
    lines.append(f"families: {len(groups)}")
    for family, configs in groups.items():
        shown = configs[:max_items]
        suffix = "" if len(configs) <= max_items else f" ... (+{len(configs) - max_items} more)"
        lines.append(f"- {family} ({len(configs)})")
        for config in shown:
            lines.append(f"  - {config}")
        if suffix:
            lines.append(f"  {suffix}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List SimpleDet model-family/config mappings without importing mxnet."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Path to the SimpleDet repository root. Defaults to the first parent of CWD with config/ and models/.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=8,
        help="Maximum configs to print per family in text mode.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve() if args.repo_root else find_repo_root(Path.cwd())
    if not (repo_root / "config").is_dir() or not (repo_root / "models").is_dir():
        raise SystemExit(f"{repo_root} is not a SimpleDet repository root")

    groups = collect_configs(repo_root)

    if args.format == "json":
        print(
            json.dumps(
                {"repo_root": str(repo_root), "families": groups},
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(format_text(repo_root, groups, max(1, args.max_items)))


if __name__ == "__main__":
    main()
