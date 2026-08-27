#!/usr/bin/env python3
"""Safe TaskBench graph generation, sampling, and visualization helpers.

The native TaskBench graph scripts use implicit output locations. This helper
requires explicit input/output paths and performs no network or credential work.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple


Graph = Dict[str, Any]
Link = Dict[str, Any]


def fail(message: str, code: int = 2) -> None:
    print(json.dumps({"ok": False, "error": message}, indent=2), file=sys.stderr)
    raise SystemExit(code)


def read_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        fail(f"input file does not exist: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def require_nodes(obj: Any, source: Path) -> List[Dict[str, Any]]:
    if not isinstance(obj, dict):
        fail(f"{source} must contain a JSON object")
    nodes = obj.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        fail(f"{source} must contain a non-empty 'nodes' list")
    ids: set[str] = set()
    for idx, node in enumerate(nodes):
        if not isinstance(node, dict):
            fail(f"node {idx} in {source} is not an object")
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id.strip():
            fail(f"node {idx} in {source} has no string id")
        if node_id in ids:
            fail(f"duplicate node id in {source}: {node_id}")
        ids.add(node_id)
    return nodes


def compact_node(node: Dict[str, Any], dependency_type: str) -> Dict[str, Any]:
    base = {"id": node["id"], "desc": node.get("desc", "")}
    if dependency_type == "resource":
        for field in ("input-type", "output-type"):
            value = node.get(field)
            if not isinstance(value, list):
                fail(f"resource node {node['id']!r} must have list field {field!r}")
            base[field] = value
    else:
        params = node.get("parameters")
        if not isinstance(params, list):
            fail(f"temporal node {node['id']!r} must have list field 'parameters'")
        base["parameters"] = params
        if "input-type" in node:
            base["input-type"] = node.get("input-type")
        if "output-type" in node:
            base["output-type"] = node.get("output-type")
    return base


def generate_graph(args: argparse.Namespace) -> None:
    source = Path(args.input)
    target = Path(args.output)
    obj = read_json(source)
    nodes_in = require_nodes(obj, source)
    nodes = [compact_node(node, args.dependency_type) for node in nodes_in]

    links: List[Link] = []
    if args.dependency_type == "resource":
        for src in nodes:
            src_outputs = set(str(x) for x in src.get("output-type", []))
            for dst in nodes:
                if src["id"] == dst["id"]:
                    continue
                dst_inputs = set(str(x) for x in dst.get("input-type", []))
                shared = sorted(src_outputs.intersection(dst_inputs))
                if shared:
                    links.append({"source": src["id"], "target": dst["id"], "type": shared[0]})
    else:
        for src in nodes:
            for dst in nodes:
                if src["id"] != dst["id"]:
                    links.append({"source": src["id"], "target": dst["id"], "type": "complete"})

    graph = {"nodes": nodes, "links": links}
    write_json(target, graph)
    print(json.dumps({
        "ok": True,
        "command": "generate-graph",
        "dependency_type": args.dependency_type,
        "input": str(source),
        "output": str(target),
        "nodes": len(nodes),
        "links": len(links),
    }, indent=2))


def load_graph(path: Path) -> Tuple[List[Dict[str, Any]], List[Link]]:
    obj = read_json(path)
    nodes = require_nodes(obj, path)
    links = obj.get("links")
    if not isinstance(links, list):
        fail(f"{path} must contain a 'links' list")
    node_ids = {node["id"] for node in nodes}
    for idx, link in enumerate(links):
        if not isinstance(link, dict):
            fail(f"link {idx} in {path} is not an object")
        source = link.get("source")
        target = link.get("target")
        if source not in node_ids or target not in node_ids:
            fail(f"link {idx} references unknown node: {source!r} -> {target!r}")
        if "type" not in link:
            link["type"] = "complete"
    return nodes, links


def infer_dependency_type(nodes: Sequence[Dict[str, Any]]) -> str:
    first = nodes[0]
    if "input-type" in first and "output-type" in first:
        return "resource"
    if "parameters" in first:
        return "temporal"
    return "unknown"


def validate_requested_type(nodes: Sequence[Dict[str, Any]], requested: str) -> str:
    inferred = infer_dependency_type(nodes)
    if requested != "auto" and inferred != "unknown" and requested != inferred:
        fail(f"requested dependency type {requested!r} does not match graph node schema {inferred!r}")
    return inferred if requested == "auto" else requested


def adjacency(links: Sequence[Link]) -> Tuple[Dict[str, List[Tuple[str, Link]]], Dict[str, List[Tuple[str, Link]]]]:
    succ: Dict[str, List[Tuple[str, Link]]] = {}
    pred: Dict[str, List[Tuple[str, Link]]] = {}
    for link in links:
        source = str(link["source"])
        target = str(link["target"])
        succ.setdefault(source, []).append((target, link))
        pred.setdefault(target, []).append((source, link))
    return succ, pred


def link_key(source: str, target: str) -> Tuple[str, str]:
    return (source, target)


def sample_single(node_ids: Sequence[str], rng: random.Random) -> Tuple[List[str], List[Tuple[str, str]]]:
    return [rng.choice(list(node_ids))], []


def sample_chain(node_ids: Sequence[str], links: Sequence[Link], num_nodes: int, rng: random.Random) -> Tuple[List[str], List[Tuple[str, str]]]:
    succ, pred = adjacency(links)
    selected = [rng.choice(list(node_ids))]
    chosen_edges: List[Tuple[str, str]] = []
    attempts = 0
    max_attempts = max(20, len(node_ids) * 6)
    while len(selected) < num_nodes and attempts < max_attempts:
        attempts += 1
        head = selected[0]
        tail = selected[-1]
        candidates: List[Tuple[str, str, str]] = []
        candidates.extend(("prepend", other, head) for other, _ in pred.get(head, []))
        candidates.extend(("append", tail, other) for other, _ in succ.get(tail, []))
        rng.shuffle(candidates)
        added = False
        for direction, source, target in candidates:
            new_node = source if direction == "prepend" else target
            if new_node in selected:
                continue
            if direction == "prepend":
                selected.insert(0, new_node)
            else:
                selected.append(new_node)
            chosen_edges.append((source, target))
            added = True
            break
        if not added:
            remaining = [node for node in node_ids if node not in selected]
            if not remaining:
                break
            # Preserve explicit output rather than failing on sparse graphs: add
            # an isolated node and leave the sample visibly disconnected.
            selected.append(rng.choice(remaining))
    return selected, chosen_edges


def sample_dag(node_ids: Sequence[str], links: Sequence[Link], num_nodes: int, rng: random.Random) -> Tuple[List[str], List[Tuple[str, str]]]:
    succ, pred = adjacency(links)
    selected = [rng.choice(list(node_ids))]
    chosen_edges: List[Tuple[str, str]] = []
    attempts = 0
    max_attempts = max(30, len(node_ids) * 8)
    while len(selected) < num_nodes and attempts < max_attempts:
        attempts += 1
        base = rng.choice(selected)
        candidates: List[Tuple[str, str, str]] = []
        candidates.extend(("pred", other, base) for other, _ in pred.get(base, []))
        candidates.extend(("succ", base, other) for other, _ in succ.get(base, []))
        rng.shuffle(candidates)
        added = False
        for _direction, source, target in candidates:
            new_node = source if source not in selected else target
            if new_node in selected:
                continue
            selected.append(new_node)
            chosen_edges.append((source, target))
            added = True
            break
        if not added:
            remaining = [node for node in node_ids if node not in selected]
            if not remaining:
                break
            selected.append(rng.choice(remaining))
    return selected, chosen_edges


def sample_graph(args: argparse.Namespace) -> None:
    source = Path(args.input)
    target = Path(args.output)
    nodes, links = load_graph(source)
    dependency_type = validate_requested_type(nodes, args.dependency_type)
    node_by_id = {node["id"]: node for node in nodes}
    node_ids = list(node_by_id)
    if args.num_nodes < 1:
        fail("--num-nodes must be at least 1")
    num_nodes = min(args.num_nodes, len(node_ids))
    rng = random.Random(args.seed)

    if args.method == "single":
        selected, chosen_edge_keys = sample_single(node_ids, rng)
    elif args.method == "chain":
        selected, chosen_edge_keys = sample_chain(node_ids, links, num_nodes, rng)
    elif args.method == "dag":
        selected, chosen_edge_keys = sample_dag(node_ids, links, num_nodes, rng)
    else:
        fail(f"unsupported sample method: {args.method}")

    selected_set = set(selected)
    link_lookup = {link_key(str(link["source"]), str(link["target"])): link for link in links}
    sampled_links: List[Link] = []
    seen_edges: set[Tuple[str, str]] = set()
    for source_id, target_id in chosen_edge_keys:
        if source_id in selected_set and target_id in selected_set and (source_id, target_id) not in seen_edges:
            sampled_links.append(dict(link_lookup.get((source_id, target_id), {"source": source_id, "target": target_id, "type": "complete"})))
            seen_edges.add((source_id, target_id))

    sampled = {
        "nodes": [node_by_id[node_id] for node_id in selected],
        "links": sampled_links,
    }
    write_json(target, sampled)
    print(json.dumps({
        "ok": True,
        "command": "sample-graph",
        "dependency_type": dependency_type,
        "method": args.method,
        "seed": args.seed,
        "input": str(source),
        "output": str(target),
        "nodes": len(sampled["nodes"]),
        "links": len(sampled["links"]),
        "disconnected": len(sampled["nodes"]) > 1 and len(sampled["links"]) == 0,
    }, indent=2))


def circular_layout(node_ids: Sequence[str]) -> Dict[str, Tuple[float, float]]:
    total = max(1, len(node_ids))
    positions: Dict[str, Tuple[float, float]] = {}
    for idx, node_id in enumerate(node_ids):
        angle = 2.0 * math.pi * idx / total
        positions[node_id] = (math.cos(angle), math.sin(angle))
    return positions


def visualize(args: argparse.Namespace) -> None:
    source = Path(args.input)
    target = Path(args.output)
    nodes, links = load_graph(source)
    validate_requested_type(nodes, args.dependency_type)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - depends on local environment
        fail(f"matplotlib is required for visualization: {exc}")

    node_ids = [node["id"] for node in nodes]
    positions = circular_layout(node_ids)
    count = len(node_ids)
    size = min(24.0, max(6.0, math.sqrt(max(count, 1)) * 2.0))
    fig, ax = plt.subplots(figsize=(size, size), dpi=120)
    ax.set_title(args.title or "TaskBench graph")
    ax.axis("off")

    xs = [positions[node_id][0] for node_id in node_ids]
    ys = [positions[node_id][1] for node_id in node_ids]
    ax.scatter(xs, ys, s=max(80, 5000 // max(count, 1)), c="#87ceeb", edgecolors="#225577", zorder=3)

    if count <= args.max_labels:
        for node_id, (x, y) in positions.items():
            ax.text(x, y, node_id, fontsize=max(5, min(10, 180 // max(count, 1))), ha="center", va="center", zorder=4)

    for link in links:
        source_id = str(link["source"])
        target_id = str(link["target"])
        if source_id not in positions or target_id not in positions:
            continue
        x1, y1 = positions[source_id]
        x2, y2 = positions[target_id]
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops={"arrowstyle": "->", "color": "#666666", "lw": 0.7, "alpha": 0.55, "shrinkA": 8, "shrinkB": 8},
            zorder=2,
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(target)
    plt.close(fig)
    print(json.dumps({
        "ok": True,
        "command": "visualize",
        "input": str(source),
        "output": str(target),
        "nodes": len(nodes),
        "links": len(links),
        "labels_drawn": len(nodes) <= args.max_labels,
    }, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe TaskBench graph tools with explicit output paths.")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate-graph", help="Generate graph_desc.json from tool_desc.json.")
    gen.add_argument("--input", required=True, help="Input tool_desc.json path.")
    gen.add_argument("--output", required=True, help="Output graph_desc.json path.")
    gen.add_argument("--dependency-type", required=True, choices=["resource", "temporal"], help="Graph dependency type.")
    gen.set_defaults(func=generate_graph)

    sample = sub.add_parser("sample-graph", help="Sample a small subgraph fixture from graph_desc.json.")
    sample.add_argument("--input", required=True, help="Input graph_desc.json path.")
    sample.add_argument("--output", required=True, help="Output sampled graph_desc.json path.")
    sample.add_argument("--dependency-type", default="auto", choices=["auto", "resource", "temporal"], help="Validate graph node schema against this dependency type.")
    sample.add_argument("--method", default="chain", choices=["single", "chain", "dag"], help="Sampling method.")
    sample.add_argument("--num-nodes", type=int, default=3, help="Maximum number of nodes to sample.")
    sample.add_argument("--seed", type=int, default=0, help="Deterministic random seed.")
    sample.set_defaults(func=sample_graph)

    vis = sub.add_parser("visualize", help="Create a headless graph visualization.")
    vis.add_argument("--input", required=True, help="Input graph_desc.json path.")
    vis.add_argument("--output", required=True, help="Output image path such as .png, .pdf, or .svg.")
    vis.add_argument("--dependency-type", default="auto", choices=["auto", "resource", "temporal"], help="Validate graph node schema against this dependency type.")
    vis.add_argument("--title", default="TaskBench graph", help="Figure title.")
    vis.add_argument("--max-labels", type=int, default=80, help="Hide labels when graph has more nodes than this value.")
    vis.set_defaults(func=visualize)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
