#!/usr/bin/env python3
"""Run tiny pomegranate distribution smoke checks.

This script is intentionally small and CPU-safe. It does not read repository files.
"""

from __future__ import annotations

import torch

from pomegranate.distributions import Categorical, Exponential, IndependentComponents, Normal


def main() -> int:
    X = torch.tensor(
        [[0.0, 1.0], [0.2, 1.5], [1.0, 2.5], [1.2, 3.0]],
        dtype=torch.float32,
    )

    normal = Normal(covariance_type="diag").fit(X)
    normal_logp = normal.log_probability(X)
    assert normal_logp.shape == (4,)

    categorical = Categorical().fit(torch.tensor([[0], [1], [1], [2], [2], [2]]))
    categorical_logp = categorical.log_probability(torch.tensor([[0], [2]]))
    assert categorical_logp.shape == (2,)

    independent = IndependentComponents(
        [
            Normal([0.0], [1.0], covariance_type="diag"),
            Exponential([2.0]),
        ]
    )
    independent_logp = independent.log_probability(torch.tensor([[0.0, 1.0], [1.0, 2.0]]))
    assert independent_logp.shape == (2,)

    print("distribution smoke passed")
    print("Normal logp:", normal_logp.detach().cpu().round(decimals=4).tolist())
    print("Categorical logp:", categorical_logp.detach().cpu().round(decimals=4).tolist())
    print("IndependentComponents logp:", independent_logp.detach().cpu().round(decimals=4).tolist())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
