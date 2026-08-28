#!/usr/bin/env python3
"""Offline structural preflight for a DocsGPT workflow graph JSON/YAML file.

Expected top-level keys include ``nodes`` and ``edges``; an optional ``workflow``
object is ignored. This helper does not execute CEL, models, tools, or code.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

NODE_TYPES = {"start", "end", "agent", "note", "state", "condition", "code"}


def load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    try:
        import yaml
    except ImportError:
        return json.loads(text)
    return yaml.safe_load(text)


def source(edge: dict[str, Any]) -> Any:
    return edge.get("source", edge.get("source_id"))


def target(edge: dict[str, Any]) -> Any:
    return edge.get("target", edge.get("target_id"))


def source_handle(edge: dict[str, Any]) -> Any:
    return edge.get("sourceHandle", edge.get("source_handle"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", type=Path)
    args = parser.parse_args()
    try:
        data = load(args.workflow)
    except Exception as error:
        print(f"ERROR: cannot parse workflow: {error}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("ERROR: workflow graph must be an object", file=sys.stderr)
        return 1
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(nodes, list) or not isinstance(edges, list):
        print("ERROR: nodes and edges must be lists", file=sys.stderr)
        return 1

    by_id: dict[str, dict[str, Any]] = {}
    starts: list[str] = []
    ends: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"nodes[{index}] must be an object")
            continue
        node_id = node.get("id")
        node_type = node.get("type")
        if not isinstance(node_id, str) or not node_id:
            errors.append(f"nodes[{index}] requires a non-empty id")
            continue
        if node_id in by_id:
            errors.append(f"duplicate node id {node_id!r}")
        by_id[node_id] = node
        if node_type not in NODE_TYPES:
            errors.append(f"node {node_id!r} has invalid type {node_type!r}")
        if node_type == "start":
            starts.append(node_id)
        if node_type == "end":
            ends.add(node_id)

    if len(starts) != 1:
        errors.append(f"expected exactly one start node, found {len(starts)}")
    if not ends:
        errors.append("expected at least one end node")

    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
    edge_ids: set[str] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"edges[{index}] must be an object")
            continue
        edge_id = edge.get("id")
        if edge_id and edge_id in edge_ids:
            errors.append(f"duplicate edge id {edge_id!r}")
        if edge_id:
            edge_ids.add(edge_id)
        src, dst = source(edge), target(edge)
        if src not in by_id:
            errors.append(f"edge {edge_id or index!r} references missing source {src!r}")
        if dst not in by_id:
            errors.append(f"edge {edge_id or index!r} references missing target {dst!r}")
        if src in by_id and dst in by_id:
            outgoing[src].append(edge)
            incoming[dst].append(edge)

    for node_id, node in by_id.items():
        config = node.get("config") if isinstance(node.get("config"), dict) else {}
        if node.get("type") == "condition":
            handles = {str(source_handle(edge) or "").lower() for edge in outgoing[node_id]}
            if not ({"else", "default"} & handles):
                errors.append(f"condition node {node_id!r} needs an else/default outgoing edge")
            cases = config.get("cases", [])
            if isinstance(cases, list):
                for case_index, case in enumerate(cases):
                    if isinstance(case, dict):
                        expression = case.get("expression", "")
                        if "{{" in str(expression) or "}}" in str(expression):
                            errors.append(f"condition node {node_id!r} case {case_index} uses template braces in CEL")
        if node.get("type") == "state":
            operations = config.get("operations", [])
            if isinstance(operations, list):
                for op_index, operation in enumerate(operations):
                    if not isinstance(operation, dict):
                        errors.append(f"state node {node_id!r} operation {op_index} must be an object")
                        continue
                    if not operation.get("target_variable") and not operation.get("targetVariable"):
                        errors.append(f"state node {node_id!r} operation {op_index} lacks target_variable")
                    expression = operation.get("expression", "")
                    if "{{" in str(expression) or "}}" in str(expression):
                        errors.append(f"state node {node_id!r} operation {op_index} uses template braces in CEL")
        if node.get("type") not in {"end", "note"} and not outgoing[node_id]:
            errors.append(f"node {node_id!r} has no outgoing edge")

    reachable: set[str] = set()
    if len(starts) == 1:
        queue = deque([starts[0]])
        while queue:
            current = queue.popleft()
            if current in reachable:
                continue
            reachable.add(current)
            queue.extend(target(edge) for edge in outgoing[current])
        for node_id, node in by_id.items():
            if node_id not in reachable and node.get("type") != "note":
                warnings.append(f"node {node_id!r} is unreachable from start")
        if not (reachable & ends):
            errors.append("no end node is reachable from start")

        reverse_reachable = set(ends)
        queue = deque(ends)
        while queue:
            current = queue.popleft()
            for edge in incoming[current]:
                src = source(edge)
                if src not in reverse_reachable:
                    reverse_reachable.add(src)
                    queue.append(src)
        for node_id in sorted(reachable - reverse_reachable):
            errors.append(f"reachable node {node_id!r} has no path to an end node")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"Workflow graph is structurally valid ({len(by_id)} nodes, {len(edges)} edges)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
