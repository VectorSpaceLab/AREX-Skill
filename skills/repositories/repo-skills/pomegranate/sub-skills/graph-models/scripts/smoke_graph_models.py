#!/usr/bin/env python3
"""Run tiny pomegranate BayesianNetwork and FactorGraph smoke checks.

The Bayesian network example is adapted from the repository's Monty Hall notebook
and modernized to current `pomegranate` imports.
"""

from __future__ import annotations

import torch

from pomegranate.bayesian_network import BayesianNetwork
from pomegranate.distributions import Categorical, ConditionalCategorical, JointCategorical
from pomegranate.factor_graph import FactorGraph


def run_monty_hall() -> torch.Tensor:
    guest = Categorical([[1.0 / 3, 1.0 / 3, 1.0 / 3]])
    prize = Categorical([[1.0 / 3, 1.0 / 3, 1.0 / 3]])
    monty_probs = torch.tensor(
        [[
            [[0.0, 0.5, 0.5], [0.0, 0.0, 1.0], [0.0, 1.0, 0.0]],
            [[0.0, 0.0, 1.0], [0.5, 0.0, 0.5], [1.0, 0.0, 0.0]],
            [[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.5, 0.5, 0.0]],
        ]],
        dtype=torch.float32,
    )
    monty = ConditionalCategorical(monty_probs)
    model = BayesianNetwork([guest, prize, monty], [(guest, monty), (prize, monty)])

    X = torch.tensor([[0, 1, -1], [0, 2, -1], [2, 1, -1]])
    masked = torch.masked.MaskedTensor(X, mask=X >= 0)
    predicted = model.predict(masked)
    assert predicted.shape == (3, 3)
    return predicted


def run_factor_graph() -> torch.Tensor:
    m1 = Categorical([[0.5, 0.5]])
    m2 = Categorical([[0.5, 0.5]])
    factor = JointCategorical([[0.45, 0.05], [0.10, 0.40]])
    graph = FactorGraph([factor], [m1, m2], [(m1, factor), (m2, factor)])

    X = torch.tensor([[0, -1], [1, -1]])
    masked = torch.masked.MaskedTensor(X, mask=X >= 0)
    predicted = graph.predict(masked)
    assert predicted.shape == (2, 2)
    return predicted


def main() -> int:
    bn_pred = run_monty_hall()
    fg_pred = run_factor_graph()
    print("graph-model smoke passed")
    print("BayesianNetwork completed rows:", bn_pred.detach().cpu().tolist())
    print("FactorGraph completed rows:", fg_pred.detach().cpu().tolist())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
