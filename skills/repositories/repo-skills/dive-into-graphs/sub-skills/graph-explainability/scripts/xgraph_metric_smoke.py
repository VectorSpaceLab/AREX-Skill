#!/usr/bin/env python3
"""Tiny DIG explainability smoke check.

Runs a tiny edge-mask metric example on a synthetic graph. No downloads.
"""
import argparse
import json

import torch
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
from torch_geometric.utils.random import barabasi_albert_graph

from dig.xgraph.evaluation import ExplanationProcessor, XCollector, control_sparsity
from dig.xgraph.utils.compatibility import compatible_state_dict


def main():
    parser = argparse.ArgumentParser(description="Tiny DIG explainability smoke check.")
    parser.parse_args()

    device = torch.device('cpu')
    model = GCNConv(in_channels=1, out_channels=2).to(device)
    x_collector = XCollector(0.5)
    x_processor = ExplanationProcessor(model=model, device=device)

    x = torch.ones((10, 1), dtype=torch.float)
    edge_index = barabasi_albert_graph(10, 3)
    data = Data(x=x, edge_index=edge_index, y=torch.tensor([1.]))
    masks = [control_sparsity(torch.randn(edge_index.shape[1]), 0.5) for _ in range(2)]
    x_processor(data, masks, x_collector)

    state = compatible_state_dict({"conv1.weight": torch.ones(2, 1)})
    print(json.dumps({
        "fidelity": x_collector.fidelity,
        "fidelity_inv": x_collector.fidelity_inv,
        "sparsity": x_collector.sparsity,
        "state_keys": sorted(state.keys()),
    }, indent=2, sort_keys=True))
    print("xgraph_metric_smoke: ok")


if __name__ == "__main__":
    main()
