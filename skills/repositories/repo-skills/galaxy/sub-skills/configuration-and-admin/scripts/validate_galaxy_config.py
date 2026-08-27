#!/usr/bin/env python3
"""Read-only Galaxy YAML configuration smoke checker."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only on minimal Python installs
    yaml = None

COMMON_GALAXY_KEYS = {
    "admin_users",
    "auth_config_file",
    "brand",
    "database_connection",
    "dependency_resolvers",
    "file_path",
    "job_config_file",
    "new_file_path",
    "object_store_config_file",
    "tool_config_file",
    "tool_data_path",
    "tool_dependency_dir",
}

COMMON_GRAVITY_KEYS = {
    "app_server",
    "celery",
    "gunicorn",
    "log_dir",
    "process_manager",
    "state_dir",
    "virtualenv",
}

PATH_KEYS = (
    "auth_config_file",
    "dependency_resolvers_config_file",
    "file_path",
    "job_config_file",
    "new_file_path",
    "object_store_config_file",
    "tool_config_file",
    "tool_data_path",
    "tool_dependency_dir",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely parse a Galaxy YAML config and report obvious top-level "
            "shape/path warnings without starting Galaxy or mutating files."
        )
    )
    parser.add_argument("--config", required=True, help="Path to galaxy.yml or another Galaxy YAML config file.")
    parser.add_argument(
        "--sample",
        help="Optional path to a Galaxy sample YAML file to parse-check alongside --config.",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Exit non-zero when warnings are found. Parsing errors are always non-zero.",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> tuple[Any, list[str]]:
    warnings: list[str] = []
    if not path.exists():
        raise ValueError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a regular file: {path}")
    if yaml is None:
        raise ValueError("PyYAML is not installed; install pyyaml or run in a Galaxy environment that provides YAML support.")
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"Cannot read {path}: {exc}") from exc
    if data is None:
        data = {}
        warnings.append("YAML document is empty; Galaxy will behave as if no app options were set.")
    return data, warnings


def section_mapping(data: dict[str, Any], section: str, warnings: list[str]) -> dict[str, Any]:
    value = data.get(section)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Top-level '{section}' section must be a mapping or null, not {type(value).__name__}.")
    return value


def analyze(path: Path, label: str) -> tuple[list[str], list[str]]:
    data, warnings = load_yaml(path)
    messages: list[str] = []
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a YAML mapping at the top level, not {type(data).__name__}.")

    galaxy = section_mapping(data, "galaxy", warnings)
    gravity = section_mapping(data, "gravity", warnings)
    top_keys = set(data)

    if "galaxy" not in data and "gravity" not in data:
        warnings.append("No top-level 'galaxy' or 'gravity' section found; Galaxy YAML normally uses at least 'galaxy:'.")

    misplaced_galaxy = sorted(COMMON_GALAXY_KEYS.intersection(top_keys))
    if misplaced_galaxy:
        warnings.append(
            "Common Galaxy app keys appear at the top level instead of under 'galaxy': "
            + ", ".join(misplaced_galaxy)
        )

    misplaced_gravity = sorted(COMMON_GRAVITY_KEYS.intersection(galaxy))
    if misplaced_gravity:
        warnings.append(
            "Common Gravity/process keys appear under 'galaxy' instead of top-level 'gravity': "
            + ", ".join(misplaced_gravity)
        )

    if path.name.endswith(".sample"):
        warnings.append("This path looks like a sample/template file; active edits usually belong in a non-sample galaxy.yml.")

    messages.append(f"{label}: parsed YAML mapping with top-level keys: {', '.join(sorted(map(str, top_keys))) or '(none)'}")
    if "galaxy" in data:
        messages.append(f"{label}: galaxy section contains {len(galaxy)} explicit option(s).")
    if "gravity" in data:
        messages.append(f"{label}: gravity section contains {len(gravity)} explicit option(s).")

    path_summaries = []
    for key in PATH_KEYS:
        if key in galaxy and galaxy[key] not in (None, ""):
            path_summaries.append(f"{key}={galaxy[key]!r}")
    if path_summaries:
        messages.append(f"{label}: path-like Galaxy options: " + "; ".join(path_summaries))

    if "dependency_resolvers" in galaxy and not isinstance(galaxy["dependency_resolvers"], list):
        warnings.append("galaxy.dependency_resolvers is present but is not a list.")
    if "admin_users" in galaxy and not isinstance(galaxy["admin_users"], (str, list, tuple)):
        warnings.append("galaxy.admin_users is present but is not a string/list-style value.")

    return messages, warnings


def main() -> int:
    args = parse_args()
    all_messages: list[str] = []
    all_warnings: list[str] = []

    checks = [(Path(args.config), "config")]
    if args.sample:
        checks.append((Path(args.sample), "sample"))

    for path, label in checks:
        try:
            messages, warnings = analyze(path, label)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        all_messages.extend(messages)
        all_warnings.extend(f"{label}: {warning}" for warning in warnings)

    for message in all_messages:
        print(f"OK: {message}")
    for warning in all_warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if all_warnings and args.strict_warnings:
        print("ERROR: warnings found and --strict-warnings was supplied.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
