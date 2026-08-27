#!/usr/bin/env python3
"""Print Observal harness registry support coverage as JSON.

This helper is read-only: it imports the shared harness registry, statically
checks server parser registration, and reports adapter/hook-spec file coverage.
It does not contact the network, import the FastAPI app, or write files.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any


REGISTRY_REL = Path("packages/observal-shared/observal_shared/harness_registry.py")
SHARED_REL = Path("packages/observal-shared")
SERVER_PARSERS_INIT = Path("observal-server/services/session_parsers/__init__.py")
INGEST_CLASSIFY = Path("observal-server/services/session_parsers/ingest_classify.py")
CLI_HARNESS_DIR = Path("observal_cli/harness")
SERVER_HARNESS_DIR = Path("observal-server/services/harness")
HOOK_SPECS_DIR = Path("observal_cli/harness_specs")
DOCTOR_FILE = Path("observal_cli/cmd_doctor.py")
LAYER_FILE = Path("observal_cli/layer.py")
SCAN_FILE = Path("observal_cli/cmd_scan.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report Observal harness registry coverage as JSON.")
    parser.add_argument(
        "--repo-root",
        default="",
        help="Path to an Observal checkout. Defaults to the nearest parent containing the shared registry.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON with indentation.")
    return parser.parse_args()


def find_repo_root(value: str) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / REGISTRY_REL).is_file():
            return candidate
    return cwd


def module_stem(harness: str) -> str:
    return harness.replace("-", "_")


def literal_dict_keys(path: Path, variable: str) -> set[str]:
    if not path.is_file():
        return set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()
    keys: set[str] = set()
    for node in ast.walk(tree):
        value: ast.AST | None = None
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == variable for target in node.targets
        ):
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == variable:
            value = node.value
        if not isinstance(value, ast.Dict):
            continue
        for key in value.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                keys.add(key.value)
    return keys


def function_names(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()
    return {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def import_registry(repo_root: Path) -> dict[str, dict[str, Any]]:
    shared_path = str(repo_root / SHARED_REL)
    if shared_path not in sys.path:
        sys.path.insert(0, shared_path)
    from observal_shared.harness_registry import HARNESS_REGISTRY  # noqa: PLC0415

    return HARNESS_REGISTRY


def sorted_capabilities(value: Any) -> list[str]:
    if isinstance(value, (set, list, tuple)):
        return sorted(str(item) for item in value)
    return []


def main() -> int:
    args = parse_args()
    repo_root = find_repo_root(args.repo_root)
    registry_path = repo_root / REGISTRY_REL
    if not registry_path.is_file():
        print(json.dumps({"ok": False, "error": f"registry not found: {REGISTRY_REL}"}), file=sys.stderr)
        return 2

    try:
        registry = import_registry(repo_root)
    except Exception as exc:  # pragma: no cover - defensive for broken checkouts
        print(json.dumps({"ok": False, "error": f"could not import harness registry: {exc}"}), file=sys.stderr)
        return 2

    read_parsers = literal_dict_keys(repo_root / SERVER_PARSERS_INIT, "_PARSERS")
    ingest_classifiers = literal_dict_keys(repo_root / INGEST_CLASSIFY, "_CLASSIFIERS")
    timestamp_extractors = literal_dict_keys(repo_root / INGEST_CLASSIFY, "_TS_EXTRACTORS")
    layer_harnesses = literal_dict_keys(repo_root / LAYER_FILE, "HARNESS_LAYER_CONFIGS")
    scan_home_dirs = literal_dict_keys(repo_root / SCAN_FILE, "_HARNESS_HOME_DIRS")
    doctor_functions = function_names(repo_root / DOCTOR_FILE)

    harness_rows: list[dict[str, Any]] = []
    for name, spec in registry.items():
        stem = module_stem(name)
        parser_id = spec.get("session_parser")
        hook_spec_path = repo_root / HOOK_SPECS_DIR / f"{stem}_hooks_spec.py"
        cli_adapter_path = repo_root / CLI_HARNESS_DIR / f"{stem}.py"
        server_adapter_path = repo_root / SERVER_HARNESS_DIR / f"{stem}.py"
        harness_rows.append(
            {
                "name": name,
                "display_name": spec.get("display_name", ""),
                "capabilities": sorted_capabilities(spec.get("capabilities")),
                "scopes": list(spec.get("scopes") or []),
                "default_scope": spec.get("default_scope", ""),
                "session_parser": parser_id,
                "parser_coverage": {
                    "read_parser": bool(parser_id and parser_id in read_parsers),
                    "ingest_classifier": bool(parser_id and parser_id in ingest_classifiers),
                    "timestamp_extractor": bool(parser_id and parser_id in timestamp_extractors),
                },
                "hook_spec": {
                    "expected_file": str(HOOK_SPECS_DIR / f"{stem}_hooks_spec.py"),
                    "available": hook_spec_path.is_file(),
                },
                "adapter_files": {
                    "cli": cli_adapter_path.is_file(),
                    "server": server_adapter_path.is_file(),
                },
                "doctor_functions": {
                    "check": f"_check_{stem}" in doctor_functions,
                    "patch": f"_patch_{stem}" in doctor_functions,
                    "cleanup": f"_cleanup_{stem}" in doctor_functions,
                },
                "layer_config": name in layer_harnesses,
                "scan_home_dir_label": name in scan_home_dirs,
                "mcp_servers_key": spec.get("mcp_servers_key", ""),
                "hook_type": spec.get("hook_type", ""),
                "model_catalog_file": spec.get("model_catalog_file", ""),
                "supported_model_count": len(spec.get("supported_models") or []),
            }
        )

    def missing(predicate_key: str, nested: str | None = None) -> list[str]:
        result: list[str] = []
        for row in harness_rows:
            value = row[predicate_key] if nested is None else row[predicate_key][nested]
            if not value:
                result.append(row["name"])
        return result

    summary = {
        "missing_read_parsers": missing("parser_coverage", "read_parser"),
        "missing_ingest_classifiers": missing("parser_coverage", "ingest_classifier"),
        "missing_timestamp_extractors": missing("parser_coverage", "timestamp_extractor"),
        "missing_hook_specs": missing("hook_spec", "available"),
        "missing_cli_adapters": missing("adapter_files", "cli"),
        "missing_server_adapters": missing("adapter_files", "server"),
        "missing_doctor_patch": missing("doctor_functions", "patch"),
        "missing_doctor_cleanup": missing("doctor_functions", "cleanup"),
        "missing_layer_config": missing("layer_config"),
        "missing_scan_home_dir_label": missing("scan_home_dir_label"),
    }

    payload = {
        "ok": not any(
            summary[key]
            for key in (
                "missing_read_parsers",
                "missing_ingest_classifiers",
                "missing_timestamp_extractors",
                "missing_cli_adapters",
                "missing_server_adapters",
            )
        ),
        "registry_count": len(registry),
        "parser_ids": {
            "read_parsers": sorted(read_parsers),
            "ingest_classifiers": sorted(ingest_classifiers),
            "timestamp_extractors": sorted(timestamp_extractors),
        },
        "summary": summary,
        "harnesses": harness_rows,
    }
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
