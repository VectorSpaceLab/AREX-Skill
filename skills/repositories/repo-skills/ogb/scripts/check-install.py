#!/usr/bin/env python3
"""Verify the installed OGB package and the most important optional helpers."""

from __future__ import annotations

import importlib.metadata as metadata
import importlib.util


def version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "<missing>"


def present(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def main() -> None:
    print("ogb:", version("ogb"))
    print("torch:", version("torch"))
    print("rdkit:", version("rdkit"))
    print("torch_geometric:", "present" if present("torch_geometric") else "missing")
    print("dgl:", "present" if present("dgl") else "missing")

    import ogb
    from ogb.graphproppred import GraphPropPredDataset, Evaluator as GraphEvaluator
    from ogb.nodeproppred import NodePropPredDataset, Evaluator as NodeEvaluator
    from ogb.linkproppred import LinkPropPredDataset, Evaluator as LinkEvaluator
    from ogb.io import DatasetSaver

    print("ogb.__version__:", ogb.__version__)
    print("graph:", GraphPropPredDataset.__name__, GraphEvaluator.__name__)
    print("node:", NodePropPredDataset.__name__, NodeEvaluator.__name__)
    print("link:", LinkPropPredDataset.__name__, LinkEvaluator.__name__)
    print("dataset_saver:", DatasetSaver.__name__)

    from ogb.utils import smiles2graph

    graph = smiles2graph("CCO")
    print("smiles2graph_nodes:", graph["num_nodes"])
    print("smiles2graph_edges:", graph["edge_index"].shape[1])

    try:
        import torch

        print("torch_cuda_available:", torch.cuda.is_available())
        print("torch_cuda_device_count:", torch.cuda.device_count())
        if torch.cuda.is_available():
            x = torch.empty((1,), device="cuda")
            print("cuda_smoke_device:", x.device)
    except Exception as exc:  # pragma: no cover - diagnostics only
        print("torch_cuda_smoke_failed:", repr(exc))


if __name__ == "__main__":
    main()
