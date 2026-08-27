#!/usr/bin/env python3
"""Validate the Unstract test-rig manifests without running tests.

This script reads `tests/groups.yaml` and `tests/critical_paths.yaml` from a
checkout of the repository (or from `--repo-root`) and prints a compact summary
that is safe to run in a prepared inspection environment.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path}: expected a mapping at top level")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Unstract test-rig manifests")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root that contains tests/groups.yaml and tests/critical_paths.yaml.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    groups_path = repo_root / "tests" / "groups.yaml"
    paths_path = repo_root / "tests" / "critical_paths.yaml"

    groups = _load_yaml(groups_path)
    paths = _load_yaml(paths_path)
    manifest = groups.get("groups", {})
    critical_paths = paths.get("paths", [])

    if not isinstance(manifest, dict):
        raise TypeError("groups.yaml: expected groups to be a mapping")
    if not isinstance(critical_paths, list):
        raise TypeError("critical_paths.yaml: expected paths to be a list")

    print(f"repo_root: {repo_root}")
    print(f"groups: {len(manifest)}")
    print(f"critical_paths: {len(critical_paths)}")

    tiers: dict[str, int] = {}
    for name, group in manifest.items():
        if not isinstance(group, dict):
            raise TypeError(f"groups.yaml: group {name!r} must be a mapping")
        tier = str(group.get("tier", "unknown"))
        tiers[tier] = tiers.get(tier, 0) + 1
    print("tiers:")
    for tier, count in sorted(tiers.items()):
        print(f"  - {tier}: {count}")

    known_groups = set(manifest)
    missing_refs: list[str] = []
    for entry in critical_paths:
        if not isinstance(entry, dict):
            raise TypeError("critical_paths.yaml: each entry must be a mapping")
        path_id = entry.get("id", "<unknown>")
        covered_by = entry.get("covered_by", [])
        if not isinstance(covered_by, list):
            raise TypeError(f"critical path {path_id!r}: covered_by must be a list")
        for group_name in covered_by:
            if group_name not in known_groups:
                missing_refs.append(f"{path_id}: {group_name}")
    if missing_refs:
        raise ValueError("unknown groups referenced by critical paths: " + ", ".join(missing_refs))

    empty = [entry.get("id", "<unknown>") for entry in critical_paths if not entry.get("covered_by")]
    if empty:
        print("gaps:")
        for item in empty:
            print(f"  - {item}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
