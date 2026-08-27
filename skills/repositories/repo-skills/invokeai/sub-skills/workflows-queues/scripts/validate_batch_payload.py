#!/usr/bin/env python3
"""Validate common InvokeAI queue Batch payload mistakes without importing InvokeAI."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REQUIRED_BATCH_KEYS = ("graph",)


def issue(severity: str, message: str, path: str = "$") -> dict[str, str]:
    return {"severity": severity, "path": path, "message": message}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def unwrap_batch_payload(payload: Any) -> Any:
    if isinstance(payload, dict) and "batch" in payload and isinstance(payload["batch"], dict):
        return payload["batch"]
    return payload


def type_family(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict) and set(value.keys()) == {"image_name"} and isinstance(value.get("image_name"), str):
        return "image"
    if value is None:
        return "null"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return type(value).__name__


def extract_graph_nodes(graph: Any) -> tuple[dict[str, set[str]], list[dict[str, str]]]:
    issues: list[dict[str, str]] = []
    nodes_by_id: dict[str, set[str]] = {}
    if not isinstance(graph, dict):
        issues.append(issue("error", "graph must be an object", "$.graph"))
        return nodes_by_id, issues

    nodes = graph.get("nodes")
    if isinstance(nodes, dict):
        for node_id, node in nodes.items():
            node_path = f"$.graph.nodes.{node_id}"
            if not isinstance(node, dict):
                issues.append(issue("warning", "graph node is not an object; field validation skipped", node_path))
                nodes_by_id[str(node_id)] = set()
                continue
            field_names = {str(key) for key in node.keys()}
            nested_inputs = node.get("inputs")
            if isinstance(nested_inputs, dict):
                field_names.update(str(key) for key in nested_inputs.keys())
            data_obj = node.get("data")
            if isinstance(data_obj, dict):
                field_names.update(str(key) for key in data_obj.keys())
                data_inputs = data_obj.get("inputs")
                if isinstance(data_inputs, dict):
                    field_names.update(str(key) for key in data_inputs.keys())
            nodes_by_id[str(node_id)] = field_names
    elif isinstance(nodes, list):
        for index, node in enumerate(nodes):
            node_path = f"$.graph.nodes[{index}]"
            if not isinstance(node, dict):
                issues.append(issue("warning", "graph node is not an object; field validation skipped", node_path))
                continue
            node_id = node.get("id")
            if not isinstance(node_id, str) or not node_id:
                issues.append(issue("error", "graph node id must be a non-empty string", f"{node_path}.id"))
                continue
            field_names = {str(key) for key in node.keys()}
            inputs = node.get("inputs")
            if isinstance(inputs, dict):
                field_names.update(str(key) for key in inputs.keys())
            data_obj = node.get("data")
            if isinstance(data_obj, dict):
                field_names.update(str(key) for key in data_obj.keys())
                data_inputs = data_obj.get("inputs")
                if isinstance(data_inputs, dict):
                    field_names.update(str(key) for key in data_inputs.keys())
            nodes_by_id[node_id] = field_names
    else:
        issues.append(issue("error", "graph.nodes must be an object or list", "$.graph.nodes"))

    return nodes_by_id, issues


def validate_workflow_metadata(workflow: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if workflow is None:
        return issues
    if not isinstance(workflow, dict):
        return [issue("error", "workflow must be an object when provided", "$.workflow")]
    required = ("name", "author", "description", "version", "contact", "tags", "notes", "exposedFields", "meta", "nodes", "edges")
    for key in required:
        if key not in workflow:
            issues.append(issue("warning", f"workflow metadata missing key: {key}", f"$.workflow.{key}"))
    meta = workflow.get("meta")
    if not isinstance(meta, dict):
        issues.append(issue("warning", "workflow.meta should be an object", "$.workflow.meta"))
    elif meta.get("category") not in {"user", "default"}:
        issues.append(issue("warning", "workflow.meta.category should be user or default", "$.workflow.meta.category"))
    if "tags" in workflow and not isinstance(workflow.get("tags"), str):
        issues.append(issue("warning", "workflow.tags should be a comma-separated string", "$.workflow.tags"))
    return issues


def validate_batch(batch: Any) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    summary: dict[str, Any] = {
        "batch_id": None,
        "runs": None,
        "has_workflow": False,
        "groups": 0,
        "requested_sessions_estimate": None,
        "field_mappings": [],
        "graph_node_count": 0,
    }

    if not isinstance(batch, dict):
        return {"ok": False, "summary": summary, "issues": [issue("error", "batch payload must be an object")]}

    for key in REQUIRED_BATCH_KEYS:
        if key not in batch:
            issues.append(issue("error", f"missing required batch key: {key}", f"$.{key}"))

    runs = batch.get("runs", 1)
    summary["runs"] = runs
    if not isinstance(runs, int) or isinstance(runs, bool) or runs < 1:
        issues.append(issue("error", "runs must be an integer >= 1", "$.runs"))
        runs_for_count = 1
    else:
        runs_for_count = runs

    summary["batch_id"] = batch.get("batch_id")
    summary["has_workflow"] = batch.get("workflow") is not None
    issues.extend(validate_workflow_metadata(batch.get("workflow")))

    nodes_by_id, graph_issues = extract_graph_nodes(batch.get("graph"))
    issues.extend(graph_issues)
    summary["graph_node_count"] = len(nodes_by_id)

    data = batch.get("data")
    requested_multiplier = 1
    mappings: list[tuple[str, str]] = []
    group_lengths: list[int] = []

    if data is None:
        summary["groups"] = 0
        summary["requested_sessions_estimate"] = runs_for_count
    elif not isinstance(data, list):
        issues.append(issue("error", "data must be null or a list of zipped groups", "$.data"))
    else:
        summary["groups"] = len(data)
        for group_index, group in enumerate(data):
            group_path = f"$.data[{group_index}]"
            if not isinstance(group, list):
                issues.append(issue("error", "batch data group must be a list", group_path))
                continue
            if not group:
                group_lengths.append(0)
                requested_multiplier *= 0
                issues.append(issue("warning", "empty batch data group requests zero sessions", group_path))
                continue

            lengths: list[int] = []
            for datum_index, datum in enumerate(group):
                datum_path = f"{group_path}[{datum_index}]"
                if not isinstance(datum, dict):
                    issues.append(issue("error", "BatchDatum must be an object", datum_path))
                    continue
                node_path = datum.get("node_path")
                field_name = datum.get("field_name")
                items = datum.get("items", [])

                if not isinstance(node_path, str) or not node_path:
                    issues.append(issue("error", "node_path must be a non-empty string", f"{datum_path}.node_path"))
                if not isinstance(field_name, str) or not field_name:
                    issues.append(issue("error", "field_name must be a non-empty string", f"{datum_path}.field_name"))
                if not isinstance(items, list):
                    issues.append(issue("error", "items must be a list", f"{datum_path}.items"))
                    items = []

                lengths.append(len(items))
                if isinstance(node_path, str) and isinstance(field_name, str):
                    mappings.append((node_path, field_name))
                    if node_path not in nodes_by_id:
                        issues.append(issue("error", f"node_path references unknown graph node {node_path!r}", f"{datum_path}.node_path"))
                    elif nodes_by_id[node_path] and field_name not in nodes_by_id[node_path]:
                        issues.append(issue("warning", f"field_name {field_name!r} not found in lightweight graph fields for node {node_path!r}", f"{datum_path}.field_name"))

                families = [type_family(item) for item in items]
                distinct = sorted(set(families))
                if len(distinct) > 1:
                    issues.append(issue("error", f"items must have one type family; got {distinct}", f"{datum_path}.items"))

            nonempty_lengths = lengths if lengths else [0]
            first_length = nonempty_lengths[0]
            if any(length != first_length for length in nonempty_lengths):
                issues.append(issue("error", f"zipped group item lengths differ: {nonempty_lengths}", group_path))
            group_lengths.append(first_length)
            requested_multiplier *= first_length

        duplicate_mappings = sorted(mapping for mapping, count in Counter(mappings).items() if count > 1)
        for node_path, field_name in duplicate_mappings:
            issues.append(issue("error", f"duplicate node/field mapping: {node_path}.{field_name}", "$.data"))
        summary["field_mappings"] = [f"{node_path}.{field_name}" for node_path, field_name in mappings]
        summary["group_lengths"] = group_lengths
        summary["requested_sessions_estimate"] = requested_multiplier * runs_for_count

    ok = not any(item["severity"] == "error" for item in issues)
    return {"ok": ok, "summary": summary, "issues": issues}


def print_text(result: dict[str, Any], path: Path) -> None:
    summary = result["summary"]
    print(f"Batch payload: {path}")
    print(f"  batch_id: {summary.get('batch_id')}")
    print(f"  runs: {summary.get('runs')}")
    print(f"  graph nodes: {summary.get('graph_node_count')}")
    print(f"  data groups: {summary.get('groups')}")
    print(f"  requested sessions estimate: {summary.get('requested_sessions_estimate')}")
    print(f"  workflow metadata: {'yes' if summary.get('has_workflow') else 'no'}")
    if summary.get("field_mappings"):
        print("  field mappings:")
        for mapping in summary["field_mappings"]:
            print(f"    - {mapping}")
    if result["issues"]:
        print("Issues:")
        for item in result["issues"]:
            print(f"  [{item['severity']}] {item['path']}: {item['message']}")
    else:
        print("Issues: none")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate common InvokeAI queue Batch payload mistakes.")
    parser.add_argument("payload", type=Path, help="Path to a Batch JSON file or an API body containing a batch key")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable JSON result")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero for warnings as well as errors")
    args = parser.parse_args(argv)

    try:
        payload = unwrap_batch_payload(load_json(args.payload))
    except Exception as exc:
        result = {"ok": False, "summary": {}, "issues": [issue("error", f"failed to read JSON: {exc}")]}
    else:
        result = validate_batch(payload)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result, args.payload)

    has_errors = any(item["severity"] == "error" for item in result.get("issues", []))
    has_warnings = any(item["severity"] == "warning" for item in result.get("issues", []))
    return 1 if has_errors or (args.strict and has_warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
