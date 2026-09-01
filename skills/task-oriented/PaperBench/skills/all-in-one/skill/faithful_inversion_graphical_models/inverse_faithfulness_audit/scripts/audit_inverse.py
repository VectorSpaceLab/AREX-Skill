#!/usr/bin/env python3
"""Audit naturalness and local I-map evidence for inverse BN structures."""

from __future__ import annotations

import argparse
import itertools
import json
from collections import defaultdict


def normalize_parents(parents):
    nodes = set(parents)
    for values in parents.values():
        nodes.update(values)
    return {node: sorted(set(parents.get(node, []))) for node in sorted(nodes)}


def children_from_parents(parents):
    children = {node: [] for node in parents}
    for child, par_list in parents.items():
        for parent in par_list:
            children.setdefault(parent, []).append(child)
    return {node: sorted(values) for node, values in children.items()}


def descendants_of(node, children):
    seen = set()
    stack = list(children.get(node, []))
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(children.get(current, []))
    return seen


def ancestors_of(node, parents):
    seen = set()
    stack = list(parents.get(node, []))
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(parents.get(current, []))
    return seen


def undirected_neighbors(parents):
    neighbors = {node: set() for node in parents}
    for child, par_list in parents.items():
        for parent in par_list:
            neighbors[child].add(parent)
            neighbors[parent].add(child)
    return neighbors


def all_simple_paths(neighbors, start, goal):
    stack = [(start, [start])]
    while stack:
        node, path = stack.pop()
        for next_node in sorted(neighbors.get(node, [])):
            if next_node in path:
                continue
            new_path = path + [next_node]
            if next_node == goal:
                yield new_path
            else:
                stack.append((next_node, new_path))


def has_conditioned_descendant(node, conditioned, children):
    return bool(descendants_of(node, children) & conditioned)


def path_is_active(path, parents, children, conditioned):
    conditioned = set(conditioned)
    for index in range(1, len(path) - 1):
        left = path[index - 1]
        middle = path[index]
        right = path[index + 1]
        collider = left in parents.get(middle, []) and right in parents.get(middle, [])
        if collider:
            if middle not in conditioned and not has_conditioned_descendant(middle, conditioned, children):
                return False
        elif middle in conditioned:
            return False
    return True


def d_separated(parents, left, right, conditioned):
    parents = normalize_parents(parents)
    children = children_from_parents(parents)
    neighbors = undirected_neighbors(parents)
    for path in all_simple_paths(neighbors, left, right):
        if path_is_active(path, parents, children, set(conditioned)):
            return False
    return True


def inverse_children(inverse_parents):
    children = defaultdict(list)
    for child, par_list in inverse_parents.items():
        for parent in par_list:
            children[parent].append(child)
    return {node: sorted(values) for node, values in children.items()}


def inverse_descendants(node, inverse_parents):
    return descendants_of(node, inverse_children(inverse_parents))


def audit_inverse(parents, inverse_parents, latents, observed, mode="topological"):
    parents = normalize_parents(parents)
    inverse_parents = {node: sorted(set(values)) for node, values in inverse_parents.items()}
    latents = set(latents)
    observed = set(observed)
    nodes = set(parents)
    children = children_from_parents(parents)
    issues = []

    for variable in inverse_parents:
        if variable not in latents:
            issues.append({"check": "factor_variable_is_not_latent", "variable": variable})
    for variable, par_list in inverse_parents.items():
        for parent in par_list:
            if parent not in nodes:
                issues.append({"check": "unknown_inverse_parent", "variable": variable, "parent": parent})

    natural_issues = []
    for child, par_list in inverse_parents.items():
        for parent in par_list:
            if mode == "topological" and child in descendants_of(parent, children):
                natural_issues.append({"child": child, "parent": parent, "reason": "edge_from_ancestor_to_descendant"})
            if mode == "reverse_topological" and child in ancestors_of(parent, parents):
                natural_issues.append({"child": child, "parent": parent, "reason": "edge_from_descendant_to_ancestor"})
    issues.extend({"check": "naturalness", **item} for item in natural_issues)

    local_issues = []
    all_nodes = set(parents)
    for variable, par_list in inverse_parents.items():
        descendants = inverse_descendants(variable, inverse_parents)
        non_descendants = all_nodes - descendants - {variable}
        for other in sorted(non_descendants - set(par_list)):
            if not d_separated(parents, variable, other, par_list):
                local_issues.append({
                    "variable": variable,
                    "other": other,
                    "conditioned_on": sorted(par_list),
                    "reason": "inverse_asserts_unsupported_local_independence",
                })
    issues.extend({"check": "local_imap", **item} for item in local_issues)

    minimality_issues = []
    checked_edges = 0
    for variable, par_list in inverse_parents.items():
        for parent in par_list:
            checked_edges += 1
            reduced_conditioning = [item for item in par_list if item != parent]
            if d_separated(parents, variable, parent, reduced_conditioning):
                minimality_issues.append({
                    "variable": variable,
                    "parent": parent,
                    "conditioned_on": sorted(reduced_conditioning),
                    "reason": "edge_removal_still_d_separated",
                })
    issues.extend({"check": "minimality", **item} for item in minimality_issues)

    report = {
        "schema_version": 1,
        "mode": mode,
        "ok": not issues,
        "natural_ok": not natural_issues,
        "local_imap_ok": not local_issues,
        "minimality_ok": not minimality_issues,
        "checked_edges": checked_edges,
        "issues": issues,
    }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON input with parents, inverse_parents, latents, observed, and mode.")
    parser.add_argument("--output", default="")
    args = parser.parse_args(argv)
    with open(args.input, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    report = audit_inverse(
        data["parents"],
        data["inverse_parents"],
        data["latents"],
        data.get("observed", []),
        data.get("mode", "topological"),
    )
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
