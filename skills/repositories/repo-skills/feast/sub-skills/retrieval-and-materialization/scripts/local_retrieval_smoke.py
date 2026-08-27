#!/usr/bin/env python3
"""Safe Feast local retrieval checker and command planner.

This script does not mutate a feature repo by default. It verifies that Feast can
be imported, optionally inspects a local feature repo config, and prints suggested
commands for apply, historical retrieval, materialization, and online retrieval.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_START = "2025-01-01T00:00:00"
DEFAULT_END = "2025-01-02T00:00:00"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check a local Feast repo safely and print retrieval/materialization commands.",
    )
    parser.add_argument(
        "--repo-path",
        default=".",
        help="Path to a Feast feature repository containing feature_store.yaml.",
    )
    parser.add_argument(
        "--feature-ref",
        action="append",
        default=[],
        help="Feature ref to include in printed examples, e.g. driver_hourly_stats:conv_rate. Repeatable.",
    )
    parser.add_argument(
        "--entity-row",
        default="{}",
        help='JSON object for an online entity row example, e.g. \'{"driver_id": 1001}\'.',
    )
    parser.add_argument(
        "--start-date",
        default=DEFAULT_START,
        help="Start timestamp to print for materialization commands.",
    )
    parser.add_argument(
        "--end-date",
        default=DEFAULT_END,
        help="End timestamp to print for materialization commands.",
    )
    parser.add_argument(
        "--run-import-check",
        action="store_true",
        help="Instantiate feast.FeatureStore(repo_path=...) after import and config checks.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable summary instead of text.",
    )
    return parser.parse_args()


def import_feast() -> tuple[Any | None, str | None]:
    try:
        feast = importlib.import_module("feast")
    except Exception as exc:  # pragma: no cover - message depends on environment
        return None, f"Unable to import feast: {exc}"
    return feast, None


def load_entity_row(raw: str) -> tuple[dict[str, Any], str | None]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {}, f"--entity-row is not valid JSON: {exc}"
    if not isinstance(parsed, dict):
        return {}, "--entity-row must decode to a JSON object"
    return parsed, None


def inspect_repo(repo_path: Path) -> dict[str, Any]:
    config_path = repo_path / "feature_store.yaml"
    data_dir = repo_path / "data"
    return {
        "repo_path": str(repo_path),
        "repo_exists": repo_path.exists(),
        "feature_store_yaml": str(config_path),
        "feature_store_yaml_exists": config_path.exists(),
        "data_dir_exists": data_dir.exists(),
        "registry_candidates": [
            str(path) for path in [data_dir / "registry.db", repo_path / "registry.db"] if path.exists()
        ],
        "online_store_candidates": [
            str(path)
            for path in [data_dir / "online_store.db", repo_path / "online_store.db"]
            if path.exists()
        ],
    }


def try_feature_store(feast: Any, repo_path: Path) -> tuple[str | None, str | None]:
    try:
        store = feast.FeatureStore(repo_path=str(repo_path))
        project = getattr(store, "project", None)
    except Exception as exc:  # pragma: no cover - depends on user repo
        return None, f"FeatureStore(repo_path=...) failed: {exc}"
    return str(project), None


def build_commands(repo_path: Path, features: list[str], entity_row: dict[str, Any], start: str, end: str) -> list[str]:
    feature_list = features or ["<feature_view>:<feature>"]
    entity_repr = repr(entity_row or {"<join_key>": "<value>"})
    quoted_features = ", ".join(repr(feature) for feature in feature_list)
    return [
        f"cd {repo_path}",
        "feast apply",
        f"feast materialize {start} {end}",
        f"feast materialize-incremental {end}",
        "python - <<'PY'\n"
        "from feast import FeatureStore\n"
        "store = FeatureStore(repo_path='.')\n"
        f"features = [{quoted_features}]\n"
        f"entity_rows = [{entity_repr}]\n"
        "print(store.get_online_features(features=features, entity_rows=entity_rows).to_dict())\n"
        "PY",
    ]


def print_text(summary: dict[str, Any]) -> None:
    print("Feast local retrieval smoke check")
    print(f"- Feast import: {'ok' if summary['feast_import_ok'] else 'failed'}")
    if summary.get("feast_version"):
        print(f"- Feast version: {summary['feast_version']}")
    if summary.get("errors"):
        for error in summary["errors"]:
            print(f"- Error: {error}")
    repo = summary["repo"]
    print(f"- Repo path: {repo['repo_path']}")
    print(f"- feature_store.yaml: {'found' if repo['feature_store_yaml_exists'] else 'missing'}")
    print(f"- data directory: {'found' if repo['data_dir_exists'] else 'missing'}")
    if repo["registry_candidates"]:
        print(f"- Registry candidates: {', '.join(repo['registry_candidates'])}")
    if repo["online_store_candidates"]:
        print(f"- Online store candidates: {', '.join(repo['online_store_candidates'])}")
    if summary.get("feature_store_project"):
        print(f"- FeatureStore project: {summary['feature_store_project']}")
    print("\nSuggested non-destructive next checks:")
    print("- feast --help")
    print("- feast materialize --help")
    print("- feast get-online-features --help")
    print("\nSuggested local workflow commands; review before running:")
    for command in summary["suggested_commands"]:
        print(command)
        if command.startswith("python -"):
            print()


def main() -> int:
    args = parse_args()
    repo_path = Path(args.repo_path).expanduser().resolve()
    entity_row, entity_error = load_entity_row(args.entity_row)
    feast, import_error = import_feast()
    repo_summary = inspect_repo(repo_path)

    errors = []
    if import_error:
        errors.append(import_error)
    if entity_error:
        errors.append(entity_error)
    if not repo_summary["repo_exists"]:
        errors.append("Repo path does not exist")
    if not repo_summary["feature_store_yaml_exists"]:
        errors.append("feature_store.yaml was not found; pass --repo-path for an applied Feast feature repo")

    project = None
    if args.run_import_check and feast is not None and repo_summary["feature_store_yaml_exists"]:
        project, store_error = try_feature_store(feast, repo_path)
        if store_error:
            errors.append(store_error)

    summary = {
        "feast_import_ok": feast is not None,
        "feast_version": getattr(feast, "__version__", None) if feast is not None else None,
        "repo": repo_summary,
        "feature_refs": args.feature_ref,
        "entity_row": entity_row,
        "feature_store_project": project,
        "suggested_commands": build_commands(
            repo_path,
            args.feature_ref,
            entity_row,
            args.start_date,
            args.end_date,
        ),
        "errors": errors,
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary)

    return 1 if import_error or entity_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
