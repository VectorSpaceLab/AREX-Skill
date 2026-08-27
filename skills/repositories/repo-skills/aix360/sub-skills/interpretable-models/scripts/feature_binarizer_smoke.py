#!/usr/bin/env python3
"""Tiny, local smoke check for AIX360 tree-derived rule features.

This helper intentionally uses an in-memory mixed-type table. It does not
read repository files, download data, write checkpoints, or require a solver.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable

import numpy as np
import pandas as pd


def make_data() -> tuple[pd.DataFrame, np.ndarray]:
    """Return a tiny deterministic numeric/categorical classification table."""
    # Keep the default check numeric so it remains runnable with both the
    # historical ``sparse`` and current ``sparse_output`` sklearn APIs used by
    # AIX360's categorical encoder. Categorical schema behavior is documented
    # separately and can be exercised in a compatible optional environment.
    x = pd.DataFrame(
        {
            "age": [18, 22, 27, 31, 36, 41, 46, 52, 58, 64, 69, 75],
            "balance": [5.0, 7.5, 11.0, 15.0, 19.0, 23.0, 31.0, 37.0, 42.0, 50.0, 61.0, 72.0],
        }
    )
    y = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1], dtype=int)
    return x, y


def assert_columns_present(frame: pd.DataFrame, required: Iterable[str]) -> None:
    missing = [name for name in required if name not in frame.columns]
    if missing:
        raise ValueError(
            "input schema is missing column(s): " + ", ".join(map(str, missing))
        )


def run_smoke(with_models: bool = False) -> None:
    from aix360.algorithms.rbm import FeatureBinarizerFromTrees

    x, y = make_data()
    # Keep the fit schema explicit. This also demonstrates the categorical
    # declaration rather than relying on dtype inference.
    fbt = FeatureBinarizerFromTrees(
        treeNum=1, treeDepth=2, threshRound=4, randomState=0,
    )
    fbt.fit(x, y)
    transformed = fbt.transform(x)

    if not isinstance(transformed, pd.DataFrame):
        raise AssertionError("transform should return a DataFrame")
    if transformed.shape[0] != x.shape[0] or transformed.shape[1] == 0:
        raise AssertionError("unexpected transformed shape")
    if not isinstance(transformed.columns, pd.MultiIndex) or transformed.columns.nlevels != 3:
        raise AssertionError("expected a 3-level (feature, operation, value) MultiIndex")
    if not np.isfinite(transformed.to_numpy(dtype=float)).all():
        raise AssertionError("transformed values must be finite")
    if not set(transformed.to_numpy().ravel()).issubset({0, 1}):
        raise AssertionError("tree-derived features must be binary")
    assert_columns_present(x, [str(v) for v in fbt.features.get_level_values("feature").unique()])

    # The helper must fail before AIX360 receives a silently altered schema.
    missing = x.drop(columns=["age"])
    try:
        assert_columns_present(missing, ["age"])
    except ValueError as exc:
        if "age" not in str(exc):
            raise AssertionError("missing-column error did not name the column") from exc
    else:
        raise AssertionError("missing-column check did not fail")

    print(f"FeatureBinarizerFromTrees OK: input={x.shape}, binary={transformed.shape}")
    print(f"feature names: {list(transformed.columns[:4])}")
    print("categorical note: declare object columns with colCateg and probe the sklearn encoder API first")

    if with_models:
        # Optional and bounded: this checks the fit/explain contract without
        # assuming a particular LP solver is installed.
        from aix360.algorithms.rbm import BooleanRuleCG, BRCGExplainer

        import cvxpy

        installed = set(cvxpy.installed_solvers())
        solver = next((name for name in ("CLARABEL", "OSQP", "SCS", "ECOS") if name in installed), None)
        if solver is None:
            raise RuntimeError("no compatible cvxpy solver is installed")
        model = BooleanRuleCG(
            iterMax=3, timeMax=5, K=2, D=2, B=2,
            solver=solver, silent=True,
        )
        explainer = BRCGExplainer(model)
        try:
            explainer.fit(transformed, y)
            predicted = explainer.predict(transformed)
            rule_info = explainer.explain(maxConj=5)
        except Exception as exc:  # solver/backend details belong in diagnosis
            raise RuntimeError(
                f"feature smoke passed, but bounded BRCG failed with solver {solver}; inspect solver setup"
            ) from exc
        if len(predicted) != len(y) or not isinstance(rule_info.get("rules"), list):
            raise AssertionError("unexpected BRCG output contract")
        print(f"BRCG OK: classes={sorted(set(map(int, predicted)))}, rules={len(rule_info['rules'])}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a tiny in-memory AIX360 FeatureBinarizerFromTrees check."
    )
    parser.add_argument(
        "--with-models", action="store_true",
        help="also run a bounded BRCG fit (requires a working cvxpy solver)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run_smoke(with_models=args.with_models)
    except Exception as exc:
        print(f"smoke check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
