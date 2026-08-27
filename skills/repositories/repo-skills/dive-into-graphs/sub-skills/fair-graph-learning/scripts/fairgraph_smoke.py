#!/usr/bin/env python3
"""Tiny DIG fair-graph smoke check.

Exercises metric helpers on synthetic tensors only. No downloads and no CUDA
requirements.
"""
import argparse
import json

import numpy as np
import scipy.sparse as sp
import torch

from dig.fairgraph.method import run
from dig.fairgraph.utils.utils import accuracy, fair_metric, scipysp_to_pytorchsp


def main():
    parser = argparse.ArgumentParser(description="Tiny DIG fair-graph smoke check.")
    parser.parse_args()

    output = torch.tensor([[-0.1], [1.2], [0.7], [-0.5]])
    labels = torch.tensor([0, 1, 1, 0])
    sens = torch.tensor([0, 0, 1, 1])
    idx = torch.tensor([0, 1, 2, 3])
    acc = accuracy(output, labels)
    parity, equality = fair_metric(output, idx, labels, sens)
    sp_mat = sp.coo_matrix(np.array([[0.0, 1.0], [2.0, 0.0]], dtype=np.float32))
    torch_sp = scipysp_to_pytorchsp(sp_mat)

    print(json.dumps({
        "accuracy": float(acc),
        "parity": float(parity),
        "equality": float(equality),
        "runner": run.__name__,
        "torch_sparse_shape": list(torch_sp.shape),
        "torch_sparse_nnz": int(torch_sp._nnz()),
    }, indent=2, sort_keys=True))
    print("fairgraph_smoke: ok")


if __name__ == "__main__":
    main()
