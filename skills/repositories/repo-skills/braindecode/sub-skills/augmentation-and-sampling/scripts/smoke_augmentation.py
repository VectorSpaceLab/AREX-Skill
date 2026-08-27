#!/usr/bin/env python3
"""Check clean-plus-augmented batch invariants on a local TensorDataset."""
from __future__ import annotations
import argparse
import torch
from torch.utils.data import TensorDataset
from braindecode.augmentation import AugmentedDataLoader
from braindecode.augmentation.base import Transform

def replace_with_k(X, y=None, k=7.0):
    out = torch.full_like(X, k)
    return (out, y) if y is not None else out
class ConstantTransform(Transform):
    operation = staticmethod(replace_with_k)
    def __init__(self, k=7.0):
        self.k = k
        super().__init__(probability=1.0)
    def get_augmentation_params(self, X, y):
        return {"k": self.k}
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n-augmentation", type=int, default=2)
    args = p.parse_args()
    if args.n_augmentation < 0:
        p.error("--n-augmentation must be non-negative")
    X = torch.randn(4, 2, 12)
    y = torch.arange(4)
    loader = AugmentedDataLoader(TensorDataset(X, y), transforms=ConstantTransform(),
                                 batch_size=4, shuffle=False,
                                 n_augmentation=args.n_augmentation)
    batch_x, batch_y = next(iter(loader))
    factor = 1 + args.n_augmentation
    assert batch_x.shape[0] == factor * 4
    assert torch.equal(batch_y, y.repeat(factor))
    assert torch.equal(batch_x[:4], X)
    print(f"batch_shape={tuple(batch_x.shape)} labels={tuple(batch_y.shape)}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
