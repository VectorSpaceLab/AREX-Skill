#!/usr/bin/env python3
"""Safely inspect TaskingAI plugin bundle schemas.

This helper performs static filesystem inspection only. It does not import the
TaskingAI service, read environment credentials, contact networks, or execute
plugin handlers.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency path
    yaml = None

VALID_ID = re.compile(r"^[a-z0-9][a-z0-9_]*$")
STORAGE_HELPER_MARKERS = (
    "save_base64_image_to_s3_or_local",
    "save_url_image_to_s3_or_local",
)


def rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def load_yaml(path: Path, warnings: List[str]) -> Dict[str, Any]:
    if yaml is None:
        warnings.append("PyYAML is not installed; schema contents were not parsed")
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        if not isinstance(data, dict):
            warnings.append(f"{path.name}: parsed YAML is not a mapping")
            return {}
        return data
    except Exception as exc:
        warnings.append(f"Could not parse {path.name}: {exc}")
        return {}


def inspect(repo_root: Path) -> Dict[str, Any]:
    repo_root = repo_root.resolve()
    plugin_root = repo_root / "plugin"
    bundles_root = plugin_root / "bundles"
    warnings: List[str] = []

    if not bundles_root.is_dir():
        raise SystemExit(f"No plugin/bundles directory found under the supplied repo root")

    bundles: List[Dict[str, Any]] = []
    plugin_count = 0
    no_credential_bundles: List[str] = []
    credential_bundles: Dict[str, List[str]] = {}
    parameter_types: Dict[str, int] = {}
    output_types: Dict[str, int] = {}
    storage_plugins: List[str] = []

    for bundle_dir in sorted(p for p in bundles_root.iterdir() if p.is_dir()):
        bundle_id = bundle_dir.name
        if bundle_id.startswith("template") or not VALID_ID.match(bundle_id):
            continue

        bundle_schema = bundle_dir / "resources" / "bundle_schema.yml"
        plugins_root = bundle_dir / "plugins"
        if not bundle_schema.is_file():
            warnings.append(f"Missing bundle schema for {bundle_id}")
            continue
        if not plugins_root.is_dir():
            warnings.append(f"Missing plugins directory for {bundle_id}")
            continue

        bundle_data = load_yaml(bundle_schema, warnings)
        credentials_schema = bundle_data.get("credentials_schema") or {}
        if not isinstance(credentials_schema, dict):
            warnings.append(f"Invalid credentials_schema for {bundle_id}; expected mapping")
            credentials_schema = {}
        credential_names = sorted(credentials_schema.keys())
        if credential_names:
            credential_bundles[bundle_id] = credential_names
        else:
            no_credential_bundles.append(bundle_id)

        plugin_entries: List[Dict[str, Any]] = []
        for plugin_dir in sorted(p for p in plugins_root.iterdir() if p.is_dir()):
            plugin_id = plugin_dir.name
            if not VALID_ID.match(plugin_id):
                continue
            plugin_schema = plugin_dir / "plugin_schema.yml"
            if not plugin_schema.is_file():
                warnings.append(f"Missing plugin schema for {bundle_id}/{plugin_id}")
                continue

            plugin_data = load_yaml(plugin_schema, warnings)
            input_schema = plugin_data.get("input_schema") or {}
            output_schema = plugin_data.get("output_schema") or {}
            if isinstance(input_schema, dict):
                for schema in input_schema.values():
                    if isinstance(schema, dict):
                        type_name = str(schema.get("type", "unknown"))
                        parameter_types[type_name] = parameter_types.get(type_name, 0) + 1
            if isinstance(output_schema, dict):
                for schema in output_schema.values():
                    if isinstance(schema, dict):
                        type_name = str(schema.get("type", "unknown"))
                        output_types[type_name] = output_types.get(type_name, 0) + 1

            plugin_py = plugin_dir / "plugin.py"
            uses_storage = False
            if plugin_py.is_file():
                try:
                    text = plugin_py.read_text(encoding="utf-8", errors="replace")
                    uses_storage = any(marker in text for marker in STORAGE_HELPER_MARKERS)
                except Exception as exc:
                    warnings.append(f"Could not inspect handler text for {bundle_id}/{plugin_id}: {exc}")
            if uses_storage:
                storage_plugins.append(f"{bundle_id}/{plugin_id}")

            plugin_entries.append(
                {
                    "plugin_id": plugin_id,
                    "schema_path": rel(plugin_schema, repo_root),
                    "input_keys": sorted(input_schema.keys()) if isinstance(input_schema, dict) else [],
                    "output_keys": sorted(output_schema.keys()) if isinstance(output_schema, dict) else [],
                    "uses_image_storage": uses_storage,
                }
            )
            plugin_count += 1

        bundles.append(
            {
                "bundle_id": bundle_id,
                "schema_path": rel(bundle_schema, repo_root),
                "credentials": credential_names,
                "plugin_count": len(plugin_entries),
                "plugins": plugin_entries,
            }
        )

    return {
        "bundle_count": len(bundles),
        "plugin_count": plugin_count,
        "schema_roots": {
            "bundles": "plugin/bundles/<bundle_id>/resources/bundle_schema.yml",
            "plugins": "plugin/bundles/<bundle_id>/plugins/<plugin_id>/plugin_schema.yml",
        },
        "no_credential_bundles": no_credential_bundles,
        "credential_bundles": credential_bundles,
        "parameter_types": dict(sorted(parameter_types.items())),
        "output_types": dict(sorted(output_types.items())),
        "image_storage_plugins": sorted(storage_plugins),
        "bundles": bundles,
        "warnings": sorted(set(warnings)),
    }


def print_text(report: Dict[str, Any]) -> None:
    print(f"Bundle count: {report['bundle_count']}")
    print(f"Plugin count: {report['plugin_count']}")
    print("Schema paths:")
    print(f"  bundles: {report['schema_roots']['bundles']}")
    print(f"  plugins: {report['schema_roots']['plugins']}")
    print()
    print("No-credential bundles:")
    print("  " + (", ".join(report["no_credential_bundles"]) or "none"))
    print()
    print("Image-storage plugins:")
    print("  " + (", ".join(report["image_storage_plugins"]) or "none"))
    print()
    print("Bundles:")
    for bundle in report["bundles"]:
        creds = ", ".join(bundle["credentials"]) if bundle["credentials"] else "none"
        print(f"- {bundle['bundle_id']} ({bundle['plugin_count']} plugins, credentials: {creds})")
        print(f"  bundle_schema: {bundle['schema_path']}")
        for plugin in bundle["plugins"]:
            storage = " storage" if plugin["uses_image_storage"] else ""
            print(f"  - {plugin['plugin_id']}{storage}: {plugin['schema_path']}")
    if report["warnings"]:
        print()
        print("Warnings:")
        for warning in report["warnings"]:
            print(f"- {warning}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Static TaskingAI plugin bundle/schema inspector")
    parser.add_argument("--repo-root", default=".", help="Path to a TaskingAI repository root")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    report = inspect(Path(args.repo_root))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
