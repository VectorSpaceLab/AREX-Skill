#!/usr/bin/env python3
"""NaMI graph inversion for small Bayesian-network structures."""

from __future__ import annotations

import argparse
import itertools
import json
from collections import defaultdict, deque


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


def assert_acyclic(parents):
    parents = normalize_parents(parents)
    children = children_from_parents(parents)
    indegree = {node: len(parents[node]) for node in parents}
    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    visited = []
    while queue:
        node = queue.popleft()
        visited.append(node)
        for child in children.get(node, []):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(visited) != len(parents):
        raise ValueError("generative graph must be acyclic")


def moralize(parents):
    parents = normalize_parents(parents)
    neighbors = {node: set() for node in parents}
    for child, par_list in parents.items():
        for parent in par_list:
            neighbors[child].add(parent)
            neighbors[parent].add(child)
        for left, right in itertools.combinations(par_list, 2):
            neighbors[left].add(right)
            neighbors[right].add(left)
    return neighbors


def missing_fill_edges(neighbors, unmarked_neighbors):
    missing = []
    for left, right in itertools.combinations(sorted(unmarked_neighbors), 2):
        if right not in neighbors[left]:
            missing.append([left, right])
    return missing


def latent_upstream(node, parents, children, latents, mode):
    if mode == "topological":
        return [value for value in parents[node] if value in latents]
    if mode == "reverse_topological":
        return [value for value in children.get(node, []) if value in latents]
    raise ValueError("mode must be topological or reverse_topological")


def latent_downstream(node, parents, children, latents, mode):
    if mode == "topological":
        return [value for value in children.get(node, []) if value in latents]
    if mode == "reverse_topological":
        return [value for value in parents[node] if value in latents]
    raise ValueError("mode must be topological or reverse_topological")


def choose_min_fill(frontier, neighbors, marked):
    candidates = []
    for node in sorted(frontier):
        unmarked_neighbors = sorted(neighbors[node] - marked)
        fill_edges = missing_fill_edges(neighbors, unmarked_neighbors)
        candidates.append((len(fill_edges), node, fill_edges, unmarked_neighbors))
    _, node, fill_edges, unmarked_neighbors = min(candidates)
    return node, fill_edges, unmarked_neighbors


def nami_invert(parents, latents, observed, mode="topological"):
    parents = normalize_parents(parents)
    assert_acyclic(parents)
    latents = set(latents)
    observed = set(observed)
    unknown = (latents | observed) - set(parents)
    if unknown:
        raise ValueError("unknown variables: " + ", ".join(sorted(unknown)))
    if latents & observed:
        raise ValueError("latents and observed variables must be disjoint")

    children = children_from_parents(parents)
    neighbors = moralize(parents)
    marked = set()
    frontier = {
        node
        for node in latents
        if not latent_upstream(node, parents, children, latents, mode)
    }
    inverse_parents = {node: [] for node in sorted(latents)}
    trace = []
    elimination_order = []

    while frontier:
        selected, fill_edges, unmarked_neighbors = choose_min_fill(frontier, neighbors, marked)
        for left, right in fill_edges:
            neighbors[left].add(right)
            neighbors[right].add(left)
        inverse_parents[selected] = sorted(unmarked_neighbors)
        step = {
            "step": len(trace) + 1,
            "frontier_before": sorted(frontier),
            "selected": selected,
            "fill_edges": fill_edges,
            "inverse_parents": sorted(unmarked_neighbors),
            "mode": mode,
        }
        trace.append(step)
        elimination_order.append(selected)
        marked.add(selected)
        frontier.remove(selected)
        for candidate in latent_downstream(selected, parents, children, latents, mode):
            if candidate in marked:
                continue
            upstream = latent_upstream(candidate, parents, children, latents, mode)
            if all(item in marked for item in upstream):
                frontier.add(candidate)

    if marked != latents:
        missing = sorted(latents - marked)
        raise ValueError("frontier exhausted before all latents were eliminated: " + ", ".join(missing))

    return {
        "schema_version": 1,
        "mode": mode,
        "inverse_parents": inverse_parents,
        "elimination_order": elimination_order,
        "sampling_order": list(reversed(elimination_order)),
        "edge_count": sum(len(values) for values in inverse_parents.values()),
        "trace": trace,
    }


def binary_tree_parents(depth):
    if depth < 2:
        raise ValueError("depth must be at least 2")
    node_count = 2 ** depth - 1
    parents = {}
    for index in range(node_count):
        node = f"x{index}"
        if index == 0:
            parents[node] = []
        else:
            parents[node] = [f"x{(index - 1) // 2}"]
    first_leaf = 2 ** (depth - 1) - 1
    latents = [f"x{i}" for i in range(first_leaf)]
    observed = [f"x{i}" for i in range(first_leaf, node_count)]
    return parents, latents, observed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="", help="JSON file with parents, latents, observed, and optional mode.")
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    parser.add_argument("--mode", choices=["topological", "reverse_topological"], default="topological")
    parser.add_argument("--example", choices=["", "binary_tree"], default="")
    parser.add_argument("--depth", type=int, default=3)
    args = parser.parse_args(argv)

    if args.example == "binary_tree":
        parents, latents, observed = binary_tree_parents(args.depth)
        mode = args.mode
    elif args.input:
        with open(args.input, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        parents = data["parents"]
        latents = data["latents"]
        observed = data.get("observed", [])
        mode = data.get("mode", args.mode)
    else:
        parser.error("provide --input or --example binary_tree")

    result = nami_invert(parents, latents, observed, mode=mode)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
