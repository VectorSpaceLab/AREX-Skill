#!/usr/bin/env python3
"""Tiny component smoke check for PyTorch Metric Learning.

This script exercises a few representative component combinations on toy tensors
without downloading data or requiring a GPU.
"""

from __future__ import annotations

import torch

from pytorch_metric_learning import losses, miners, reducers
from pytorch_metric_learning.distances import CosineSimilarity, LpDistance
from pytorch_metric_learning.losses import CrossBatchMemory, SelfSupervisedLoss
from pytorch_metric_learning.utils import loss_and_miner_utils as lmu


def main() -> None:
    torch.manual_seed(7)
    emb = torch.tensor(
        [[1.0, 0.0], [0.9, 0.1], [-1.0, 0.0], [-0.9, -0.1]], dtype=torch.float32
    )
    emb = torch.nn.functional.normalize(emb, dim=1).requires_grad_(True)
    labels = torch.tensor([0, 0, 1, 1])

    triplet_loss = losses.TripletMarginLoss(distance=LpDistance())
    triplet_miner = miners.TripletMarginMiner(distance=LpDistance())
    triplets = triplet_miner(emb, labels)
    loss_value = triplet_loss(emb, labels, triplets)
    loss_value.backward()
    assert loss_value.ndim == 0

    contrastive = losses.ContrastiveLoss(distance=CosineSimilarity())
    reducer = reducers.ThresholdReducer(high=1.0)
    reduced = contrastive(emb, labels)
    assert reduced.ndim == 0
    assert reducer({"loss": {"losses": torch.tensor([0.1, 0.2]), "indices": torch.tensor([0, 1]), "reduction_type": "element"}}, emb, labels) is not None

    wrapped = SelfSupervisedLoss(losses.TripletMarginLoss())
    ssl = wrapped(emb, emb.flip(0))
    assert ssl.ndim == 0

    memory = CrossBatchMemory(losses.TripletMarginLoss(), embedding_size=2, memory_size=8)
    memory_loss = memory(emb, labels)
    assert memory_loss.ndim == 0

    pairs = lmu.get_all_pairs_indices(labels)
    triplets2 = lmu.convert_to_triplets(pairs, labels)
    assert len(triplets2) == 3

    print("components-smoke-ok")


if __name__ == "__main__":
    main()
