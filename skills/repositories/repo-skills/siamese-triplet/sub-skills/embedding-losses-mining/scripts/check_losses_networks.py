#!/usr/bin/env python3
"""Smoke the embedding networks, losses, selectors, and online mining helpers."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch


def add_module_dir(module_dir: str) -> None:
    path = str(Path(module_dir).resolve())
    if path not in sys.path:
        sys.path.insert(0, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--module-dir",
        default=str(Path.cwd()),
        help="Directory containing the repo's top-level modules; defaults to the current working directory.",
    )
    args = parser.parse_args()

    add_module_dir(args.module_dir)

    from losses import ContrastiveLoss, OnlineContrastiveLoss, OnlineTripletLoss, TripletLoss
    from networks import ClassificationNet, EmbeddingNet, SiameseNet, TripletNet
    from utils import (
        AllPositivePairSelector,
        AllTripletSelector,
        HardNegativePairSelector,
        HardestNegativeTripletSelector,
        RandomNegativeTripletSelector,
        SemihardNegativeTripletSelector,
    )

    x = torch.randn(3, 1, 28, 28)
    embedding = EmbeddingNet()
    emb = embedding(x)
    assert emb.shape == (3, 2)

    classification = ClassificationNet(EmbeddingNet(), n_classes=2)
    scores = classification(x)
    assert scores.shape == (3, 2)

    siamese = SiameseNet(EmbeddingNet())
    out1, out2 = siamese(x[:2], x[1:3])
    assert out1.shape == out2.shape == (2, 2)

    triplet = TripletNet(EmbeddingNet())
    anchor, positive, negative = triplet(x[:1], x[1:2], x[2:3])
    assert anchor.shape == positive.shape == negative.shape == (1, 2)

    labels = torch.tensor([0, 0, 1, 1], dtype=torch.long)
    embeddings = torch.randn(4, 2)

    contrastive = ContrastiveLoss(1.0)
    triplet_loss = TripletLoss(1.0)
    assert contrastive(embeddings[:2], embeddings[2:], torch.tensor([1, 0])).ndim == 0
    assert triplet_loss(embeddings[:1], embeddings[1:2], embeddings[2:3]).ndim == 0

    pos_pairs, neg_pairs = AllPositivePairSelector(balance=False).get_pairs(embeddings, labels)
    assert len(pos_pairs) > 0
    assert len(neg_pairs) > 0

    hard_pairs = HardNegativePairSelector(cpu=True).get_pairs(embeddings, labels)
    assert len(hard_pairs[0]) > 0

    triplets = AllTripletSelector().get_triplets(embeddings, labels)
    assert triplets.ndim == 2 and triplets.shape[1] == 3

    # The factory helpers should build usable selectors on the same fixture.
    for selector_factory in (
        HardestNegativeTripletSelector,
        RandomNegativeTripletSelector,
        SemihardNegativeTripletSelector,
    ):
        selector = selector_factory(1.0)
        mined = selector.get_triplets(embeddings, labels)
        assert mined.ndim == 2 and mined.shape[1] == 3

    online_cl = OnlineContrastiveLoss(1.0, AllPositivePairSelector(balance=False))
    online_tl = OnlineTripletLoss(1.0, AllTripletSelector())
    cl_value = online_cl(embeddings, labels)
    tl_value, count = online_tl(embeddings, labels)
    assert cl_value.ndim == 0
    assert tl_value.ndim == 0 and count > 0

    print("loss/network smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
