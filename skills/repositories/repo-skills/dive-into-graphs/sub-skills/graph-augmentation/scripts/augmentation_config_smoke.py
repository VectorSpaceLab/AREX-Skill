#!/usr/bin/env python3
"""Tiny DIG augmentation smoke check.

Exercises DegreeTrans and AUG_trans on a tiny synthetic graph and prints the
available GraphAug/S-Mixup names. No downloads.
"""
import argparse
import json

import torch
from torch_geometric.data import Data

from dig.auggraph.dataset import AUG_trans, DegreeTrans, Subset
from dig.auggraph.method.GraphAug import RunnerAugCls, RunnerGenerator, RunnerRewardGen
from dig.auggraph.method.SMixup import smixup
from dig.auggraph.method.GraphAug.constants.enums import DatasetName


def main():
    parser = argparse.ArgumentParser(description="Tiny DIG augmentation smoke check.")
    parser.parse_args()

    tiny_graphs = [
        Data(x=None, edge_index=torch.tensor([[0, 1], [1, 0]], dtype=torch.long), y=torch.tensor([0])),
        Data(x=None, edge_index=torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]], dtype=torch.long), y=torch.tensor([1])),
    ]
    degree = DegreeTrans(tiny_graphs)

    def identity_aug(data):
        return [data, None]

    aug = AUG_trans(identity_aug, device=torch.device('cpu'), pre_trans=None, post_trans=None)
    transformed = [degree(g) for g in tiny_graphs]
    augmented = aug(transformed[0])

    print(json.dumps({
        "degree_dim": int(transformed[0].x.shape[1]),
        "augmented_nodes": int(augmented.num_nodes),
        "runners": [RunnerAugCls.__name__, RunnerGenerator.__name__, RunnerRewardGen.__name__],
        "smixup_name": smixup.__name__,
        "datasets": [d.value for d in [DatasetName.NCI1, DatasetName.IMDB_BINARY]],
    }, indent=2, sort_keys=True))
    print("augmentation_config_smoke: ok")


if __name__ == "__main__":
    main()
