#!/usr/bin/env python3
"""Read-only inspector for installed DataDesigner plugin entry points.

The inspector intentionally uses only standard-library metadata APIs. It never
imports ``data_designer``, never calls ``EntryPoint.load()``, never contacts a
plugin catalog, and never invokes uv/pip. Use it when you need to confirm what
``data_designer.plugins`` entry points are visible to the current interpreter.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from collections import Counter
from importlib import metadata
from typing import Any

ENTRY_POINT_GROUP = "data_designer.plugins"
DATA_DESIGNER_DISTRIBUTIONS = (
    "data-designer",
    "data-designer-config",
    "data-designer-engine",
)


def _entry_points_for_group(group: str) -> list[metadata.EntryPoint]:
    try:
        return list(metadata.entry_points(group=group))
    except TypeError:  # pragma: no cover - compatibility with older importlib.metadata APIs.
        return list(metadata.entry_points().select(group=group))


def _distribution_version(distribution_name: str) -> str | None:
    try:
        return metadata.version(distribution_name)
    except metadata.PackageNotFoundError:
        return None


def _entry_point_distribution(entry_point: metadata.EntryPoint) -> tuple[str | None, str | None]:
    distribution = getattr(entry_point, "dist", None)
    if distribution is None:
        return None, None

    package_name = None
    distribution_metadata = getattr(distribution, "metadata", None)
    if hasattr(distribution_metadata, "get"):
        raw_name = distribution_metadata.get("Name")
        if isinstance(raw_name, str) and raw_name:
            package_name = raw_name
    if package_name is None:
        raw_name = getattr(distribution, "name", None)
        if isinstance(raw_name, str) and raw_name:
            package_name = raw_name

    raw_version = getattr(distribution, "version", None)
    package_version = raw_version if isinstance(raw_version, str) and raw_version else None
    return package_name, package_version


def _build_entry_point_records() -> list[dict[str, str | None]]:
    records: list[dict[str, str | None]] = []
    for entry_point in _entry_points_for_group(ENTRY_POINT_GROUP):
        package_name, package_version = _entry_point_distribution(entry_point)
        records.append(
            {
                "name": entry_point.name,
                "value": entry_point.value,
                "group": entry_point.group,
                "package_name": package_name,
                "package_version": package_version,
            }
        )
    return sorted(
        records,
        key=lambda item: (
            item["name"] or "",
            item["package_name"] or "",
            item["value"] or "",
        ),
    )


def _duplicate_values(records: list[dict[str, str | None]], key: str) -> dict[str, int]:
    counts = Counter(str(record[key]) for record in records if record.get(key))
    return {value: count for value, count in sorted(counts.items()) if count > 1}


def _build_warnings(
    *,
    plugins_disabled: bool,
    distribution_versions: dict[str, str | None],
    entry_points: list[dict[str, str | None]],
) -> list[str]:
    warnings: list[str] = []
    if plugins_disabled:
        warnings.append(
            "DISABLE_DATA_DESIGNER_PLUGINS=true; DataDesigner PluginRegistry will skip entry-point discovery."
        )

    missing_distributions = [name for name, version in distribution_versions.items() if version is None]
    if missing_distributions:
        warnings.append(
            "Current interpreter is missing DataDesigner distribution metadata for: "
            + ", ".join(missing_distributions)
        )

    present_versions = {version for version in distribution_versions.values() if version is not None}
    if len(present_versions) > 1:
        warnings.append(
            "Installed DataDesigner package family versions differ: "
            + ", ".join(f"{name}={version}" for name, version in distribution_versions.items())
        )

    duplicate_entry_names = _duplicate_values(entry_points, "name")
    if duplicate_entry_names:
        warnings.append(
            "Multiple data_designer.plugins entry points share the same entry-point name: "
            + ", ".join(f"{name} ({count})" for name, count in duplicate_entry_names.items())
        )

    duplicate_values = _duplicate_values(entry_points, "value")
    if duplicate_values:
        warnings.append(
            "Multiple data_designer.plugins entry points share the same import target: "
            + ", ".join(f"{value} ({count})" for value, count in duplicate_values.items())
        )

    suspicious_values = [record for record in entry_points if ":" not in str(record.get("value") or "")]
    if suspicious_values:
        warnings.append(
            "Some entry-point values do not use the usual 'module:object' form: "
            + ", ".join(str(record["name"]) for record in suspicious_values)
        )

    return warnings


def build_report() -> dict[str, Any]:
    disabled_env_value = os.environ.get("DISABLE_DATA_DESIGNER_PLUGINS")
    plugins_disabled = (disabled_env_value or "false").lower() == "true"
    distribution_versions = {
        distribution_name: _distribution_version(distribution_name)
        for distribution_name in DATA_DESIGNER_DISTRIBUTIONS
    }
    entry_points = _build_entry_point_records()
    return {
        "inspector": {
            "mode": "metadata-only",
            "entry_point_group": ENTRY_POINT_GROUP,
            "loads_entry_points": False,
            "mutates_environment": False,
            "uses_network": False,
            "uses_package_manager": False,
        },
        "environment": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "disable_data_designer_plugins": disabled_env_value,
            "plugins_disabled": plugins_disabled,
        },
        "data_designer_distributions": distribution_versions,
        "entry_points": entry_points,
        "warnings": _build_warnings(
            plugins_disabled=plugins_disabled,
            distribution_versions=distribution_versions,
            entry_points=entry_points,
        ),
    }


def _print_text(report: dict[str, Any]) -> None:
    env = report["environment"]
    print("DataDesigner plugin entry-point inspection")
    print("Mode: metadata-only (EntryPoint.load() is not called)")
    print(f"Python: {env['python_version']} ({env['python_executable']})")
    disabled_value = env["disable_data_designer_plugins"]
    print(f"DISABLE_DATA_DESIGNER_PLUGINS: {disabled_value if disabled_value is not None else '(unset)'}")

    print("\nDataDesigner distributions:")
    for name, version in report["data_designer_distributions"].items():
        print(f"  - {name}: {version if version is not None else '(not installed)'}")

    entry_points = report["entry_points"]
    print(f"\nEntry points in {ENTRY_POINT_GROUP!r}: {len(entry_points)}")
    if not entry_points:
        print("  (none)")
    for record in entry_points:
        package = record["package_name"] or "unknown package"
        version = f"=={record['package_version']}" if record["package_version"] else ""
        print(f"  - {record['name']} -> {record['value']} [{package}{version}]")

    warnings = report["warnings"]
    print("\nWarnings:")
    if not warnings:
        print("  (none)")
    for warning in warnings:
        print(f"  - {warning}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit a JSON report instead of text.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 2 when warnings are present. Still performs only read-only checks.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
    if args.strict and report["warnings"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
