#!/usr/bin/env python3
"""Run tiny pomegranate sequence-model smoke checks for MarkovChain and HMMs."""

from __future__ import annotations

import torch

from pomegranate.distributions import Categorical, ConditionalCategorical, Exponential
from pomegranate.hmm import DenseHMM, SparseHMM
from pomegranate.markov_chain import MarkovChain


def run_markov_chain() -> torch.Tensor:
    initial = Categorical([[0.4, 0.6]])
    transition = ConditionalCategorical([[[0.7, 0.3], [0.2, 0.8]]])
    model = MarkovChain([initial, transition])
    X = torch.tensor([[[0], [1], [1]], [[1], [0], [0]]])
    logp = model.log_probability(X)
    assert logp.shape == (2,)
    return logp


def run_hmms() -> tuple[torch.Tensor, torch.Tensor]:
    X = torch.tensor([[[0.5], [1.0], [1.5]], [[2.0], [2.5], [3.0]]], dtype=torch.float32)
    starts = [0.6, 0.4]
    ends = [0.1, 0.1]
    dense_edges = [[0.7, 0.2], [0.3, 0.6]]

    dense = DenseHMM(
        [Exponential([1.0]), Exponential([2.5])],
        edges=dense_edges,
        starts=starts,
        ends=ends,
    )
    dense_logp = dense.log_probability(X)
    assert dense_logp.shape == (2,)

    s1 = Exponential([1.0])
    s2 = Exponential([2.5])
    sparse_edges = [[s1, s1, 0.7], [s1, s2, 0.2], [s2, s1, 0.3], [s2, s2, 0.6]]
    sparse = SparseHMM([s1, s2], edges=sparse_edges, starts=starts, ends=ends)
    sparse_logp = sparse.log_probability(X)
    assert sparse_logp.shape == (2,)
    return dense_logp, sparse_logp


def main() -> int:
    mc_logp = run_markov_chain()
    dense_logp, sparse_logp = run_hmms()
    print("sequence-model smoke passed")
    print("MarkovChain logp:", mc_logp.detach().cpu().round(decimals=4).tolist())
    print("DenseHMM logp:", dense_logp.detach().cpu().round(decimals=4).tolist())
    print("SparseHMM logp:", sparse_logp.detach().cpu().round(decimals=4).tolist())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
