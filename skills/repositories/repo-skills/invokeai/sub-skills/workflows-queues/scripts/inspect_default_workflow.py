#!/usr/bin/env python3
"""Inspect InvokeAI default workflow JSON without importing InvokeAI."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")
UUIDISH_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
RESOURCE_KEYS = ("model", "image", "board", "style", "lora", "controlnet", "vae")
REQUIRED_KEYS = (
    "id",
    "name",
    "author",
    "description",
    "version",
    "contact",
    "tags",
    "notes",
    "exposedFields",
    "meta",
    "nodes",
    "edges",
)


def issue(severity: str, message: str) -> dict[str, str]:
    return {"severity": severity, "message": message}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def value_preview(value: Any, limit: int = 80) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True) if not isinstance(value, str) else value
    return text if len(text) <= limit else text[: limit - 3] + "..."


def looks_resource_like(key: str, value: Any) -> bool:
    lowered = key.lower()
    if not any(token in lowered for token in RESOURCE_KEYS):
        return False
    if value in (None, "", [], {}):
        return False
    if isinstance(value, str):
        return UUIDISH_RE.match(value) is not None or "/" in value or "\\" in value
    if isinstance(value, dict):
        suspicious_names = {"image_name", "board_id", "style_preset_id", "key", "hash", "path", "name"}
        if suspicious_names.intersection(value):
            return True
        return any(looks_resource_like(str(child_key), child_value) for child_key, child_value in value.items())
    if isinstance(value, list):
        return any(looks_resource_like(key, item) for item in value)
    return False


def iter_resource_values(value: Any, path: str = "$") -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if looks_resource_like(str(key), child):
                found.append((child_path, child))
            found.extend(iter_resource_values(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(iter_resource_values(child, f"{path}[{index}]"))
    return found


def inspect_workflow(data: Any, allow_user_category: bool = False) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    summary: dict[str, Any] = {
        "id": None,
        "name": None,
        "category": None,
        "meta_version": None,
        "node_count": 0,
        "edge_count": 0,
        "exposed_field_count": 0,
        "node_types": {},
        "tags": [],
    }

    if not isinstance(data, dict):
        return {"ok": False, "summary": summary, "issues": [issue("error", "workflow JSON must be an object")]}

    for key in REQUIRED_KEYS:
        if key not in data:
            issues.append(issue("error", f"missing required top-level key: {key}"))

    workflow_id = data.get("id")
    summary["id"] = workflow_id
    summary["name"] = data.get("name")
    if not isinstance(workflow_id, str) or not workflow_id:
        issues.append(issue("error", "id must be a non-empty string"))
    elif not allow_user_category and not workflow_id.startswith("default_"):
        issues.append(issue("error", 'default workflow id must start with "default_"'))

    tags = data.get("tags")
    if isinstance(tags, str):
        summary["tags"] = [tag.strip() for tag in tags.split(",") if tag.strip()]
    elif tags is not None:
        issues.append(issue("warning", "tags should be a comma-separated string, not another JSON type"))

    meta = data.get("meta")
    if not isinstance(meta, dict):
        issues.append(issue("error", "meta must be an object"))
        meta = {}
    category = meta.get("category")
    version = meta.get("version")
    summary["category"] = category
    summary["meta_version"] = version
    allowed_categories = {"default", "user"} if allow_user_category else {"default"}
    if category not in allowed_categories:
        expected = "default or user" if allow_user_category else "default"
        issues.append(issue("error", f"meta.category must be {expected}; got {category!r}"))
    if not isinstance(version, str) or SEMVER_RE.match(version) is None:
        issues.append(issue("error", f"meta.version must be a semver string; got {version!r}"))

    nodes = data.get("nodes")
    if not isinstance(nodes, list):
        issues.append(issue("error", "nodes must be a list"))
        nodes = []
    edges = data.get("edges")
    if not isinstance(edges, list):
        issues.append(issue("error", "edges must be a list"))
        edges = []
    exposed_fields = data.get("exposedFields")
    if not isinstance(exposed_fields, list):
        issues.append(issue("error", "exposedFields must be a list"))
        exposed_fields = []

    summary["node_count"] = len(nodes)
    summary["edge_count"] = len(edges)
    summary["exposed_field_count"] = len(exposed_fields)

    node_ids: list[str] = []
    node_inputs: dict[str, set[str]] = {}
    node_types: Counter[str] = Counter()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            issues.append(issue("error", f"nodes[{index}] must be an object"))
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id:
            issues.append(issue("error", f"nodes[{index}].id must be a non-empty string"))
            continue
        node_ids.append(node_id)
        data_obj = node.get("data")
        if isinstance(data_obj, dict):
            node_type = data_obj.get("type")
            if isinstance(node_type, str):
                node_types[node_type] += 1
            inputs = data_obj.get("inputs")
            if isinstance(inputs, dict):
                node_inputs[node_id] = {str(field_name) for field_name in inputs.keys()}
        else:
            issues.append(issue("warning", f"node {node_id} has no object data block"))
    summary["node_types"] = dict(sorted(node_types.items()))

    duplicate_ids = sorted(node_id for node_id, count in Counter(node_ids).items() if count > 1)
    for node_id in duplicate_ids:
        issues.append(issue("error", f"duplicate node id: {node_id}"))
    node_id_set = set(node_ids)

    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            issues.append(issue("error", f"edges[{index}] must be an object"))
            continue
        source = edge.get("source")
        target = edge.get("target")
        if source not in node_id_set:
            issues.append(issue("error", f"edges[{index}].source references unknown node {source!r}"))
        if target not in node_id_set:
            issues.append(issue("error", f"edges[{index}].target references unknown node {target!r}"))

    for index, exposed in enumerate(exposed_fields):
        if not isinstance(exposed, dict):
            issues.append(issue("error", f"exposedFields[{index}] must be an object"))
            continue
        node_id = exposed.get("nodeId")
        field_name = exposed.get("fieldName")
        if node_id not in node_id_set:
            issues.append(issue("error", f"exposedFields[{index}] references unknown node {node_id!r}"))
            continue
        if not isinstance(field_name, str) or not field_name:
            issues.append(issue("error", f"exposedFields[{index}].fieldName must be a non-empty string"))
            continue
        if node_id in node_inputs and field_name not in node_inputs[node_id]:
            issues.append(issue("warning", f"exposed field {node_id}.{field_name} is absent from node data.inputs"))

    for path, value in iter_resource_values(data):
        issues.append(issue("warning", f"possible local resource reference at {path}: {value_preview(value)}"))

    ok = not any(item["severity"] == "error" for item in issues)
    return {"ok": ok, "summary": summary, "issues": issues}


def print_text(result: dict[str, Any], path: Path) -> None:
    summary = result["summary"]
    print(f"Workflow: {path}")
    print(f"  id: {summary.get('id')}")
    print(f"  name: {summary.get('name')}")
    print(f"  category: {summary.get('category')}")
    print(f"  meta.version: {summary.get('meta_version')}")
    print(f"  nodes: {summary.get('node_count')}  edges: {summary.get('edge_count')}  exposedFields: {summary.get('exposed_field_count')}")
    if summary.get("tags"):
        print(f"  tags: {', '.join(summary['tags'])}")
    if summary.get("node_types"):
        node_type_text = ", ".join(f"{name}={count}" for name, count in summary["node_types"].items())
        print(f"  node types: {node_type_text}")
    if result["issues"]:
        print("Issues:")
        for item in result["issues"]:
            print(f"  [{item['severity']}] {item['message']}")
    else:
        print("Issues: none")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect an InvokeAI workflow JSON file for default-workflow shape issues.")
    parser.add_argument("workflow", type=Path, help="Path to a workflow JSON file")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable JSON result")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero for warnings as well as errors")
    parser.add_argument("--allow-user-category", action="store_true", help="Allow meta.category=user and non-default IDs")
    args = parser.parse_args(argv)

    try:
        data = load_json(args.workflow)
    except Exception as exc:
        result = {"ok": False, "summary": {}, "issues": [issue("error", f"failed to read JSON: {exc}")]}
    else:
        result = inspect_workflow(data, allow_user_category=args.allow_user_category)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result, args.workflow)

    has_errors = any(item["severity"] == "error" for item in result.get("issues", []))
    has_warnings = any(item["severity"] == "warning" for item in result.get("issues", []))
    return 1 if has_errors or (args.strict and has_warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
