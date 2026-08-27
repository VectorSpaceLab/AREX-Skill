#!/usr/bin/env python3
"""Tiny dataset and sampler smoke check for PyTorch Metric Learning."""

from __future__ import annotations

import torch

from pytorch_metric_learning.samplers import (
    FixedSetOfTriplets,
    HierarchicalSampler,
    MPerClassSampler,
)


def main() -> None:
    labels = torch.tensor([0, 0, 1, 1, 2, 2, 3, 3])
    sampler = MPerClassSampler(labels, m=2, batch_size=4, length_before_new_iter=8)
    iterator = iter(sampler)
    batch = [next(iterator) for _ in range(4)]
    assert len(batch) == 4
    assert len(torch.unique(labels[batch])) == 2

    hierarchical_labels = torch.tensor(
        [[0, 10], [0, 10], [1, 20], [1, 20], [2, 20], [2, 20], [3, 30], [3, 30]]
    )
    hierarchical = HierarchicalSampler(
        hierarchical_labels,
        batch_size=4,
        samples_per_class=2,
        super_classes_per_batch=2,
        outer_label=1,
        inner_label=0,
    )
    iterator2 = iter(hierarchical)
    batch2 = [next(iterator2) for _ in range(4)]
    assert len(batch2) == 4

    fixed = FixedSetOfTriplets(labels, num_triplets=4)
    iterator3 = iter(fixed)
    batch3 = [next(iterator3) for _ in range(12)]
    assert len(batch3) == 12

    print("data-smoke-ok")


if __name__ == "__main__":
    main()
