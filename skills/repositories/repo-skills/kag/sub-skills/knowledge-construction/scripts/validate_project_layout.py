#!/usr/bin/env python3
"""Validate the local layout of a KAG project before a live build.

This helper is safe by default. It checks the config file, namespace/schema
alignment, and whether the builder layout looks complete enough to proceed.

Examples:
  python skills/disco/kag/sub-skills/knowledge-construction/scripts/validate_project_layout.py
  python skills/disco/kag/sub-skills/knowledge-construction/scripts/validate_project_layout.py ./my-project --json
  python skills/disco/kag/sub-skills/knowledge-construction/scripts/validate_project_layout.py ./my-project --strict
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


NAMESPACE_RE = re.compile(r"^[A-Z][A-Za-z0-9]{0,15}$")


def add_env_constructor() -> None:
    def _env(loader: yaml.SafeLoader, node: yaml.Node) -> Any:
        value = loader.construct_scalar(node)
        return os.getenv(value.strip())

    yaml.SafeLoader.add_constructor("!ENV", _env)


add_env_constructor()


def find_config(project_dir: Path, config_name: str = "kag_config.yaml") -> Optional[Path]:
    candidate = project_dir / config_name
    if candidate.exists():
        return candidate
    return None


def load_config(path: Path) -> Dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    return yaml.safe_load(raw) or {}


def pick_schema_path(project_dir: Path, config: Dict[str, Any], namespace: str) -> Path:
    schema_dir = config.get("schema_dir")
    schema_file = config.get("schema_file")
    project_conf = config.get("project", {}) if isinstance(config.get("project"), dict) else {}
    schema_dir = project_conf.get("schema_dir", schema_dir) or "schema"
    schema_file = project_conf.get("schema_file", schema_file) or f"{namespace}.schema"
    return project_dir / schema_dir / schema_file


def find_project_namespace(config: Dict[str, Any]) -> Optional[str]:
    project_conf = config.get("project", {})
    if isinstance(project_conf, dict):
        namespace = project_conf.get("namespace")
        if namespace:
            return str(namespace)
    return None


def search_destructive_writer(node: Any, path: str = "") -> List[str]:
    hits: List[str] = []
    if isinstance(node, dict):
        node_type = str(node.get("type", "")).lower()
        delete_flag = node.get("delete")
        if node_type in {"kg", "kg_writer"} and bool(delete_flag):
            hits.append(path or "<root>")
        for key, value in node.items():
            child_path = f"{path}.{key}" if path else str(key)
            hits.extend(search_destructive_writer(value, child_path))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            hits.extend(search_destructive_writer(item, f"{path}[{index}]"))
    return hits


def summarize(project_dir: Path, config: Dict[str, Any], config_file: Path) -> Tuple[Dict[str, Any], List[str], List[str]]:
    warnings: List[str] = []
    errors: List[str] = []

    namespace = find_project_namespace(config)
    if not namespace:
        errors.append("project.namespace is missing")
        namespace = "<missing>"
    elif not NAMESPACE_RE.match(namespace):
        errors.append(f"project.namespace '{namespace}' does not match the expected capitalized alphanumeric form")

    schema_path = pick_schema_path(project_dir, config, namespace)
    if not schema_path.exists():
        errors.append(f"schema file not found: {schema_path.relative_to(project_dir) if schema_path.is_relative_to(project_dir) else schema_path}")

    builder_dir = project_dir / "builder"
    if not builder_dir.exists():
        warnings.append("builder/ directory is missing")
    elif not (builder_dir / "indexer.py").exists():
        warnings.append("builder/indexer.py is missing")

    solver_dir = project_dir / "solver"
    if not solver_dir.exists():
        warnings.append("solver/ directory is missing")

    reasoner_dir = project_dir / "reasoner"
    if not reasoner_dir.exists():
        warnings.append("reasoner/ directory is missing")

    if not (project_dir / "schema").exists() and schema_path.parent.name == "schema":
        warnings.append("schema/ directory is missing")

    project_conf = config.get("project", {}) if isinstance(config.get("project"), dict) else {}
    project_summary = {
        "namespace": namespace,
        "id": project_conf.get("id"),
        "host_addr": project_conf.get("host_addr"),
        "language": project_conf.get("language"),
        "biz_scene": project_conf.get("biz_scene"),
    }

    destructive_hits = search_destructive_writer(config.get("kag_builder_pipeline", {}), "kag_builder_pipeline")
    if destructive_hits:
        warnings.append("destructive KG writer mode detected at: " + ", ".join(destructive_hits))

    summary = {
        "project_dir": str(project_dir),
        "config_file": str(config_file),
        "project": project_summary,
        "schema_file": str(schema_path),
        "directories": {
            "builder": builder_dir.exists(),
            "solver": solver_dir.exists(),
            "reasoner": reasoner_dir.exists(),
            "schema": (project_dir / "schema").exists(),
        },
        "warnings": warnings,
        "errors": errors,
    }
    return summary, warnings, errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a KAG project layout.")
    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Path to the project directory. Defaults to the current directory.",
    )
    parser.add_argument("--config", help="Config file name or path. Defaults to kag_config.yaml in the project directory.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.exists():
        print(f"Project directory does not exist: {project_dir}")
        return 1

    config_name = Path(args.config).name if args.config else "kag_config.yaml"
    if args.config and Path(args.config).exists():
        config_file = Path(args.config).expanduser().resolve()
    else:
        candidate = find_config(project_dir, config_name)
        if candidate is None:
            print(f"No {config_name} found under {project_dir}")
            return 1
        config_file = candidate.resolve()

    try:
        config = load_config(config_file)
    except Exception as exc:
        print(f"Failed to parse {config_file}: {exc}")
        return 1

    summary, warnings, errors = summarize(project_dir, config, config_file)
    failed = bool(errors) or (args.strict and bool(warnings))

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"project: {summary['project_dir']}")
        print(f"config: {summary['config_file']}")
        print(f"namespace: {summary['project']['namespace']}")
        print(f"schema_file: {summary['schema_file']}")
        for name, exists in summary["directories"].items():
            print(f"{name}: {'yes' if exists else 'no'}")
        if warnings:
            print("warnings:")
            for warning in warnings:
                print(f"- {warning}")
        if errors:
            print("errors:")
            for error in errors:
                print(f"- {error}")
        if not warnings and not errors:
            print("layout looks consistent")

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
