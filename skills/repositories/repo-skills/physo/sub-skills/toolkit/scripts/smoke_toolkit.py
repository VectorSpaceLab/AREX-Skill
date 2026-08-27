#!/usr/bin/env python3
"""Small deterministic CPU-only sampler, Dataset, and constant-fit smoke.

No network, plotting, or long symbolic-regression run is performed.
"""

from __future__ import annotations

import sys
import warnings

warnings.filterwarnings("ignore", message="Latex display is not available.*")

import numpy as np
import torch

from physo.physym.dataset import Dataset
from physo.toolkit import get_library, sample_random_expressions


def main() -> int:
    np.random.seed(7)
    torch.manual_seed(7)

    sampled = sample_random_expressions(
        batch_size=2,
        max_length=5,
        X_names=["x"],
        y_name="y",
        fixed_consts=[1.0],
        free_consts_names=["c"],
        free_consts_init_val=[1.0],
        op_names=["add", "mul", "neg"],
        priors_config=[
            ("HardLengthPrior", {"min_length": 1, "max_length": 5}),
            ("SoftLengthPrior", {"length_loc": 3, "scale": 1.0}),
        ],
        device="cpu",
        verbose=False,
        warn_about_units=False,
    )
    if len(sampled) != 2 or sampled.status().shape[0] != 2:
        raise AssertionError("random sampler returned the wrong batch shape")

    X = torch.tensor([[0.0, 1.0, 2.0, 3.0]], dtype=torch.float64)
    y = 2.5 * X[0]
    data = Dataset([X], [y], multi_y_weights=1.0, library=sampled.library)
    if data.multi_X_flatten.shape != (1, 4) or data.multi_y_flatten.shape != (4,):
        raise AssertionError("Dataset flattening returned the wrong shape")

    fit_library = get_library(
        X_names=["x"],
        y_name="y",
        fixed_consts=[],
        free_consts_names=["a"],
        free_consts_init_val=[1.0],
        op_names=["mul"],
        warn_about_units=False,
        device="cpu",
    )
    prefix = fit_library.encode([["mul", "a", "x"]])[0]
    program = fit_library.decode([[int(value) for value in prefix]]).get_prog(0)
    X_fit = torch.linspace(0.0, 1.0, 8, dtype=torch.float64).unsqueeze(0)
    y_target = 2.5 * X_fit[0]
    history = program.optimize_constants(X=X_fit, y_target=y_target)
    mse = torch.mean((program(X_fit) - y_target) ** 2).item()
    recovered = float(program.free_consts.class_values[0, 0].detach())
    if len(history) == 0 or mse > 1e-10 or abs(recovered - 2.5) > 1e-6:
        raise AssertionError(
            f"constant fit did not converge: recovered={recovered}, mse={mse}"
        )

    print(
        "PASS: sampled 2 expressions, validated Dataset shapes, "
        f"and recovered a={recovered:.6f} (mse={mse:.3e})"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # clear failure signal for a shell smoke check
        print(f"FAIL: toolkit smoke: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
