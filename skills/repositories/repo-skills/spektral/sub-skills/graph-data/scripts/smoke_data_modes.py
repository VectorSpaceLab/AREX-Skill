#!/usr/bin/env python3
"""No-download smoke checks for Spektral graph data modes and transforms."""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from spektral.data import BatchLoader, Dataset, DisjointLoader, Graph, MixedLoader, SingleLoader
from spektral.layers import GCNConv
from spektral.transforms import Degree, LayerPreprocess


def ring(n: int, dtype: str = "float32"):
    a = np.zeros((n, n), dtype=dtype)
    for i in range(n):
        j = (i + 1) % n
        a[i, j] = 1
        a[j, i] = 1
    return sp.csr_matrix(a)


class SingleGraphDataset(Dataset):
    def read(self):
        return [Graph(x=np.eye(3, dtype=np.float32), a=ring(3))]


class ManyGraphDataset(Dataset):
    def read(self):
        return [
            Graph(x=np.arange(6, dtype=np.float32).reshape(3, 2), a=ring(3)),
            Graph(x=np.arange(8, dtype=np.float32).reshape(4, 2), a=ring(4)),
        ]


class MixedGraphDataset(Dataset):
    def read(self):
        self.a = ring(4)
        return [
            Graph(x=np.arange(8, dtype=np.float32).reshape(4, 2)),
            Graph(x=np.arange(8, dtype=np.float32).reshape(4, 2) + 10),
        ]


def main() -> int:
    single_inputs = next(iter(SingleLoader(SingleGraphDataset(), epochs=1)))
    assert len(single_inputs) == 2
    assert single_inputs[0].shape == (3, 3)
    assert single_inputs[1].shape == (3, 3)
    print("single_loader_shape", single_inputs[0].shape, single_inputs[1].shape)

    disjoint_inputs = next(
        iter(DisjointLoader(ManyGraphDataset(), batch_size=2, epochs=1, shuffle=False))
    )
    assert len(disjoint_inputs) == 3
    assert disjoint_inputs[0].shape == (7, 2)
    assert disjoint_inputs[1].shape == (7, 7)
    assert disjoint_inputs[2].shape == (7,)
    print("disjoint_loader_shape", disjoint_inputs[0].shape, disjoint_inputs[1].shape, disjoint_inputs[2].shape)

    batch_inputs = next(
        iter(BatchLoader(ManyGraphDataset(), batch_size=2, epochs=1, shuffle=False, mask=True))
    )
    assert len(batch_inputs) == 2
    assert batch_inputs[0].shape == (2, 4, 3)
    assert batch_inputs[1].shape == (2, 4, 4)
    print("batch_loader_shape", batch_inputs[0].shape, batch_inputs[1].shape)

    mixed_inputs = next(
        iter(MixedLoader(MixedGraphDataset(), batch_size=2, epochs=1, shuffle=False))
    )
    assert len(mixed_inputs) == 2
    assert mixed_inputs[0].shape == (2, 4, 2)
    assert mixed_inputs[1].shape == (4, 4)
    print("mixed_loader_shape", mixed_inputs[0].shape, mixed_inputs[1].shape)

    dataset = ManyGraphDataset()
    max_degree = int(dataset.map(lambda g: g.a.sum(-1).max(), reduce=max))
    assert max_degree == 2
    dataset.apply(Degree(max_degree))
    assert dataset[0].x.shape[-1] == 5
    print("degree_transform_shape", dataset[0].x.shape)

    filtered = dataset[:]
    filtered.filter(lambda g: g.n_nodes >= 4)
    assert len(filtered) == 1
    print("filtered_length", len(filtered))

    preprocessed = ManyGraphDataset()
    preprocessed.apply(LayerPreprocess(GCNConv))
    assert preprocessed[0].a.shape == (3, 3)
    print("layer_preprocess_shape", preprocessed[0].a.shape)

    print("smoke_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
