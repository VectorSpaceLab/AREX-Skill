#!/usr/bin/env python3
"""Safely inspect a RAGFlow agent template or canvas DSL JSON.

The script performs static checks only: it reads a local JSON file, reports DSL
keys, component IDs/classes, graph/path consistency, and variable references.
It never contacts a RAGFlow service and never executes workflow components.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REF_PATTERN = re.compile(
    r"\{*\s*\{([a-zA-Z:0-9]+@[A-Za-z0-9_.-]+|sys\.[A-Za-z0-9_.]+|env\.[A-Za-z0-9_.]+)\}\s*\}*"
)
ITERATION_ALIAS_PATTERN = re.compile(r"\{*\s*\{(item|index|result)\}\s*\}*")


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise SystemExit(f"ERROR: file not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")


def find_dsl(root: Any) -> tuple[dict[str, Any], str]:
    if not isinstance(root, dict):
        raise SystemExit("ERROR: top-level JSON value must be an object")
    if isinstance(root.get("dsl"), dict):
        return root["dsl"], "root.dsl"
    if isinstance(root.get("components"), dict):
        return root, "root"
    raise SystemExit("ERROR: could not find a DSL object with a components map at root or root.dsl")


def iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from iter_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from iter_strings(nested)


def collect_targets(component: dict[str, Any]) -> dict[str, list[str]]:
    targets: dict[str, list[str]] = defaultdict(list)
    for field in ("upstream", "downstream"):
        values = component.get(field, [])
        if isinstance(values, list):
            targets[field].extend(str(item) for item in values if isinstance(item, str))

    params = component.get("obj", {}).get("params", {})
    if isinstance(params, dict):
        exception_goto = params.get("exception_goto")
        if isinstance(exception_goto, list):
            targets["exception_goto"].extend(str(item) for item in exception_goto if isinstance(item, str))

        for condition in params.get("conditions", []) if isinstance(params.get("conditions"), list) else []:
            if isinstance(condition, dict) and isinstance(condition.get("to"), list):
                targets["condition.to"].extend(str(item) for item in condition["to"] if isinstance(item, str))
        end_cpn_ids = params.get("end_cpn_ids")
        if isinstance(end_cpn_ids, list):
            targets["end_cpn_ids"].extend(str(item) for item in end_cpn_ids if isinstance(item, str))

    parent_id = component.get("parent_id")
    if isinstance(parent_id, str) and parent_id:
        targets["parent_id"].append(parent_id)
    return dict(targets)


def graph_edges(graph: Any) -> list[tuple[str, str]]:
    if not isinstance(graph, dict):
        return []
    edges = []
    for edge in graph.get("edges", []) if isinstance(graph.get("edges"), list) else []:
        if not isinstance(edge, dict):
            continue
        source = edge.get("source")
        target = edge.get("target")
        if isinstance(source, str) and isinstance(target, str):
            edges.append((source, target))
    return edges


def graph_nodes(graph: Any) -> set[str]:
    if not isinstance(graph, dict):
        return set()
    nodes = set()
    for node in graph.get("nodes", []) if isinstance(graph.get("nodes"), list) else []:
        if isinstance(node, dict) and isinstance(node.get("id"), str):
            nodes.add(node["id"])
    return nodes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Statically inspect a RAGFlow agent template or canvas DSL JSON. No service calls are made."
    )
    parser.add_argument("json_file", type=Path, help="Path to a template export or DSL JSON file")
    parser.add_argument("--show-params", action="store_true", help="Print sorted top-level parameter keys for each component")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when warnings are found")
    args = parser.parse_args(argv)

    root = load_json(args.json_file)
    dsl, dsl_location = find_dsl(root)
    components = dsl.get("components")
    if not isinstance(components, dict) or not components:
        print(f"ERROR: {dsl_location}.components must be a non-empty object", file=sys.stderr)
        return 2

    warnings: list[str] = []
    component_ids = set(components)
    class_counts: Counter[str] = Counter()
    references: dict[str, set[str]] = defaultdict(set)
    aliases: dict[str, set[str]] = defaultdict(set)

    print(f"DSL location: {dsl_location}")
    print("Top-level DSL keys: " + ", ".join(sorted(str(key) for key in dsl.keys())))
    print(f"Components: {len(components)}")

    globals_obj = dsl.get("globals", {})
    if isinstance(globals_obj, dict):
        global_keys = sorted(str(key) for key in globals_obj.keys())
        print("Globals: " + (", ".join(global_keys) if global_keys else "(none)"))
    else:
        warnings.append("globals exists but is not an object")

    path = dsl.get("path", [])
    if isinstance(path, list):
        missing_path = [item for item in path if isinstance(item, str) and item not in component_ids]
        print("Path: " + (" -> ".join(str(item) for item in path) if path else "(empty)"))
        for item in missing_path:
            warnings.append(f"path references missing component: {item}")
    else:
        warnings.append("path exists but is not a list")

    print("\nComponent inventory:")
    for component_id in sorted(components):
        component = components[component_id]
        if not isinstance(component, dict):
            warnings.append(f"component {component_id} is not an object")
            continue
        obj = component.get("obj")
        if not isinstance(obj, dict):
            warnings.append(f"component {component_id} missing obj object")
            component_name = "(missing)"
            params = {}
        else:
            component_name = obj.get("component_name")
            if not isinstance(component_name, str) or not component_name:
                warnings.append(f"component {component_id} missing obj.component_name")
                component_name = "(missing)"
            params = obj.get("params", {})
            if not isinstance(params, dict):
                warnings.append(f"component {component_id} params is not an object")
                params = {}
        class_counts[component_name] += 1

        downstream = component.get("downstream", [])
        upstream = component.get("upstream", [])
        downstream_count = len(downstream) if isinstance(downstream, list) else "?"
        upstream_count = len(upstream) if isinstance(upstream, list) else "?"
        print(f"- {component_id}: {component_name} upstream={upstream_count} downstream={downstream_count}")
        if args.show_params and isinstance(params, dict):
            keys = ", ".join(sorted(str(key) for key in params.keys())) or "(none)"
            print(f"  params: {keys}")

        for relation, targets in collect_targets(component).items():
            for target in targets:
                if target not in component_ids:
                    warnings.append(f"component {component_id} {relation} references missing component: {target}")

        for text in iter_strings(params):
            for match in REF_PATTERN.finditer(text):
                ref = match.group(1)
                references[component_id].add(ref)
                if "@" in ref:
                    ref_component = ref.split("@", 1)[0]
                    if ref_component not in component_ids:
                        warnings.append(f"component {component_id} variable references missing component: {ref}")
            for match in ITERATION_ALIAS_PATTERN.finditer(text):
                aliases[component_id].add(match.group(1))

    print("\nComponent classes:")
    for name, count in sorted(class_counts.items()):
        print(f"- {name}: {count}")

    graph = dsl.get("graph")
    nodes = graph_nodes(graph)
    edges = graph_edges(graph)
    if nodes or edges:
        print(f"\nGraph: nodes={len(nodes)} edges={len(edges)}")
        for node_id in sorted(nodes - component_ids):
            warnings.append(f"graph node has no matching component: {node_id}")
        for component_id in sorted(component_ids - nodes):
            warnings.append(f"component has no matching graph node: {component_id}")
        component_edges = set()
        for source, component in components.items():
            if isinstance(component, dict) and isinstance(component.get("downstream"), list):
                for target in component["downstream"]:
                    if isinstance(target, str):
                        component_edges.add((source, target))
        graph_edge_set = set(edges)
        for edge in sorted(graph_edge_set - component_edges):
            warnings.append(f"graph edge not present in component downstream: {edge[0]} -> {edge[1]}")
        for edge in sorted(component_edges - graph_edge_set):
            warnings.append(f"component downstream not present in graph edges: {edge[0]} -> {edge[1]}")

    if references:
        print("\nVariable references:")
        for component_id in sorted(references):
            print(f"- {component_id}: " + ", ".join(sorted(references[component_id])))
    else:
        print("\nVariable references: (none found)")

    if aliases:
        print("\nIteration aliases:")
        for component_id in sorted(aliases):
            print(f"- {component_id}: " + ", ".join(sorted(aliases[component_id])))

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("\nWarnings: none")

    if warnings and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
