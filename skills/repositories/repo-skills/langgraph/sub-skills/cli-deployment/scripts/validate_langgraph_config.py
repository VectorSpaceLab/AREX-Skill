#!/usr/bin/env python3
"""Offline checks for a LangGraph `langgraph.json` file.

This helper performs safe JSON, shape, path, and optional import checks. It does
not run Docker, contact networks, start services, or require credentials.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PYTHON_VERSIONS = {"3.11", "3.12", "3.13"}
IMAGE_DISTROS = {"debian", "bookworm", "wolfi"}
PIP_INSTALLERS = {"auto", "pip", "uv"}
NODE_EXTENSIONS = {".ts", ".mts", ".cts", ".js", ".mjs", ".cjs"}
KNOWN_KEYS = {
    "$schema",
    "python_version",
    "node_version",
    "api_version",
    "base_image",
    "image_distro",
    "pip_config_file",
    "pip_installer",
    "source",
    "dependencies",
    "dockerfile_lines",
    "graphs",
    "env",
    "store",
    "auth",
    "encryption",
    "http",
    "webhooks",
    "checkpointer",
    "ui",
    "ui_config",
    "keep_pkg_tools",
    "disable_persistence",
    "_INTERNAL_docker_tag",
    "project_root",
    "package",
}


@dataclass
class Finding:
    level: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate common LangGraph CLI config issues without Docker or network access."
    )
    parser.add_argument(
        "config",
        nargs="?",
        default="langgraph.json",
        help="Path to langgraph.json (default: langgraph.json).",
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Import Python graph modules and verify target attributes exist.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as JSON instead of human-readable text.",
    )
    parser.add_argument(
        "--write-tiny-fixture",
        metavar="PATH",
        help="Write a minimal langgraph.json fixture to PATH and exit.",
    )
    return parser.parse_args()


def write_tiny_fixture(path_text: str) -> None:
    path = Path(path_text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "$schema": "https://langgra.ph/schema.json",
                "python_version": "3.11",
                "dependencies": ["."],
                "graphs": {"agent": "./agent.py:graph"},
                "env": ".env",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    agent_path = path.parent / "agent.py"
    if not agent_path.exists():
        agent_path.write_text("graph = object()\n", encoding="utf-8")
    print(f"Wrote tiny fixture: {path}")
    print(f"Wrote tiny graph module: {agent_path}")


def load_config(path: Path) -> tuple[dict[str, Any] | None, list[Finding]]:
    findings: list[Finding] = []
    if not path.exists():
        return None, [Finding("error", f"Config file does not exist: {path}")]
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [Finding("error", f"Invalid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}")]
    if not isinstance(raw, dict):
        return None, [Finding("error", "Top-level config must be a JSON object.")]
    return raw, findings


def graph_path(spec: Any) -> str | None:
    if isinstance(spec, str):
        return spec
    if isinstance(spec, dict) and isinstance(spec.get("path"), str):
        return spec["path"]
    return None


def is_node_graph(spec: str) -> bool:
    file_part = spec.split(":", 1)[0]
    return Path(file_part).suffix in NODE_EXTENSIONS


def validate_shape(config: dict[str, Any], config_path: Path) -> list[Finding]:
    findings: list[Finding] = []
    config_dir = config_path.parent

    if "$schema" in config:
        findings.append(Finding("warning", "`$schema` is harmless editor/schema metadata; current CLI validation may still warn about it as an unknown key."))

    for key in sorted(set(config) - KNOWN_KEYS):
        findings.append(Finding("warning", f"Unknown top-level key: {key}"))

    graphs = config.get("graphs")
    if not isinstance(graphs, dict) or not graphs:
        findings.append(Finding("error", "`graphs` must be a non-empty object."))
        graph_specs: list[tuple[str, str]] = []
    else:
        graph_specs = []
        for graph_id, spec in graphs.items():
            if not isinstance(graph_id, str) or not graph_id:
                findings.append(Finding("error", "Graph IDs must be non-empty strings."))
                continue
            path_spec = graph_path(spec)
            if path_spec is None:
                findings.append(Finding("error", f"Graph `{graph_id}` must be a string or object with a string `path`."))
                continue
            graph_specs.append((graph_id, path_spec))
            if ":" not in path_spec:
                findings.append(Finding("error", f"Graph `{graph_id}` path must use './file.py:attribute' format."))
            else:
                file_part, attr = path_spec.split(":", 1)
                if not file_part:
                    findings.append(Finding("error", f"Graph `{graph_id}` has an empty file path."))
                if not attr or not re.match(r"^[A-Za-z_]\w*(\.[A-Za-z_]\w*)*$", attr):
                    findings.append(Finding("error", f"Graph `{graph_id}` has an invalid attribute path: {attr!r}."))
                if file_part.startswith("."):
                    candidate = (config_dir / file_part).resolve()
                    if not candidate.exists():
                        findings.append(Finding("error", f"Graph `{graph_id}` file does not exist: {file_part}"))

    some_python = any(not is_node_graph(spec) for _, spec in graph_specs)
    some_node = any(is_node_graph(spec) for _, spec in graph_specs)
    source = config.get("source")
    source_kind = source.get("kind") if isinstance(source, dict) else None

    python_version = config.get("python_version")
    if python_version is not None:
        if not isinstance(python_version, str):
            findings.append(Finding("error", "`python_version` must be a string."))
        elif python_version not in PYTHON_VERSIONS:
            findings.append(Finding("error", "`python_version` should be one of 3.11, 3.12, or 3.13."))
    elif some_python:
        findings.append(Finding("warning", "Python graphs default to python_version 3.11 when omitted."))

    node_version = config.get("node_version")
    if node_version is not None:
        if not isinstance(node_version, str) or not node_version.isdigit():
            findings.append(Finding("error", "`node_version` must be a major version string such as '20'."))
        elif int(node_version) < 20:
            findings.append(Finding("error", "`node_version` must be at least major version 20."))
    elif some_node:
        findings.append(Finding("warning", "Node graphs default to node_version 20 when omitted."))

    dependencies = config.get("dependencies")
    if source_kind == "uv":
        if dependencies:
            findings.append(Finding("error", "Remove `dependencies` when using source.kind 'uv'."))
        if not python_version:
            findings.append(Finding("error", "source.kind 'uv' requires `python_version`."))
        root = source.get("root", ".") if isinstance(source, dict) else "."
        if not isinstance(root, str) or not root.strip():
            findings.append(Finding("error", "`source.root` must be a non-empty string."))
    elif some_python:
        if not isinstance(dependencies, list) or not dependencies:
            findings.append(Finding("error", "Python dependency-based configs require non-empty `dependencies`."))

    if source is not None:
        if not isinstance(source, dict):
            findings.append(Finding("error", "`source` must be an object."))
        elif source_kind != "uv":
            findings.append(Finding("error", "Only source.kind 'uv' is supported."))

    if config.get("project_root") or config.get("package"):
        findings.append(Finding("error", "Top-level `project_root` and `package` are legacy fields; use `source.root` and `source.package`."))

    image_distro = config.get("image_distro")
    if image_distro is not None and image_distro not in IMAGE_DISTROS:
        findings.append(Finding("error", "`image_distro` must be one of debian, bookworm, or wolfi."))

    pip_installer = config.get("pip_installer")
    if pip_installer is not None and pip_installer not in PIP_INSTALLERS:
        findings.append(Finding("error", "`pip_installer` must be one of auto, pip, or uv."))

    dockerfile_lines = config.get("dockerfile_lines")
    if dockerfile_lines is not None and not all(isinstance(line, str) for line in dockerfile_lines):
        findings.append(Finding("error", "`dockerfile_lines` must be an array of strings."))

    env = config.get("env")
    if env is not None and not isinstance(env, (str, dict)):
        findings.append(Finding("error", "`env` must be a path string or object mapping names to values."))

    for dep in dependencies or []:
        if isinstance(dep, str) and dep.startswith("."):
            dep_path = (config_dir / dep).resolve()
            if not dep_path.exists():
                findings.append(Finding("error", f"Local dependency path does not exist: {dep}"))

    for object_field in (("auth", "path"), ("encryption", "path"), ("http", "app")):
        parent, child = object_field
        value = config.get(parent)
        if isinstance(value, dict) and child in value:
            target = value[child]
            if not isinstance(target, str) or ":" not in target:
                findings.append(Finding("error", f"`{parent}.{child}` must use './file.py:attribute' format."))

    return findings


def check_imports(config: dict[str, Any], config_path: Path) -> list[Finding]:
    findings: list[Finding] = []
    graphs = config.get("graphs")
    if not isinstance(graphs, dict):
        return findings

    config_dir = config_path.parent.resolve()
    original_path = list(sys.path)
    sys.path.insert(0, str(config_dir))
    for dep in config.get("dependencies") or []:
        if isinstance(dep, str) and dep.startswith("."):
            dep_path = (config_dir / dep).resolve()
            if dep_path.is_dir():
                sys.path.insert(0, str(dep_path))

    try:
        for graph_id, spec in graphs.items():
            path_spec = graph_path(spec)
            if not path_spec or ":" not in path_spec or is_node_graph(path_spec):
                continue
            file_part, attr_path = path_spec.split(":", 1)
            graph_file = (config_dir / file_part).resolve()
            if not graph_file.exists():
                continue
            module_name = f"_langgraph_config_check_{graph_id}"
            try:
                module_spec = importlib.util.spec_from_file_location(module_name, graph_file)
                if module_spec is None or module_spec.loader is None:
                    findings.append(Finding("error", f"Cannot create import spec for graph `{graph_id}`."))
                    continue
                module = importlib.util.module_from_spec(module_spec)
                module_spec.loader.exec_module(module)
                current: Any = module
                for part in attr_path.split("."):
                    current = getattr(current, part)
            except Exception as exc:  # noqa: BLE001 - report import-time failures to user.
                findings.append(Finding("error", f"Import check failed for graph `{graph_id}`: {exc.__class__.__name__}: {exc}"))
            else:
                if current.__class__.__name__ == "StateGraph":
                    findings.append(Finding("warning", f"Graph `{graph_id}` appears to export an uncompiled StateGraph; export a compiled graph instead."))
    finally:
        sys.path[:] = original_path

    return findings


def emit(findings: list[Finding], as_json: bool) -> None:
    if as_json:
        print(json.dumps([finding.__dict__ for finding in findings], indent=2))
        return
    if not findings:
        print("OK: no issues found.")
        return
    for finding in findings:
        print(f"{finding.level.upper()}: {finding.message}")


def main() -> int:
    args = parse_args()
    if args.write_tiny_fixture:
        write_tiny_fixture(args.write_tiny_fixture)
        return 0

    config_path = Path(args.config)
    config, findings = load_config(config_path)
    if config is not None:
        findings.extend(validate_shape(config, config_path))
        if args.check_imports:
            findings.extend(check_imports(config, config_path))

    emit(findings, args.json)
    return 1 if any(finding.level == "error" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
