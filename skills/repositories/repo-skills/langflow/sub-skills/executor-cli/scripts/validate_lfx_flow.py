#!/usr/bin/env python3
"""Offline safety helper for Langflow Executor flow JSON.

This script parses a Langflow flow JSON file, performs conservative structural
checks, summarizes nodes/edges/credential-looking fields, and prints safe LFX
command templates. It never imports lfx and never executes a flow.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

SENSITIVE_TOKENS = (
    "api_key",
    "apikey",
    "password",
    "secret",
    "access_key",
    "private_key",
    "api_token",
    "access_token",
    "token",
)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"ERROR: cannot read {path}: {exc}") from exc

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise SystemExit(f"ERROR: top-level JSON must be an object, got {type(payload).__name__}")
    return payload


def _get_graph(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    if isinstance(data, dict) and isinstance(data.get("nodes"), list) and isinstance(data.get("edges"), list):
        return data
    if isinstance(payload.get("nodes"), list) and isinstance(payload.get("edges"), list):
        return payload
    raise SystemExit("ERROR: expected Langflow JSON with data.nodes/data.edges or bare nodes/edges")


def _node_name(node: dict[str, Any]) -> str:
    data = node.get("data") if isinstance(node.get("data"), dict) else {}
    display = data.get("display_name") or data.get("type") or data.get("id") or node.get("id")
    return str(display or "<unknown>")


def _is_sensitive_field(field_name: str, field_def: Any) -> bool:
    lowered = field_name.lower().replace("-", "_")
    if any(token in lowered for token in SENSITIVE_TOKENS):
        return True
    return isinstance(field_def, dict) and bool(field_def.get("password") or field_def.get("display_password"))


def _field_has_value(field_def: Any) -> bool:
    if not isinstance(field_def, dict):
        return False
    return field_def.get("value") not in (None, "", [], {})


def _collect_sensitive_fields(nodes: list[dict[str, Any]]) -> list[tuple[str, str, bool]]:
    fields: list[tuple[str, str, bool]] = []
    for node in nodes:
        node_data = node.get("data") if isinstance(node.get("data"), dict) else {}
        template = node_data.get("node", {}).get("template", {}) if isinstance(node_data.get("node"), dict) else {}
        if not isinstance(template, dict):
            continue
        for field_name, field_def in sorted(template.items()):
            if _is_sensitive_field(str(field_name), field_def):
                fields.append((_node_name(node), str(field_name), _field_has_value(field_def)))
    return fields


def _collect_component_types(nodes: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in nodes:
        node_data = node.get("data") if isinstance(node.get("data"), dict) else {}
        component_type = str(node_data.get("type") or "<missing-type>")
        counts[component_type] = counts.get(component_type, 0) + 1
    return dict(sorted(counts.items()))


def _validate_structure(payload: dict[str, Any], graph: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if "data" in payload:
        for key in ("id", "name", "data"):
            if key not in payload:
                warnings.append(f"missing top-level field {key!r}; lfx validate may fail on full-export checks")
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list):
        raise SystemExit("ERROR: nodes must be a list")
    if not isinstance(edges, list):
        raise SystemExit("ERROR: edges must be a list")

    seen_ids: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise SystemExit(f"ERROR: node at index {index} is not an object")
        node_id = node.get("id")
        if not node_id:
            warnings.append(f"node at index {index} has no id")
        elif str(node_id) in seen_ids:
            warnings.append(f"duplicate node id {node_id!r}")
        else:
            seen_ids.add(str(node_id))
        node_data = node.get("data")
        if not isinstance(node_data, dict):
            warnings.append(f"node {node_id or index!r} has no object data")
        elif not node_data.get("type"):
            warnings.append(f"node {node_id or index!r} is missing data.type")

    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise SystemExit(f"ERROR: edge at index {index} is not an object")
        source = edge.get("source")
        target = edge.get("target")
        if source and str(source) not in seen_ids:
            warnings.append(f"edge {index} references missing source {source!r}")
        if target and str(target) not in seen_ids:
            warnings.append(f"edge {index} references missing target {target!r}")
    return warnings


def _quote_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def _print_templates(path: Path, *, input_value: str) -> None:
    flow = str(path)
    print("\nSafe command templates:")
    print(f"  validate: {_quote_command(['lfx', 'validate', flow, '--level', '4', '--strict'])}")
    print(
        "  run:      "
        + _quote_command(['lfx', 'run', flow, '--input-value', input_value, '--format', 'json'])
    )
    print(
        "  serve:    "
        + _quote_command(['lfx', 'serve', flow, '--env-file', '.env', '--host', '127.0.0.1', '--port', '8000'])
    )
    print(
        "  serve isolated credentials: "
        + _quote_command(['lfx', 'serve', flow, '--env-file', '.env', '--no-env-fallback'])
    )
    print("\nThese templates do not run automatically. Review dependencies and credentials first.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Parse a Langflow flow JSON file offline and print safe lfx command templates "
            "without importing lfx or executing components."
        )
    )
    parser.add_argument("flow", type=Path, help="Path to a Langflow flow JSON file")
    parser.add_argument(
        "--sample-input",
        default="Hello world",
        help="Input string to show in the lfx run template (default: %(default)s)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable summary instead of human-oriented text",
    )
    args = parser.parse_args(argv)

    payload = _load_json(args.flow)
    graph = _get_graph(payload)
    warnings = _validate_structure(payload, graph)

    nodes = [node for node in graph.get("nodes", []) if isinstance(node, dict)]
    edges = [edge for edge in graph.get("edges", []) if isinstance(edge, dict)]
    component_counts = _collect_component_types(nodes)
    sensitive_fields = _collect_sensitive_fields(nodes)

    summary = {
        "path": str(args.flow),
        "name": payload.get("name"),
        "id": payload.get("id"),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "component_types": component_counts,
        "sensitive_fields": [
            {"node": node_name, "field": field_name, "has_embedded_value": has_value}
            for node_name, field_name, has_value in sensitive_fields
        ],
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if not warnings else 2

    print(f"Flow file: {args.flow}")
    print(f"Name: {payload.get('name') or '<not set>'}")
    print(f"ID: {payload.get('id') or '<not set>'}")
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")

    if component_counts:
        print("\nComponent types:")
        for component_type, count in component_counts.items():
            print(f"  - {component_type}: {count}")

    if sensitive_fields:
        print("\nCredential-looking fields:")
        for node_name, field_name, has_value in sensitive_fields:
            value_note = "embedded value present" if has_value else "no embedded value"
            print(f"  - {node_name}.{field_name}: {value_note}")
        print("  Do not commit secrets; prefer environment variables or request-scoped global_vars.")

    if warnings:
        print("\nWarnings:", file=sys.stderr)
        for warning in warnings:
            print(f"  - {warning}", file=sys.stderr)

    _print_templates(args.flow, input_value=args.sample_input)
    return 0 if not warnings else 2


if __name__ == "__main__":
    raise SystemExit(main())
