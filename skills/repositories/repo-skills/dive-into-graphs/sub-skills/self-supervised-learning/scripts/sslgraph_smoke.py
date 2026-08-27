#!/usr/bin/env python3
"""Tiny DIG SSL smoke check.

Runs a tiny GraphCL pretraining step on two synthetic graphs and reports the
resulting module names. No downloads.
"""
import argparse
import json

import torch
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader

from dig.sslgraph.method import GraphCL, GRACE, InfoGraph, MVGRL, NodeMVGRL, pGRACE
from dig.sslgraph.method.contrastive.views_fn import NodeAttrMask
from dig.sslgraph.utils import Encoder, setup_seed


def tiny_graphs():
    x1 = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    e1 = torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]], dtype=torch.long)
    x2 = torch.tensor([[1.0, 1.0, 0.0], [0.0, 1.0, 1.0], [1.0, 0.0, 1.0]])
    e2 = torch.tensor([[0, 2, 1, 2], [2, 0, 2, 1]], dtype=torch.long)
    return [Data(x=x1, edge_index=e1, y=torch.tensor([0])), Data(x=x2, edge_index=e2, y=torch.tensor([1]))]


def main():
    parser = argparse.ArgumentParser(description="Tiny DIG SSL smoke check.")
    parser.parse_args()
    setup_seed(0)

    dataset = tiny_graphs()
    loader = DataLoader(dataset, batch_size=2, shuffle=False)
    encoder = Encoder(feat_dim=3, hidden_dim=4, n_layers=2, gnn='gin', bn=True)
    model = GraphCL(dim=8, aug_1='maskN', aug_2='dropN', aug_ratio=0.1, tau=0.2)
    optimizer = torch.optim.Adam(encoder.parameters(), lr=0.01)

    for _ in model.train(encoder, loader, optimizer, epochs=1):
        pass

    view = NodeAttrMask(mask_ratio=0.1)
    _ = view(dataset[0])

    print(json.dumps({
        "encoder": type(encoder).__name__,
        "graphcl": type(model).__name__,
        "views": ["NodeAttrMask", "dropN"],
        "extra_models": [cls.__name__ for cls in [GRACE, InfoGraph, MVGRL, NodeMVGRL, pGRACE]],
    }, indent=2, sort_keys=True))
    print("sslgraph_smoke: ok")


if __name__ == "__main__":
    main()
