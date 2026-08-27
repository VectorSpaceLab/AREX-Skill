#!/usr/bin/env python3
"""Small, CPU-safe smoke check for PhySO's shipped benchmark loaders."""

from __future__ import annotations

import sys
import warnings

# PhySO may warn when system LaTeX is unavailable; that is not a loader failure.
warnings.filterwarnings("ignore", message=r"Latex display is not available.*")


def main() -> int:
    try:
        import numpy as np
        import physo.benchmark.ClassDataset.ClassProblem as Cls
        import physo.benchmark.FeynmanDataset.FeynmanProblem as Feyn

        np.random.seed(0)

        feyn_pb = Feyn.FeynmanProblem(i_eq=0)
        feyn_X, feyn_y = feyn_pb.generate_data_points(n_samples=3)
        if feyn_X.shape != (feyn_pb.n_vars, 3) or feyn_y.shape != (3,):
            raise AssertionError(
                f"unexpected Feynman shapes: X={feyn_X.shape}, y={feyn_y.shape}"
            )
        if not np.allclose(feyn_y, feyn_pb.target_function(feyn_X)):
            raise AssertionError("Feynman target re-evaluation disagreed")
        feyn_prefix = feyn_pb.get_prefix_expression()

        class_pb = Cls.ClassProblem(i_eq=0)
        class_X, class_y, class_K = class_pb.generate_data_points(
            n_samples=3, n_realizations=2, return_K=True
        )
        expected_X = (2, class_pb.n_vars, 3)
        expected_y = (2, 3)
        expected_K = (2, class_pb.n_spe)
        if (class_X.shape, class_y.shape, class_K.shape) != (
            expected_X,
            expected_y,
            expected_K,
        ):
            raise AssertionError(
                "unexpected Class shapes: "
                f"multi_X={class_X.shape}, multi_y={class_y.shape}, K={class_K.shape}"
            )
        for i_real in range(2):
            if not np.allclose(
                class_y[i_real], class_pb.target_function(class_X[i_real], class_K[i_real])
            ):
                raise AssertionError(f"Class target re-evaluation failed for realization {i_real}")
        class_prefix = class_pb.get_prefix_expression()

        print(
            f"Feynman index=0 name={feyn_pb.eq_name} "
            f"X_names={tuple(feyn_pb.X_names)} y_name={feyn_pb.y_name} "
            f"X_shape={feyn_X.shape} y_shape={feyn_y.shape} "
            f"prefix_len={len(feyn_prefix['tokens_str'])}"
        )
        print(
            f"Class index=0 name={class_pb.eq_name} "
            f"X_names={tuple(class_pb.X_names)} K_names={tuple(class_pb.K_names)} "
            f"y_name={class_pb.y_name} multi_X_shape={class_X.shape} "
            f"multi_y_shape={class_y.shape} K_shape={class_K.shape} "
            f"prefix_len={len(class_prefix['tokens_str'])}"
        )
        print("benchmark loader smoke: PASS")
        return 0
    except Exception as exc:  # clear failure signal for shell and agent callers
        print(
            f"benchmark loader smoke: FAIL: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
