#!/usr/bin/env python3
"""Static Langflow flow JSON preflight without importing Langflow.

This helper is intentionally conservative: it checks JSON parsing, common
Langflow flow topology, obvious node/edge mistakes, and optional tweak keys.
Use `lfx validate` afterwards when installed-package component validation is
needed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_CODE_EXECUTION_FIELD_NAMES = {
    "code",
    "python_code",
    "tool_code",
    "filter_instruction",
}


@dataclass
class Issue:
    severity: str
    message: str
    path: str | None = None

    def as_dict(self) -> dict[str, str]:
        data = {"severity": self.severity, "message": self.message}
        if self.path:
            data["path"] = self.path
        return data


@dataclass
class FlowReport:
    path: Path
    issues: list[Issue] = field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    def add(self, severity: str, message: str, path: str | None = None) -> None:
        self.issues.append(Issue(severity=severity, message=message, path=path))

    def ok(self, *, strict: bool) -> bool:
        if self.errors:
            return False
        return not (strict and self.warnings)

    def as_dict(self, *, strict: bool) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "ok": self.ok(strict=strict),
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "issues": [issue.as_dict() for issue in self.issues],
        }


def _load_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle), None
    except FileNotFoundError:
        return None, "Cannot read file: path does not exist"
    except PermissionError:
        return None, "Cannot read file: permission denied"
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
    except OSError as exc:
        return None, f"Cannot read file: {exc}"


def _graph_data(flow: Any) -> tuple[dict[str, Any] | None, str]:
    if not isinstance(flow, dict):
        return None, ""
    data = flow.get("data")
    if isinstance(data, dict) and ("nodes" in data or "edges" in data):
        return data, "data"
    if "nodes" in flow or "edges" in flow:
        return flow, ""
    return None, ""


def _path(prefix: str, key: str) -> str:
    return f"{prefix}.{key}" if prefix else key


def _node_id(node: Any) -> str | None:
    if not isinstance(node, dict):
        return None
    root_id = node.get("id")
    if isinstance(root_id, str) and root_id:
        return root_id
    data_id = (node.get("data") or {}).get("id") if isinstance(node.get("data"), dict) else None
    return data_id if isinstance(data_id, str) and data_id else None


def _node_data(node: Any) -> dict[str, Any]:
    if isinstance(node, dict) and isinstance(node.get("data"), dict):
        return node["data"]
    return {}


def _node_template(node: Any) -> dict[str, Any]:
    data = _node_data(node)
    node_meta = data.get("node") if isinstance(data.get("node"), dict) else {}
    template = node_meta.get("template") if isinstance(node_meta.get("template"), dict) else {}
    return template


def _node_type(node: Any) -> str | None:
    if not isinstance(node, dict):
        return None
    data = _node_data(node)
    for value in (data.get("type"), node.get("type")):
        if isinstance(value, str) and value:
            return value
    return None


def _node_display_name(node: Any) -> str | None:
    data = _node_data(node)
    node_meta = data.get("node") if isinstance(data.get("node"), dict) else {}
    value = node_meta.get("display_name") or data.get("display_name")
    return value if isinstance(value, str) and value else None


def _edge_endpoint(edge: Any, key: str) -> str | None:
    if not isinstance(edge, dict):
        return None
    value = edge.get(key)
    return value if isinstance(value, str) and value else None


def _target_field(edge: Any) -> str | None:
    if not isinstance(edge, dict):
        return None
    data = edge.get("data") if isinstance(edge.get("data"), dict) else {}
    target_handle = data.get("targetHandle") if isinstance(data.get("targetHandle"), dict) else {}
    for value in (target_handle.get("fieldName"), edge.get("targetHandle")):
        if isinstance(value, str) and value:
            return value
    return None


def _field_has_value(field: Any) -> bool:
    if not isinstance(field, dict):
        return field not in (None, "")
    if "value" not in field:
        return False
    value = field.get("value")
    return value not in (None, "", [], {})


def _env_like_value(value: Any) -> str | None:
    if isinstance(value, str) and value and not value.startswith("sk-"):
        return value
    return None


def _collect_json_files(paths: list[Path]) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    errors: list[str] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(child for child in path.rglob("*.json") if child.is_file()))
        elif path.is_file():
            files.append(path)
        else:
            errors.append(f"Cannot read path: {path}")
    return files, errors


def _validate_tweaks(report: FlowReport, tweaks: Any, nodes_by_id: dict[str, Any]) -> None:
    if tweaks is None:
        return
    if not isinstance(tweaks, dict):
        report.add("error", "Tweaks must be a JSON object", "tweaks")
        return

    display_to_nodes: dict[str, list[Any]] = {}
    all_template_fields: set[str] = set()
    for node in nodes_by_id.values():
        if display := _node_display_name(node):
            display_to_nodes.setdefault(display, []).append(node)
        all_template_fields.update(_node_template(node).keys())

    for key, value in tweaks.items():
        if not isinstance(key, str) or not key:
            report.add("error", "Tweak keys must be non-empty strings", "tweaks")
            continue
        if isinstance(value, dict):
            target_nodes: list[Any] = []
            if key in nodes_by_id:
                target_nodes = [nodes_by_id[key]]
            elif key in display_to_nodes:
                target_nodes = display_to_nodes[key]
                if len(target_nodes) > 1:
                    report.add("warning", f"Tweak key {key!r} matches multiple display names; prefer node ids", f"tweaks.{key}")
            else:
                report.add(
                    "warning",
                    f"Tweak key {key!r} does not match a node id or display name; if intentional, use scalar global field tweaks",
                    f"tweaks.{key}",
                )
                continue

            for node in target_nodes:
                template = _node_template(node)
                node_id = _node_id(node) or key
                for field_name, field_value in value.items():
                    field_path = f"tweaks.{key}.{field_name}"
                    if field_name not in template:
                        report.add("warning", f"Tweak field {field_name!r} is not in template for node {node_id!r}", field_path)
                        continue
                    template_field = template[field_name]
                    field_type = template_field.get("type") if isinstance(template_field, dict) else None
                    if field_name in _CODE_EXECUTION_FIELD_NAMES or field_type == "code":
                        report.add("warning", f"Runtime will refuse code-field tweak {field_name!r} on node {node_id!r}", field_path)
                    if isinstance(field_value, str) and field_type in {"dict", "NestedDict", "mcp"}:
                        report.add("warning", f"Field {field_name!r} expects structured data; pass a JSON object if possible", field_path)
        else:
            if key not in all_template_fields:
                report.add("warning", f"Global scalar tweak {key!r} does not match any discovered template field", f"tweaks.{key}")
            if key in _CODE_EXECUTION_FIELD_NAMES:
                report.add("warning", f"Runtime will refuse global code-field tweak {key!r}", f"tweaks.{key}")


def validate_flow(path: Path, *, tweaks: Any = None, strict_export_shape: bool = False) -> FlowReport:
    report = FlowReport(path=path)
    flow, load_error = _load_json(path)
    if load_error:
        report.add("error", load_error)
        return report

    if not isinstance(flow, dict):
        report.add("error", "Flow JSON must be an object at the top level")
        return report

    graph, graph_prefix = _graph_data(flow)
    if graph is None:
        report.add("error", "Flow must contain graph arrays at data.nodes/data.edges or top-level nodes/top-level edges")
        return report

    if strict_export_shape:
        for key in ("id", "name", "data"):
            if key not in flow:
                report.add("error", f"Exported flow is missing top-level {key!r}", key)
        if graph_prefix != "data":
            report.add("error", "Exported flow should store the graph under top-level data", "data")

    if "data" in flow and not isinstance(flow.get("data"), dict):
        report.add("error", "Top-level data must be an object", "data")

    nodes = graph.get("nodes")
    edges = graph.get("edges")
    nodes_path = _path(graph_prefix, "nodes")
    edges_path = _path(graph_prefix, "edges")

    if not isinstance(nodes, list):
        report.add("error", "Flow graph must contain a nodes list", nodes_path)
        nodes = []
    if not isinstance(edges, list):
        report.add("error", "Flow graph must contain an edges list", edges_path)
        edges = []

    report.node_count = len(nodes)
    report.edge_count = len(edges)

    ids_seen: dict[str, int] = {}
    nodes_by_id: dict[str, Any] = {}
    for index, node in enumerate(nodes):
        node_path = f"{nodes_path}[{index}]"
        if not isinstance(node, dict):
            report.add("error", "Node must be an object", node_path)
            continue
        node_id = _node_id(node)
        if not node_id:
            report.add("error", "Node is missing id", node_path)
        else:
            ids_seen[node_id] = ids_seen.get(node_id, 0) + 1
            nodes_by_id.setdefault(node_id, node)
            data_id = _node_data(node).get("id")
            if isinstance(data_id, str) and data_id and data_id != node_id:
                report.add("warning", f"Node root id {node_id!r} differs from data.id {data_id!r}", node_path)
        if not _node_type(node):
            report.add("warning", "Node is missing component type", node_path)
        if not _node_display_name(node) and _node_type(node) not in {"note", "noteNode"}:
            report.add("warning", "Node is missing display name", node_path)

        template = _node_template(node)
        if template:
            incoming_fields = {_target_field(edge) for edge in edges if _edge_endpoint(edge, "target") == node_id}
            for field_name, field_meta in template.items():
                if not isinstance(field_meta, dict):
                    continue
                field_path = f"{node_path}.data.node.template.{field_name}"
                if field_meta.get("required") is True and field_name not in incoming_fields and not _field_has_value(field_meta):
                    report.add("warning", f"Required field {field_name!r} has no value or incoming edge", field_path)
                if field_meta.get("password") or field_meta.get("display_password"):
                    value = field_meta.get("value")
                    env_value = _env_like_value(value)
                    if not _field_has_value(field_meta) and field_name not in incoming_fields:
                        report.add("warning", f"Credential-like field {field_name!r} has no value or incoming edge", field_path)
                    elif env_value and not _ENV_NAME_RE.match(env_value):
                        report.add("warning", f"Credential variable name {env_value!r} is not env-var safe", field_path)
    duplicates = sorted(node_id for node_id, count in ids_seen.items() if count > 1)
    for node_id in duplicates:
        report.add("error", f"Duplicate node id {node_id!r}", nodes_path)

    for index, edge in enumerate(edges):
        edge_path = f"{edges_path}[{index}]"
        if not isinstance(edge, dict):
            report.add("error", "Edge must be an object", edge_path)
            continue
        source = _edge_endpoint(edge, "source")
        target = _edge_endpoint(edge, "target")
        if not source:
            report.add("error", "Edge is missing source node id", edge_path)
        elif source not in nodes_by_id:
            report.add("error", f"Edge source {source!r} does not match any node id", edge_path)
        if not target:
            report.add("error", "Edge is missing target node id", edge_path)
        elif target not in nodes_by_id:
            report.add("error", f"Edge target {target!r} does not match any node id", edge_path)
        if source == target and source is not None:
            report.add("warning", f"Edge source and target are the same node {source!r}", edge_path)
        if target in nodes_by_id:
            field = _target_field(edge)
            if field:
                template = _node_template(nodes_by_id[target])
                if template and field not in template:
                    report.add("warning", f"Edge targets field {field!r}, but target node template does not expose it", edge_path)

    if len(nodes_by_id) > 1 and not edges:
        report.add("warning", "Flow has multiple nodes but no edges", edges_path)

    _validate_tweaks(report, tweaks, nodes_by_id)
    return report


def _print_text(reports: list[FlowReport], *, strict: bool) -> None:
    for report in reports:
        status = "OK" if report.ok(strict=strict) else "FAIL"
        print(f"{status} {report.path} ({report.node_count} nodes, {report.edge_count} edges)")
        for issue in report.issues:
            location = f" [{issue.path}]" if issue.path else ""
            print(f"  {issue.severity.upper()}: {issue.message}{location}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Static preflight for Langflow flow JSON without importing Langflow.",
    )
    parser.add_argument("paths", nargs="+", type=Path, help="Flow JSON file(s) or directories containing .json files")
    parser.add_argument("--tweaks", type=Path, help="Optional JSON file containing a tweaks object to validate against each flow")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--strict-export-shape", action="store_true", help="Require exported-flow top-level id/name/data shape")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON reports")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    files, path_errors = _collect_json_files(args.paths)
    reports: list[FlowReport] = []

    tweaks = None
    if args.tweaks:
        tweaks, tweak_error = _load_json(args.tweaks)
        if tweak_error:
            report = FlowReport(path=args.tweaks)
            report.add("error", f"Cannot load tweaks file: {tweak_error}")
            reports.append(report)

    for error in path_errors:
        report = FlowReport(path=Path(error.rsplit(": ", 1)[-1]))
        report.add("error", error)
        reports.append(report)

    if not files and not path_errors:
        report = FlowReport(path=Path(os.curdir))
        report.add("error", "No JSON files found")
        reports.append(report)

    for file_path in files:
        reports.append(validate_flow(file_path, tweaks=tweaks, strict_export_shape=args.strict_export_shape))

    if args.json:
        print(json.dumps([report.as_dict(strict=args.strict) for report in reports], indent=2, sort_keys=True))
    else:
        _print_text(reports, strict=args.strict)

    return 1 if any(not report.ok(strict=args.strict) for report in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
