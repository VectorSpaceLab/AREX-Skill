#!/usr/bin/env python3
"""No-download smoke checks for Spektral model and layer wiring."""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
import tensorflow as tf
from tensorflow.keras import Input, Model

from spektral.data import BatchLoader, Dataset, DisjointLoader, Graph, SingleLoader
from spektral.layers import GCNConv, GraphMasking, MessagePassing
from spektral.models import GCN, GeneralGNN
from spektral.utils.sparse import sp_matrix_to_sp_tensor


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


class ToyMessagePassing(MessagePassing):
    def __init__(self, channels: int, **kwargs):
        super().__init__(aggregate="mean", **kwargs)
        self.channels = channels

    def build(self, input_shape):
        in_channels = input_shape[0][-1]
        self.kernel = self.add_weight(
            shape=(in_channels, self.channels), initializer="ones", name="kernel"
        )
        self.built = True

    def call(self, inputs):
        x, a = inputs
        x = tf.matmul(x, self.kernel)
        return self.propagate(x=x, a=a)

    def message(self, x):
        return self.get_sources(x)


def main() -> int:
    single_inputs = next(iter(SingleLoader(SingleGraphDataset(), epochs=1)))
    general_single = GeneralGNN(output=2)
    general_single_out = general_single(single_inputs)
    assert tuple(general_single_out.shape) == (1, 2)
    print("single_general_gnn_shape", tuple(general_single_out.shape))

    gcn_single = GCN(2)
    gcn_single_out = gcn_single(single_inputs)
    assert tuple(gcn_single_out.shape) == (3, 2)
    print("single_gcn_shape", tuple(gcn_single_out.shape))

    disjoint_inputs = next(
        iter(DisjointLoader(ManyGraphDataset(), batch_size=2, epochs=1, shuffle=False))
    )
    general_disjoint = GeneralGNN(output=2)
    general_disjoint_out = general_disjoint(disjoint_inputs)
    assert tuple(general_disjoint_out.shape) == (2, 2)
    print("disjoint_general_gnn_shape", tuple(general_disjoint_out.shape))

    gcn_disjoint = GCN(2)
    gcn_disjoint_out = gcn_disjoint(disjoint_inputs)
    assert tuple(gcn_disjoint_out.shape) == (7, 2)
    print("disjoint_gcn_shape", tuple(gcn_disjoint_out.shape))

    batch_inputs = next(
        iter(BatchLoader(ManyGraphDataset(), batch_size=2, epochs=1, shuffle=False, mask=True))
    )
    x_in = Input(shape=(None, 3))
    a_in = Input(shape=(None, None))
    x = GraphMasking()(x_in)
    out = GCNConv(2)([x, a_in])
    batch_model = Model([x_in, a_in], out)
    batch_out = batch_model(batch_inputs)
    assert tuple(batch_out.shape) == (2, 4, 2)
    print("batch_gcnconv_shape", tuple(batch_out.shape))

    x_np = np.arange(6, dtype=np.float32).reshape(3, 2)
    a_sp = sp_matrix_to_sp_tensor(ring(3))
    toy_x = Input(shape=(2,))
    toy_a = Input(shape=(None,), sparse=True)
    toy_out = ToyMessagePassing(3)([toy_x, toy_a])
    toy_model = Model([toy_x, toy_a], toy_out)
    mp_out = toy_model([tf.constant(x_np), a_sp])
    assert tuple(mp_out.shape) == (3, 3)
    print("message_passing_shape", tuple(mp_out.shape))

    print("smoke_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
