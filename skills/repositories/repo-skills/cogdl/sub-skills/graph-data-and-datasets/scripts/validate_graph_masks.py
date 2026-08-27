#!/usr/bin/env python3
"""Validate a saved CogDL node-classification Graph fixture.

The validator checks node features, labels, COO edge_index, optional edge
attributes/weights, and train/validation/test masks. It only depends on an
installed CogDL package and does not download datasets or run training.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import torch


def _cogdl_classes():
    from cogdl.data import Adjacency, Graph
    from cogdl.datasets import NodeDataset

    return Adjacency, Graph, NodeDataset


def _register_cogdl_safe_globals() -> None:
    serialization = getattr(torch, "serialization", None)
    add_safe_globals = getattr(serialization, "add_safe_globals", None)
    if add_safe_globals is None:
        return
    Adjacency, Graph, _ = _cogdl_classes()
    try:
        add_safe_globals([Graph, Adjacency])
    except Exception:
        pass


def _trusted_torch_load(path: Path, trust_pickle: bool) -> object:
    _register_cogdl_safe_globals()
    try:
        return torch.load(path, map_location="cpu")
    except Exception as exc:
        if not trust_pickle:
            raise RuntimeError(
                "torch.load could not safely load this file. If it is a trusted "
                "CogDL artifact, rerun with --trust-pickle. Original error: "
                f"{exc}"
            ) from exc
        try:
            return torch.load(path, map_location="cpu", weights_only=False)
        except TypeError:
            return torch.load(path, map_location="cpu")


def load_graph(path: Path, mode: str, trust_pickle: bool):
    """Load a Graph either directly or through NodeDataset."""

    _, Graph, NodeDataset = _cogdl_classes()
    errors: List[str] = []
    if mode in ("auto", "graph"):
        try:
            obj = _trusted_torch_load(path, trust_pickle)
            if isinstance(obj, Graph):
                return obj, "graph"
            errors.append(f"direct load returned {type(obj).__name__}, not Graph")
        except Exception as exc:
            errors.append(f"direct graph load failed: {exc}")
            if mode == "graph":
                raise

    if mode in ("auto", "node-dataset"):
        try:
            _register_cogdl_safe_globals()
            dataset = NodeDataset(path=str(path), scale_feat=False)
            graph = dataset[0]
            if isinstance(graph, Graph):
                return graph, "node-dataset"
            errors.append(f"NodeDataset returned {type(graph).__name__}, not Graph")
        except Exception as exc:
            errors.append(f"NodeDataset load failed: {exc}")
            if mode == "node-dataset":
                raise

    raise RuntimeError("; ".join(errors))


def normalize_edge_index(graph, errors: List[str], warnings: List[str]) -> Tuple[torch.Tensor, torch.Tensor]:
    try:
        edge_index = graph.edge_index
    except Exception as exc:
        errors.append(f"edge_index is missing or unreadable: {exc}")
        return torch.empty(0, dtype=torch.long), torch.empty(0, dtype=torch.long)

    if isinstance(edge_index, torch.Tensor):
        if edge_index.ndim != 2 or edge_index.shape[0] != 2:
            errors.append(f"edge_index tensor must have shape [2, E], got {tuple(edge_index.shape)}")
            return torch.empty(0, dtype=torch.long), torch.empty(0, dtype=torch.long)
        row, col = edge_index[0], edge_index[1]
    elif isinstance(edge_index, (tuple, list)) and len(edge_index) == 2:
        row, col = edge_index
    else:
        errors.append("edge_index must be a [2, E] tensor or a (row, col) pair")
        return torch.empty(0, dtype=torch.long), torch.empty(0, dtype=torch.long)

    if not torch.is_tensor(row) or not torch.is_tensor(col):
        errors.append("edge_index row and col must be tensors")
        return torch.empty(0, dtype=torch.long), torch.empty(0, dtype=torch.long)
    if row.ndim != 1 or col.ndim != 1:
        errors.append(f"edge_index row/col must be 1-D, got {tuple(row.shape)} and {tuple(col.shape)}")
    if row.numel() != col.numel():
        errors.append(f"edge_index row/col lengths differ: {row.numel()} vs {col.numel()}")
    if torch.is_floating_point(row) or torch.is_floating_point(col):
        errors.append("edge_index row/col must use integer dtype, not floating point")
    if row.dtype != torch.long:
        warnings.append(f"edge_index row dtype is {row.dtype}; torch.long is recommended")
    if col.dtype != torch.long:
        warnings.append(f"edge_index col dtype is {col.dtype}; torch.long is recommended")
    return row, col


def mask_to_bool(mask: torch.Tensor, split: str, num_nodes: int, bool_masks_only: bool, errors: List[str], warnings: List[str]) -> torch.Tensor:
    if mask.dtype == torch.bool:
        if mask.ndim != 1 or mask.numel() != num_nodes:
            errors.append(f"{split}_mask must be bool shape [{num_nodes}], got shape {tuple(mask.shape)}")
            return torch.zeros(num_nodes, dtype=torch.bool)
        return mask.cpu()

    if bool_masks_only:
        errors.append(f"{split}_mask must be boolean because --bool-masks-only was supplied")
        return torch.zeros(num_nodes, dtype=torch.bool)
    if torch.is_floating_point(mask) or mask.ndim != 1:
        errors.append(f"{split}_mask must be bool [{num_nodes}] or 1-D integer indices")
        return torch.zeros(num_nodes, dtype=torch.bool)
    if mask.numel() == 0:
        warnings.append(f"{split}_mask index tensor is empty")
        return torch.zeros(num_nodes, dtype=torch.bool)
    mask_long = mask.long().cpu()
    if int(mask_long.min().item()) < 0 or int(mask_long.max().item()) >= num_nodes:
        errors.append(f"{split}_mask contains node ids outside [0, {num_nodes - 1}]")
        return torch.zeros(num_nodes, dtype=torch.bool)
    unique_count = int(torch.unique(mask_long).numel())
    if unique_count != int(mask_long.numel()):
        warnings.append(f"{split}_mask contains duplicate node ids")
    out = torch.zeros(num_nodes, dtype=torch.bool)
    out[mask_long] = True
    return out


def validate_graph(graph, args: argparse.Namespace) -> Dict[str, object]:
    _, Graph, _ = _cogdl_classes()
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(graph, Graph):
        errors.append(f"object is {type(graph).__name__}, not cogdl.data.Graph")
        return {"ok": False, "errors": errors, "warnings": warnings}

    try:
        num_nodes = int(graph.num_nodes)
    except Exception as exc:
        errors.append(f"num_nodes is unavailable: {exc}")
        num_nodes = -1
    if num_nodes < 0:
        errors.append("num_nodes must be nonnegative")
        num_nodes = 0

    x = getattr(graph, "x", None)
    if x is None:
        if not args.allow_missing_x:
            errors.append("x is missing; pass --allow-missing-x only for featureless workflows")
        num_features = 0
    elif not torch.is_tensor(x):
        errors.append(f"x must be a torch.Tensor, got {type(x).__name__}")
        num_features = None
    else:
        if x.ndim == 0:
            errors.append("x must have at least one dimension")
        elif int(x.shape[0]) != num_nodes:
            errors.append(f"x first dimension {int(x.shape[0])} != num_nodes {num_nodes}")
        num_features = 1 if x.ndim == 1 else int(x.shape[1]) if x.ndim > 1 else None

    y = getattr(graph, "y", None)
    if y is None:
        errors.append("y labels are missing")
        num_classes = None
    elif not torch.is_tensor(y):
        errors.append(f"y must be a torch.Tensor, got {type(y).__name__}")
        num_classes = None
    else:
        if y.ndim == 0:
            errors.append("y must be node-aligned, not scalar")
        elif int(y.shape[0]) != num_nodes:
            errors.append(f"y first dimension {int(y.shape[0])} != num_nodes {num_nodes}")
        if y.numel() == 0:
            num_classes = 0
        elif y.ndim == 1:
            num_classes = int(torch.max(y).item()) + 1
        else:
            num_classes = int(y.shape[-1])

    row, col = normalize_edge_index(graph, errors, warnings)
    num_edges = int(min(row.numel(), col.numel()))
    if num_edges == 0:
        warnings.append("edge_index has no edges")
    if num_edges > 0 and num_nodes > 0:
        endpoints = torch.cat([row.long().cpu(), col.long().cpu()])
        if int(endpoints.min().item()) < 0:
            errors.append("edge_index contains negative node ids")
        if int(endpoints.max().item()) >= num_nodes:
            errors.append(f"edge_index contains ids >= num_nodes ({num_nodes})")

    adj = getattr(graph, "_adj", None)
    edge_weight = getattr(adj, "weight", None)
    edge_attr = getattr(adj, "attr", None)
    if edge_weight is not None and torch.is_tensor(edge_weight) and edge_weight.shape[0] != num_edges:
        errors.append(f"edge_weight length {edge_weight.shape[0]} != num_edges {num_edges}")
    if edge_attr is not None and torch.is_tensor(edge_attr) and edge_attr.shape[0] != num_edges:
        errors.append(f"edge_attr first dimension {edge_attr.shape[0]} != num_edges {num_edges}")

    bool_masks: Dict[str, torch.Tensor] = {}
    mask_counts: Dict[str, int] = {}
    for split in ("train", "val", "test"):
        mask = getattr(graph, f"{split}_mask", None)
        if mask is None:
            errors.append(f"{split}_mask is missing")
            bool_mask = torch.zeros(num_nodes, dtype=torch.bool)
        elif not torch.is_tensor(mask):
            errors.append(f"{split}_mask must be a torch.Tensor, got {type(mask).__name__}")
            bool_mask = torch.zeros(num_nodes, dtype=torch.bool)
        else:
            bool_mask = mask_to_bool(mask, split, num_nodes, args.bool_masks_only, errors, warnings)
        bool_masks[split] = bool_mask
        mask_counts[split] = int(bool_mask.sum().item())
        if mask_counts[split] == 0:
            warnings.append(f"{split}_mask selects no nodes")

    if not args.allow_overlap and num_nodes > 0:
        overlaps = {
            "train_val": int((bool_masks["train"] & bool_masks["val"]).sum().item()),
            "train_test": int((bool_masks["train"] & bool_masks["test"]).sum().item()),
            "val_test": int((bool_masks["val"] & bool_masks["test"]).sum().item()),
        }
        bad = {key: value for key, value in overlaps.items() if value}
        if bad:
            errors.append(f"split masks overlap: {bad}")

    covered = bool_masks["train"] | bool_masks["val"] | bool_masks["test"]
    covered_count = int(covered.sum().item()) if num_nodes >= 0 else 0
    if args.require_cover and covered_count != num_nodes:
        errors.append(f"masks cover {covered_count}/{num_nodes} nodes, but --require-cover was supplied")

    return {
        "ok": not errors,
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "num_features": num_features,
        "num_classes": num_classes,
        "mask_counts": mask_counts,
        "mask_covered_nodes": covered_count,
        "errors": errors,
        "warnings": warnings,
    }


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate shapes, labels, edge_index, and masks for a saved CogDL Graph.")
    parser.add_argument("--path", required=True, type=Path, help="Path to a torch-saved CogDL Graph artifact.")
    parser.add_argument("--load-mode", choices=("auto", "graph", "node-dataset"), default="auto", help="Load directly as a Graph, through NodeDataset, or try both. Default: auto.")
    parser.add_argument("--allow-missing-x", action="store_true", help="Allow featureless graphs. Most node-classification GNNs need x.")
    parser.add_argument("--bool-masks-only", action="store_true", help="Reject integer index masks; require boolean masks of length num_nodes.")
    parser.add_argument("--allow-overlap", action="store_true", help="Allow train/val/test masks to overlap. Default is to reject overlaps.")
    parser.add_argument("--require-cover", action="store_true", help="Require train/val/test masks together to cover every node.")
    parser.add_argument("--trust-pickle", action="store_true", help="Permit unsafe pickle loading fallback for trusted local CogDL artifacts only.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    graph, loaded_as = load_graph(args.path, args.load_mode, args.trust_pickle)
    result = validate_graph(graph, args)
    result["path"] = str(args.path)
    result["loaded_as"] = loaded_as

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = "OK" if result["ok"] else "FAILED"
        print(f"{status}: {args.path} loaded as {loaded_as}")
        print(
            f"nodes={result.get('num_nodes')} edges={result.get('num_edges')} "
            f"features={result.get('num_features')} classes={result.get('num_classes')}"
        )
        print(f"mask_counts={result.get('mask_counts')} covered={result.get('mask_covered_nodes')}")
        for warning in result["warnings"]:
            print(f"WARNING: {warning}", file=sys.stderr)
        for error in result["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - user-facing CLI guard
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
