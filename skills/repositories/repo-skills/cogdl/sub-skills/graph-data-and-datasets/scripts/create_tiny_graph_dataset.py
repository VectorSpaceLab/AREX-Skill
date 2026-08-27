#!/usr/bin/env python3
"""Create deterministic tiny CogDL dataset artifacts with no network access.

The script writes one node-classification Graph artifact and/or one graph-
classification list-of-Graph artifact under a user-selected output directory.
It then validates the artifacts through CogDL's NodeDataset, GraphDataset, and
DataLoader APIs unless --skip-load-validation is supplied.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import torch


def _cogdl_classes():
    from cogdl.data import Adjacency, DataLoader, Graph
    from cogdl.datasets import GraphDataset, NodeDataset

    return Adjacency, DataLoader, Graph, GraphDataset, NodeDataset


def _register_cogdl_safe_globals() -> None:
    """Allow safe loading of CogDL Graph pickles on supported PyTorch versions."""

    Adjacency, _, Graph, _, _ = _cogdl_classes()
    serialization = getattr(torch, "serialization", None)
    add_safe_globals = getattr(serialization, "add_safe_globals", None)
    if add_safe_globals is None:
        return
    try:
        add_safe_globals([Graph, Adjacency])
    except Exception:
        pass


def build_node_graph():
    """Return a deterministic six-node classification graph."""

    _, _, Graph, _, _ = _cogdl_classes()
    edge_index = torch.tensor(
        [[0, 1, 2, 3, 4, 5, 0, 2, 4, 1, 3, 5], [1, 2, 3, 4, 5, 0, 2, 4, 0, 3, 1, 4]],
        dtype=torch.long,
    )
    x = torch.arange(6 * 4, dtype=torch.float32).view(6, 4) / 10.0
    y = torch.tensor([0, 1, 0, 1, 2, 2], dtype=torch.long)
    train_mask = torch.tensor([True, True, False, False, False, False])
    val_mask = torch.tensor([False, False, True, True, False, False])
    test_mask = torch.tensor([False, False, False, False, True, True])
    return Graph(x=x, edge_index=edge_index, y=y, train_mask=train_mask, val_mask=val_mask, test_mask=test_mask)


def build_graphs() -> List[object]:
    """Return deterministic graph-classification examples with local node ids."""

    _, _, Graph, _, _ = _cogdl_classes()
    graphs = [
        Graph(
            x=torch.eye(4, dtype=torch.float32),
            edge_index=torch.tensor([[0, 1, 2, 3, 1, 2, 3, 0], [1, 2, 3, 0, 0, 1, 2, 3]], dtype=torch.long),
            y=torch.tensor([0], dtype=torch.long),
        ),
        Graph(
            x=torch.tensor(
                [[1.0, 0.0, 0.5, 0.2], [0.5, 1.0, 0.0, 0.3], [0.0, 0.5, 1.0, 0.4]],
                dtype=torch.float32,
            ),
            edge_index=torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]], dtype=torch.long),
            y=torch.tensor([1], dtype=torch.long),
        ),
        Graph(
            x=torch.arange(5 * 4, dtype=torch.float32).view(5, 4) / 10.0,
            edge_index=torch.tensor([[0, 0, 0, 0, 1, 2, 3, 4], [1, 2, 3, 4, 0, 0, 0, 0]], dtype=torch.long),
            y=torch.tensor([0], dtype=torch.long),
        ),
    ]
    return graphs


def _edge_parts(graph) -> Tuple[torch.Tensor, torch.Tensor]:
    row, col = graph.edge_index
    if not torch.is_tensor(row) or not torch.is_tensor(col):
        raise ValueError("edge_index must contain tensors")
    if row.ndim != 1 or col.ndim != 1 or row.numel() != col.numel():
        raise ValueError("edge_index row/col must be equal-length 1-D tensors")
    if row.dtype != torch.long or col.dtype != torch.long:
        raise ValueError("edge_index row/col must use torch.long dtype")
    return row, col


def validate_node_graph(graph) -> Dict[str, object]:
    """Validate the node-classification graph and return a JSON-ready summary."""

    _, _, Graph, _, _ = _cogdl_classes()
    if not isinstance(graph, Graph):
        raise TypeError(f"expected Graph, got {type(graph)!r}")
    if not torch.is_tensor(graph.x):
        raise ValueError("node graph x must be a tensor")
    if not torch.is_tensor(graph.y):
        raise ValueError("node graph y must be a tensor")
    num_nodes = int(graph.num_nodes)
    if graph.x.shape[0] != num_nodes:
        raise ValueError("x first dimension must equal num_nodes")
    if graph.y.shape[0] != num_nodes:
        raise ValueError("y first dimension must equal num_nodes")
    row, col = _edge_parts(graph)
    if row.numel() == 0:
        raise ValueError("tiny node graph unexpectedly has no edges")
    endpoints = torch.cat([row, col])
    if int(endpoints.min().item()) < 0:
        raise ValueError("edge_index contains negative node ids")
    if int(endpoints.max().item()) >= num_nodes:
        raise ValueError("edge_index contains node ids outside num_nodes")

    mask_summary: Dict[str, int] = {}
    combined = torch.zeros(num_nodes, dtype=torch.bool)
    for split in ("train", "val", "test"):
        mask = getattr(graph, f"{split}_mask", None)
        if not torch.is_tensor(mask) or mask.dtype != torch.bool or mask.numel() != num_nodes:
            raise ValueError(f"{split}_mask must be a bool tensor of length num_nodes")
        if torch.any(combined & mask):
            raise ValueError("train/val/test masks must be disjoint")
        combined |= mask
        mask_summary[split] = int(mask.sum().item())

    return {
        "num_nodes": num_nodes,
        "num_edges": int(row.numel()),
        "num_features": int(graph.num_features),
        "num_classes": int(graph.num_classes),
        "mask_counts": mask_summary,
    }


def validate_graph_list(graphs: List[object]) -> Dict[str, object]:
    """Validate graph-classification examples and return a JSON-ready summary."""

    _, _, Graph, _, _ = _cogdl_classes()
    if not graphs:
        raise ValueError("graph list is empty")
    node_counts: List[int] = []
    edge_counts: List[int] = []
    labels: List[int] = []
    for idx, graph in enumerate(graphs):
        if not isinstance(graph, Graph):
            raise TypeError(f"item {idx} is not a Graph")
        if not torch.is_tensor(graph.y) or graph.y.numel() != 1:
            raise ValueError(f"graph {idx} must have one graph-level label")
        row, col = _edge_parts(graph)
        num_nodes = int(graph.num_nodes)
        if graph.x is not None and graph.x.shape[0] != num_nodes:
            raise ValueError(f"graph {idx} x first dimension must equal num_nodes")
        if row.numel() > 0:
            endpoints = torch.cat([row, col])
            if int(endpoints.min().item()) < 0 or int(endpoints.max().item()) >= num_nodes:
                raise ValueError(f"graph {idx} contains out-of-range local node ids")
        node_counts.append(num_nodes)
        edge_counts.append(int(row.numel()))
        labels.append(int(graph.y.view(-1)[0].item()))
    return {
        "num_graphs": len(graphs),
        "node_counts": node_counts,
        "edge_counts": edge_counts,
        "labels": labels,
    }


def save_artifact(obj: object, path: Path, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(obj, path)


def validate_loaded_node_dataset(path: Path) -> Dict[str, object]:
    _register_cogdl_safe_globals()
    _, _, _, _, NodeDataset = _cogdl_classes()
    dataset = NodeDataset(path=str(path), data=None, scale_feat=False, metric="accuracy")
    graph = dataset[0]
    summary = validate_node_graph(graph)
    summary["dataset_repr"] = repr(dataset)
    summary["metric"] = dataset.metric
    return summary


def validate_loaded_graph_dataset(path: Path) -> Dict[str, object]:
    _register_cogdl_safe_globals()
    _, DataLoader, _, GraphDataset, _ = _cogdl_classes()
    dataset = GraphDataset(path=str(path), metric="accuracy")
    list_summary = validate_graph_list([dataset[i] for i in range(len(dataset))])
    loader = DataLoader(dataset, batch_size=min(2, len(dataset)), shuffle=False)
    batch = next(iter(loader))
    list_summary["dataset_len"] = int(len(dataset))
    list_summary["batch_num_nodes"] = int(batch.num_nodes)
    list_summary["batch_num_graphs"] = int(batch.num_graphs)
    list_summary["batch_vector_len"] = int(batch.batch.numel())
    return list_summary


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create deterministic no-download CogDL NodeDataset/GraphDataset artifacts.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory where tiny dataset artifacts will be written.")
    parser.add_argument("--kind", choices=("node", "graph", "both"), default="both", help="Which artifact type to create. Default: both.")
    parser.add_argument("--node-file", default="tiny_node_data.pt", help="Filename for the node-classification Graph artifact.")
    parser.add_argument("--graph-file", default="tiny_graph_data.pt", help="Filename for the graph-classification list artifact.")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting existing artifact files in --output-dir.")
    parser.add_argument("--skip-load-validation", action="store_true", help="Only write files; skip reloading through CogDL dataset classes.")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    _register_cogdl_safe_globals()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    result: Dict[str, object] = {"created": {}, "validation": {}}

    if args.kind in ("node", "both"):
        node_path = args.output_dir / args.node_file
        node_graph = build_node_graph()
        result["validation"]["node_before_save"] = validate_node_graph(node_graph)
        save_artifact(node_graph, node_path, args.overwrite)
        result["created"]["node_path"] = str(node_path)
        if not args.skip_load_validation:
            result["validation"]["node_loaded"] = validate_loaded_node_dataset(node_path)

    if args.kind in ("graph", "both"):
        graph_path = args.output_dir / args.graph_file
        graphs = build_graphs()
        result["validation"]["graph_list_before_save"] = validate_graph_list(graphs)
        save_artifact(graphs, graph_path, args.overwrite)
        result["created"]["graph_path"] = str(graph_path)
        if not args.skip_load_validation:
            result["validation"]["graph_dataset_loaded"] = validate_loaded_graph_dataset(graph_path)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - user-facing CLI guard
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
