#!/usr/bin/env python3
"""Inspect DGL-LifeSci model constructor signatures safely.

This helper prints signatures for selected constructors and can optionally
instantiate tiny CPU-only model objects when dimensions are provided. It does
not download pretrained checkpoints or run dataset examples.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


DEFAULT_CONSTRUCTORS = [
    "GCN",
    "GAT",
    "GATv2",
    "GraphSAGE",
    "AttentiveFPGNN",
    "GCNPredictor",
    "GATPredictor",
    "GATv2Predictor",
    "AttentiveFPPredictor",
    "MPNNPredictor",
    "WeavePredictor",
    "GINPredictor",
    "NFPredictor",
    "GNNOGBPredictor",
    "PAGTNPredictor",
    "WeightedSumAndMax",
    "SumAndMax",
    "AttentiveFPReadout",
    "MLPNodeReadout",
    "WeaveGather",
    "HadamardLinkPredictor",
    "MLPPredictor",
    "load_pretrained",
]

SUBMODULES = {
    "GATv2Predictor": "dgllife.model.model_zoo.gatv2_predictor",
    "HadamardLinkPredictor": "dgllife.model.model_zoo.hadamard_link_predictor",
    "GCNPredictor": "dgllife.model.model_zoo.gcn_predictor",
    "GATPredictor": "dgllife.model.model_zoo.gat_predictor",
    "AttentiveFPPredictor": "dgllife.model.model_zoo.attentivefp_predictor",
    "MPNNPredictor": "dgllife.model.model_zoo.mpnn_predictor",
    "WeavePredictor": "dgllife.model.model_zoo.weave_predictor",
    "GINPredictor": "dgllife.model.model_zoo.gin_predictor",
    "NFPredictor": "dgllife.model.model_zoo.nf_predictor",
    "GNNOGBPredictor": "dgllife.model.model_zoo.gnn_ogb_predictor",
    "PAGTNPredictor": "dgllife.model.model_zoo.pagtn_predictor",
    "MLPPredictor": "dgllife.model.model_zoo.mlp_predictor",
    "GCN": "dgllife.model.gnn.gcn",
    "GAT": "dgllife.model.gnn.gat",
    "GATv2": "dgllife.model.gnn.gatv2",
    "GraphSAGE": "dgllife.model.gnn.graphsage",
    "AttentiveFPGNN": "dgllife.model.gnn.attentivefp",
    "WeightedSumAndMax": "dgllife.model.readout.weighted_sum_and_max",
    "SumAndMax": "dgllife.model.readout.sum_and_max",
    "AttentiveFPReadout": "dgllife.model.readout.attentivefp_readout",
    "MLPNodeReadout": "dgllife.model.readout.mlp_readout",
    "WeaveGather": "dgllife.model.readout.weave_readout",
}


def comma_list(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def import_versions() -> Dict[str, str]:
    versions: Dict[str, str] = {}
    for module_name in ["dgllife", "dgl", "torch"]:
        try:
            module = importlib.import_module(module_name)
            versions[module_name] = getattr(module, "__version__", "unknown")
        except Exception as exc:  # pragma: no cover - diagnostic path
            versions[module_name] = f"IMPORT_ERROR: {exc}"
    return versions


def resolve_constructor(name: str, use_submodules: bool) -> Tuple[Optional[Callable[..., Any]], str, Optional[str]]:
    errors: List[str] = []
    try:
        root = importlib.import_module("dgllife.model")
        obj = getattr(root, name)
        return obj, "dgllife.model", None
    except Exception as exc:
        errors.append(f"dgllife.model: {exc}")

    if use_submodules and name in SUBMODULES:
        module_name = SUBMODULES[name]
        try:
            module = importlib.import_module(module_name)
            obj = getattr(module, name)
            return obj, module_name, None
        except Exception as exc:
            errors.append(f"{module_name}: {exc}")

    return None, "", "; ".join(errors)


def signature_for(obj: Callable[..., Any]) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # pragma: no cover - rare builtin path
        return f"SIGNATURE_ERROR: {exc}"


def build_kwargs(name: str, args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    node = args.node_feats
    edge = args.edge_feats
    hidden = args.hidden_feats
    tasks = args.tasks

    recipes: Dict[str, Dict[str, Any]] = {
        "GCN": {"in_feats": node, "hidden_feats": [hidden]},
        "GAT": {"in_feats": node, "hidden_feats": [hidden], "num_heads": [1], "agg_modes": ["mean"]},
        "GATv2": {"in_feats": node, "hidden_feats": [hidden], "num_heads": [1], "agg_modes": ["mean"]},
        "GraphSAGE": {"in_feats": node, "hidden_feats": [hidden]},
        "AttentiveFPGNN": {"node_feat_size": node, "edge_feat_size": edge, "graph_feat_size": hidden, "num_layers": 1},
        "GCNPredictor": {"in_feats": node, "hidden_feats": [hidden], "n_tasks": tasks},
        "GATPredictor": {
            "in_feats": node,
            "hidden_feats": [hidden],
            "num_heads": [1],
            "agg_modes": ["mean"],
            "n_tasks": tasks,
        },
        "GATv2Predictor": {
            "in_feats": node,
            "hidden_feats": [hidden],
            "num_heads": [1],
            "agg_modes": ["mean"],
            "n_tasks": tasks,
        },
        "AttentiveFPPredictor": {
            "node_feat_size": node,
            "edge_feat_size": edge,
            "graph_feat_size": hidden,
            "num_layers": 1,
            "num_timesteps": 1,
            "n_tasks": tasks,
        },
        "MPNNPredictor": {"node_in_feats": node, "edge_in_feats": edge, "node_out_feats": hidden, "n_tasks": tasks},
        "WeavePredictor": {"node_in_feats": node, "edge_in_feats": edge, "gnn_hidden_feats": hidden, "n_tasks": tasks},
        "GINPredictor": {
            "num_node_emb_list": [120, 3],
            "num_edge_emb_list": [6, 3],
            "num_layers": 2,
            "emb_dim": hidden,
            "n_tasks": tasks,
        },
        "NFPredictor": {"in_feats": node, "hidden_feats": [hidden], "n_tasks": tasks},
        "GNNOGBPredictor": {"in_edge_feats": edge, "hidden_feats": hidden, "n_layers": 2, "n_tasks": tasks},
        "PAGTNPredictor": {
            "node_in_feats": node,
            "node_out_feats": hidden,
            "node_hid_feats": hidden,
            "edge_feats": edge,
            "n_tasks": tasks,
        },
        "WeightedSumAndMax": {"in_feats": node},
        "SumAndMax": {},
        "AttentiveFPReadout": {"feat_size": node, "num_timesteps": 1},
        "MLPNodeReadout": {"node_feats": node, "hidden_feats": hidden, "graph_feats": hidden},
        "WeaveGather": {"node_in_feats": node, "gaussian_expand": False},
        "HadamardLinkPredictor": {"in_feats": node, "hidden_feats": hidden, "num_layers": 2, "n_tasks": tasks},
        "MLPPredictor": {"in_feats": node, "hidden_feats": hidden, "n_tasks": tasks},
    }
    return recipes.get(name)


def instantiate(name: str, obj: Callable[..., Any], args: argparse.Namespace) -> Tuple[bool, str]:
    kwargs = build_kwargs(name, args)
    if kwargs is None:
        return False, "no safe instantiation recipe"
    try:
        instance = obj(**kwargs)
        class_name = instance.__class__.__name__
        return True, f"ok: {class_name}({kwargs})"
    except Exception as exc:
        return False, f"failed: {exc} with kwargs={kwargs}"


def inspect_constructors(names: Iterable[str], args: argparse.Namespace) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    for name in names:
        obj, source, error = resolve_constructor(name, args.submodules)
        if obj is None:
            results[name] = {"available": False, "error": error}
            continue

        entry: Dict[str, Any] = {
            "available": True,
            "source": source,
            "signature": signature_for(obj),
        }
        if args.instantiate and name != "load_pretrained":
            ok, detail = instantiate(name, obj, args)
            entry["instantiated"] = ok
            entry["instantiation_detail"] = detail
        results[name] = entry
    return results


def print_text(versions: Dict[str, str], results: Dict[str, Any]) -> None:
    print("Versions:")
    for name, version in versions.items():
        print(f"  {name}: {version}")
    print("\nConstructors:")
    for name, entry in results.items():
        print(f"- {name}")
        if not entry.get("available"):
            print(f"    unavailable: {entry.get('error')}")
            continue
        print(f"    source: {entry['source']}")
        print(f"    signature: {entry['signature']}")
        if "instantiated" in entry:
            print(f"    instantiated: {entry['instantiated']}")
            print(f"    detail: {entry['instantiation_detail']}")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--constructors",
        type=comma_list,
        default=DEFAULT_CONSTRUCTORS,
        help="Comma-separated constructor/function names to inspect.",
    )
    parser.add_argument(
        "--submodules",
        action="store_true",
        help="Try known narrower submodule imports when dgllife.model root export is missing.",
    )
    parser.add_argument(
        "--instantiate",
        action="store_true",
        help="Instantiate supported constructors with tiny CPU-safe kwargs. Does not run forward passes.",
    )
    parser.add_argument("--node-feats", type=int, default=74, help="Node feature width for instantiation recipes.")
    parser.add_argument("--edge-feats", type=int, default=13, help="Edge feature width for instantiation recipes.")
    parser.add_argument("--hidden-feats", type=int, default=16, help="Hidden width for instantiation recipes.")
    parser.add_argument("--tasks", type=int, default=1, help="Number of prediction tasks for predictor recipes.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    versions = import_versions()
    results = inspect_constructors(args.constructors, args)
    if args.json:
        print(json.dumps({"versions": versions, "constructors": results}, indent=2, sort_keys=True))
    else:
        print_text(versions, results)
    unavailable = [name for name, entry in results.items() if not entry.get("available")]
    return 2 if unavailable else 0


if __name__ == "__main__":
    sys.exit(main())
