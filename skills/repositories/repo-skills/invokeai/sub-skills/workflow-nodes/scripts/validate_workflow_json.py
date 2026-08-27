#!/usr/bin/env python3
"""Validate InvokeAI workflow/graph JSON structure without importing InvokeAI.

This is a lightweight, safe checker for malformed graph JSON, missing nodes,
node-id mismatches, edge shape problems, duplicate edge destinations, and cycles.
It cannot perform InvokeAI's full type-aware validation because that requires the
runtime invocation registry and custom node imports.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


class Finding:
    def __init__(self, level: str, message: str) -> None:
        self.level = level
        self.message = message

    def __str__(self) -> str:
        return f"{self.level.upper()}: {self.message}"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def select_graph(data: Any, graph_key: str | None) -> Any:
    if graph_key:
        current = data
        for part in graph_key.split("."):
            if not isinstance(current, dict) or part not in current:
                raise KeyError(f"graph key path '{graph_key}' not found at '{part}'")
            current = current[part]
        return current

    if isinstance(data, dict) and "nodes" in data and "edges" in data:
        return data

    candidates = ["graph", "session", "workflow", "workflow_graph"]
    for key in candidates:
        value = data.get(key) if isinstance(data, dict) else None
        if isinstance(value, dict) and "nodes" in value and "edges" in value:
            return value
        if isinstance(value, dict) and isinstance(value.get("graph"), dict):
            nested = value["graph"]
            if "nodes" in nested and "edges" in nested:
                return nested

    return data


def normalize_nodes(nodes: Any, findings: list[Finding]) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}

    if isinstance(nodes, dict):
        iterator = nodes.items()
    elif isinstance(nodes, list):
        iterator = []
        seen: set[str] = set()
        for index, node in enumerate(nodes):
            if not isinstance(node, dict):
                findings.append(Finding("error", f"nodes[{index}] is not an object"))
                continue
            node_id = node.get("id")
            if not isinstance(node_id, str) or not node_id:
                findings.append(Finding("error", f"nodes[{index}] is missing a string id"))
                continue
            if node_id in seen:
                findings.append(Finding("error", f"duplicate node id '{node_id}'"))
            seen.add(node_id)
            iterator.append((node_id, node))
    else:
        findings.append(Finding("error", "graph.nodes must be an object or list"))
        return normalized

    for key, node in iterator:
        if not isinstance(key, str) or not key:
            findings.append(Finding("error", f"node key {key!r} is not a non-empty string"))
            continue
        if not isinstance(node, dict):
            findings.append(Finding("error", f"node '{key}' is not an object"))
            continue
        node_id = node.get("id")
        if node_id is None:
            findings.append(Finding("warning", f"node '{key}' has no id field; InvokeAI nodes normally include one"))
            node_id = key
        elif node_id != key:
            findings.append(Finding("error", f"node key '{key}' does not match node id '{node_id}'"))
        if "type" not in node:
            findings.append(Finding("error", f"node '{key}' is missing required type discriminator"))
        elif not isinstance(node.get("type"), str) or not node.get("type"):
            findings.append(Finding("error", f"node '{key}' has non-string or empty type"))
        if key in normalized:
            findings.append(Finding("error", f"duplicate node key '{key}'"))
        normalized[key] = node

    return normalized


def parse_connection(raw: Any, edge_index: int, side: str, findings: list[Finding]) -> tuple[str, str] | None:
    if not isinstance(raw, dict):
        findings.append(Finding("error", f"edges[{edge_index}].{side} is not an object"))
        return None
    node_id = raw.get("node_id")
    field = raw.get("field")
    if not isinstance(node_id, str) or not node_id:
        findings.append(Finding("error", f"edges[{edge_index}].{side}.node_id must be a non-empty string"))
        return None
    if not isinstance(field, str) or not field:
        findings.append(Finding("error", f"edges[{edge_index}].{side}.field must be a non-empty string"))
        return None
    return node_id, field


def validate_edges(graph: dict[str, Any], nodes: dict[str, dict[str, Any]], findings: list[Finding]) -> list[tuple[str, str]]:
    edges = graph.get("edges")
    graph_edges: list[tuple[str, str]] = []
    seen_edges: set[tuple[str, str, str, str]] = set()
    destination_counts: defaultdict[tuple[str, str], int] = defaultdict(int)

    if not isinstance(edges, list):
        findings.append(Finding("error", "graph.edges must be a list"))
        return graph_edges

    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            findings.append(Finding("error", f"edges[{index}] is not an object"))
            continue
        source = parse_connection(edge.get("source"), index, "source", findings)
        destination = parse_connection(edge.get("destination"), index, "destination", findings)
        if source is None or destination is None:
            continue

        source_id, source_field = source
        destination_id, destination_field = destination

        if source_id not in nodes:
            findings.append(Finding("error", f"edges[{index}] source node '{source_id}' does not exist"))
        if destination_id not in nodes:
            findings.append(Finding("error", f"edges[{index}] destination node '{destination_id}' does not exist"))

        edge_key = (source_id, source_field, destination_id, destination_field)
        if edge_key in seen_edges:
            findings.append(Finding("error", f"edges[{index}] duplicates edge {source_id}.{source_field} -> {destination_id}.{destination_field}"))
        seen_edges.add(edge_key)

        destination_counts[(destination_id, destination_field)] += 1
        graph_edges.append((source_id, destination_id))

        source_node = nodes.get(source_id, {})
        destination_node = nodes.get(destination_id, {})
        if source_id in nodes and source_field in source_node:
            findings.append(Finding("warning", f"edge {source_id}.{source_field} uses a field present on the source node body; source fields should usually be output fields"))
        if destination_id in nodes and destination_field not in destination_node:
            findings.append(Finding("warning", f"edge destination {destination_id}.{destination_field} is not present in serialized node fields; full InvokeAI validation is needed to confirm it exists"))

    for (node_id, field), count in sorted(destination_counts.items()):
        if count <= 1:
            continue
        node_type = nodes.get(node_id, {}).get("type")
        if not (node_type == "collect" and field == "item"):
            findings.append(Finding("error", f"destination {node_id}.{field} has {count} incoming edges; only collect.item normally accepts multiple inputs"))

    return graph_edges


def find_cycle(node_ids: set[str], edges: list[tuple[str, str]]) -> list[str] | None:
    adjacency: defaultdict[str, list[str]] = defaultdict(list)
    indegree: dict[str, int] = {node_id: 0 for node_id in node_ids}
    for source, destination in edges:
        if source not in node_ids or destination not in node_ids:
            continue
        adjacency[source].append(destination)
        indegree[destination] += 1

    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for destination in adjacency[node]:
            indegree[destination] -= 1
            if indegree[destination] == 0:
                queue.append(destination)

    if visited == len(node_ids):
        return None

    return sorted(node for node, degree in indegree.items() if degree > 0)


def validate_graph(graph: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(graph, dict):
        return [Finding("error", "selected graph is not a JSON object")]

    if "nodes" not in graph:
        findings.append(Finding("error", "graph is missing nodes"))
    if "edges" not in graph:
        findings.append(Finding("error", "graph is missing edges"))
    if findings:
        return findings

    nodes = normalize_nodes(graph.get("nodes"), findings)
    edges = validate_edges(graph, nodes, findings)

    cycle_nodes = find_cycle(set(nodes), edges)
    if cycle_nodes:
        findings.append(Finding("error", "graph contains at least one directed cycle involving: " + ", ".join(cycle_nodes)))

    for node_id, node in sorted(nodes.items()):
        node_type = node.get("type")
        if node_type == "iterate":
            collection_inputs = [edge for edge in graph.get("edges", []) if isinstance(edge, dict) and edge.get("destination", {}).get("node_id") == node_id and edge.get("destination", {}).get("field") == "collection"]
            if len(collection_inputs) == 0:
                findings.append(Finding("warning", f"iterate node '{node_id}' has no collection input edge"))
            elif len(collection_inputs) > 1:
                findings.append(Finding("error", f"iterate node '{node_id}' has multiple collection input edges"))
        elif node_type == "collect":
            inputs = [edge for edge in graph.get("edges", []) if isinstance(edge, dict) and edge.get("destination", {}).get("node_id") == node_id and edge.get("destination", {}).get("field") in {"item", "collection"}]
            if len(inputs) == 0:
                findings.append(Finding("warning", f"collect node '{node_id}' has no item or collection input edge"))

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lightweight structural validation for InvokeAI workflow/graph JSON.")
    parser.add_argument("json_file", type=Path, help="Path to a workflow, session, or graph JSON file")
    parser.add_argument("--graph-key", help="Dot-separated key path to the graph object, e.g. graph or session.graph")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON instead of text")
    args = parser.parse_args(argv)

    try:
        data = load_json(args.json_file)
        graph = select_graph(data, args.graph_key)
        findings = validate_graph(graph)
    except Exception as exc:  # noqa: BLE001 - CLI should report all parse/selection failures plainly.
        findings = [Finding("error", str(exc))]

    error_count = sum(1 for finding in findings if finding.level == "error")
    warning_count = sum(1 for finding in findings if finding.level == "warning")

    if args.json:
        print(json.dumps({"ok": error_count == 0, "errors": error_count, "warnings": warning_count, "findings": [{"level": f.level, "message": f.message} for f in findings]}, indent=2))
    else:
        if findings:
            for finding in findings:
                print(finding)
        else:
            print("OK: no structural issues found")
        print(f"Summary: {error_count} error(s), {warning_count} warning(s)")
        if warning_count:
            print("Note: warnings may require full InvokeAI registry/type validation to resolve.")

    return 1 if error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
