#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
for parent in HERE.parents:
    if (parent / "physo" / "__init__.py").exists():
        sys.path.insert(0, str(parent))
        break
else:
    raise RuntimeError("Could not locate the repo root containing the physo package.")

import numpy as np
import torch

import physo
import physo.learn.monitoring as monitoring


def build_data() -> tuple[list[np.ndarray], list[np.ndarray], list[np.ndarray]]:
    x0_a = np.linspace(-1.0, 1.0, 8)
    y_a = 2.0 * x0_a + 0.50
    w_a = np.linspace(1.0, 2.0, len(y_a))

    x0_b = np.linspace(-0.8, 0.8, 5)
    y_b = 2.0 * x0_b - 0.25
    w_b = np.linspace(0.5, 1.0, len(y_b))

    multi_X = [
        np.stack((x0_a,), axis=0),
        np.stack((x0_b,), axis=0),
    ]
    multi_y = [y_a, y_b]
    multi_y_weights = [w_a, w_b]
    return multi_X, multi_y, multi_y_weights


def main() -> None:
    seed = 0
    np.random.seed(seed)
    torch.manual_seed(seed)

    multi_X, multi_y, multi_y_weights = build_data()
    assert len(multi_X) == len(multi_y) == len(multi_y_weights) == 2

    run_config = copy.deepcopy(physo.config.config0b.config0b)
    run_config["learning_config"]["batch_size"] = 64
    run_config["learning_config"]["n_epochs"] = 2
    run_config["free_const_opti_args"]["method_args"]["n_steps"] = 4
    run_config["priors_config"] = [
        prior for prior in run_config["priors_config"]
        if prior[0] not in {"NestedFunctions", "NestedTrigonometryPrior"}
    ]

    run_logger = lambda: monitoring.RunLogger(save_path="class_sr_smoke.log", do_save=False)
    run_visualiser = lambda: monitoring.RunVisualiser(
        epoch_refresh_rate=1,
        save_path="class_sr_smoke.png",
        do_show=False,
        do_prints=False,
        do_save=False,
    )

    try:
        best_expr, logger = physo.ClassSR(
            multi_X,
            multi_y,
            multi_y_weights=multi_y_weights,
            X_names=["x0"],
            X_units=[[0, 0, 0]],
            y_name="y",
            y_units=[0, 0, 0],
            fixed_consts=[1.0],
            fixed_consts_units=[[0, 0, 0]],
            class_free_consts_names=["c0"],
            class_free_consts_units=[[0, 0, 0]],
            class_free_consts_init_val=[1.0],
            spe_free_consts_names=["k0"],
            spe_free_consts_units=[[0, 0, 0]],
            spe_free_consts_init_val=[0.0],
            run_config=run_config,
            op_names=["add", "mul"],
            get_run_logger=run_logger,
            get_run_visualiser=run_visualiser,
            parallel_mode=False,
            device="cpu",
            epochs=2,
        )
    except Exception as exc:
        print(f"FAILED: ClassSR smoke run raised {exc!r}")
        raise

    complexities, programs, rewards, rmses = logger.get_pareto_front()
    if len(programs) == 0:
        raise RuntimeError("ClassSR smoke failed: empty Pareto front.")

    class_shape = tuple(best_expr.free_consts.class_values.shape)
    spe_shape = tuple(best_expr.free_consts.spe_values.shape)
    evaluated = best_expr.get_infix_sympy(evaluate_consts=True)
    if len(evaluated) != len(multi_X):
        raise RuntimeError(
            f"ClassSR smoke failed: expected {len(multi_X)} evaluated expressions, got {len(evaluated)}."
        )

    print(
        "OK ClassSR smoke: "
        f"pareto={len(programs)}, class_shape={class_shape}, spe_shape={spe_shape}, realizations={len(evaluated)}"
    )


if __name__ == "__main__":
    main()
