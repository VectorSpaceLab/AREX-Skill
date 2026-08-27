#!/usr/bin/env python3
"""Shared no-download CogDL environment smoke.

This helper imports the package, prints registry summaries, and can optionally
probe a toy Graph + GCNLayer forward pass or a tiny CUDA allocation. It does
not train models or download datasets.
"""

from __future__ import annotations

import argparse
import json
from pprint import pprint


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON summary instead of a pretty dict")
    parser.add_argument("--show-registries", action="store_true", help="include model, dataset, app, and wrapper counts")
    parser.add_argument("--probe-graph", action="store_true", help="run a tiny Graph + GCNLayer smoke")
    parser.add_argument("--probe-cuda", action="store_true", help="allocate a one-element CUDA tensor when available")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    import torch
    import cogdl
    from cogdl.data import Graph
    from cogdl.datasets import SUPPORTED_DATASETS
    from cogdl.layers import GCNLayer
    from cogdl.models import SUPPORTED_MODELS
    from cogdl.pipelines import SUPPORTED_APPS
    from cogdl.wrappers.default_match import get_wrappers_name

    summary = {
        "cogdl_version": cogdl.__version__,
        "torch_version": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cuda_available": bool(torch.cuda.is_available()),
    }

    if args.show_registries:
        summary.update(
            {
                "supported_models": len(SUPPORTED_MODELS),
                "supported_datasets": len(SUPPORTED_DATASETS),
                "supported_apps": sorted(SUPPORTED_APPS),
                "default_wrappers": {
                    name: get_wrappers_name(name)
                    for name in ["gcn", "gin", "prone", "gatne", "stgcn"]
                },
            }
        )

    if args.probe_graph:
        edge_index = (torch.tensor([0, 1, 2]), torch.tensor([1, 2, 0]))
        graph = Graph(x=torch.eye(3), edge_index=edge_index)
        graph.sym_norm()
        out = GCNLayer(3, 2)(graph, graph.x)
        summary["toy_graph"] = {
            "num_nodes": graph.num_nodes,
            "num_edges": graph.num_edges,
            "output_shape": list(out.shape),
        }

    if args.probe_cuda:
        if torch.cuda.is_available():
            tensor = torch.empty((1,), device="cuda")
            summary["cuda_probe"] = {
                "device_count": torch.cuda.device_count(),
                "device_name": torch.cuda.get_device_name(0),
                "capability": list(torch.cuda.get_device_capability(0)),
                "tensor_device": str(tensor.device),
            }
        else:
            summary["cuda_probe"] = {"status": "unavailable"}

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        pprint(summary)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
