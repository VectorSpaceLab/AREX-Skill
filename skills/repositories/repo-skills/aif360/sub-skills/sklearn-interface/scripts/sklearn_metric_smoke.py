#!/usr/bin/env python3
"""In-memory smoke for AIF360 sklearn fairness metrics.

The fixture uses pandas DataFrame/Series objects with protected attributes in a
MultiIndex. It performs no network calls and does not use AIF360 dataset fetchers.
"""

from __future__ import annotations

import argparse
import json
import logging
from typing import Any, Callable, Dict

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny no-network smoke for aif360.sklearn metrics using "
            "pandas protected attributes stored in the index."
        )
    )
    parser.add_argument(
        "--try-ot",
        action="store_true",
        help=(
            "Also attempt optional ot_distance. If POT/aif360[OptimalTransport] "
            "is unavailable, record a skipped status instead of failing."
        ),
    )
    parser.add_argument(
        "--show-import-warnings",
        action="store_true",
        help="Show optional dependency warnings emitted during AIF360 imports.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of pretty-printed JSON.",
    )
    return parser.parse_args()


def import_aif360_metrics(show_import_warnings: bool) -> Dict[str, Callable[..., Any]]:
    if not show_import_warnings:
        logging.disable(logging.WARNING)
    try:
        from aif360.sklearn.metrics import (
            average_odds_difference,
            average_odds_error,
            consistency_score,
            difference,
            disparate_impact_ratio,
            equal_opportunity_difference,
            make_scorer,
            mdss_bias_score,
            ot_distance,
            ratio,
            statistical_parity_difference,
        )
    finally:
        if not show_import_warnings:
            logging.disable(logging.NOTSET)

    return {
        "average_odds_difference": average_odds_difference,
        "average_odds_error": average_odds_error,
        "consistency_score": consistency_score,
        "difference": difference,
        "disparate_impact_ratio": disparate_impact_ratio,
        "equal_opportunity_difference": equal_opportunity_difference,
        "make_scorer": make_scorer,
        "mdss_bias_score": mdss_bias_score,
        "ot_distance": ot_distance,
        "ratio": ratio,
        "statistical_parity_difference": statistical_parity_difference,
    }


def build_fixture() -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    sex = ["Female", "Female", "Female", "Female", "Male", "Male", "Male", "Male"]
    race = ["GroupA", "GroupB", "GroupA", "GroupB", "GroupA", "GroupB", "GroupA", "GroupB"]
    index = pd.MultiIndex.from_arrays([sex, race], names=["sex", "race"])

    X = pd.DataFrame(
        {
            "credit_score": [0.95, 0.80, 0.30, 0.25, 0.88, 0.45, 0.35, 0.20],
            "debt_ratio": [0.10, 0.20, 0.70, 0.80, 0.15, 0.65, 0.60, 0.90],
        },
        index=index,
    )
    y = pd.Series([1, 1, 0, 0, 1, 0, 0, 0], index=index, name="approved")
    sample_weight = pd.Series(
        [1.0, 1.2, 0.9, 1.1, 1.0, 1.0, 1.3, 0.8],
        index=index,
        name="sample_weight",
    )
    return X, y, sample_weight


def to_builtin(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_builtin(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_builtin(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def main() -> int:
    args = parse_args()
    metrics = import_aif360_metrics(args.show_import_warnings)

    X, y, sample_weight = build_fixture()
    model = LogisticRegression(solver="liblinear", random_state=0)
    model.fit(X, y, sample_weight=sample_weight)
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)[:, 1]

    priv_group = "Male"
    pos_label = 1

    stat_parity_scorer = metrics["make_scorer"](
        metrics["statistical_parity_difference"],
        prot_attr="sex",
        priv_group=priv_group,
        pos_label=pos_label,
    )
    di_scorer = metrics["make_scorer"](
        metrics["disparate_impact_ratio"],
        is_ratio=True,
        prot_attr="sex",
        priv_group=priv_group,
        pos_label=pos_label,
        zero_division=0,
    )

    result: Dict[str, Any] = {
        "status": "ok",
        "n_samples": int(len(y)),
        "protected_index_names": list(X.index.names),
        "prot_attr_used": "sex",
        "priv_group": priv_group,
        "pos_label": pos_label,
        "model_predictions": y_pred.tolist(),
        "metrics": {
            "statistical_parity_difference": metrics["statistical_parity_difference"](
                y, y_pred, prot_attr="sex", priv_group=priv_group, pos_label=pos_label, sample_weight=sample_weight
            ),
            "disparate_impact_ratio": metrics["disparate_impact_ratio"](
                y, y_pred, prot_attr="sex", priv_group=priv_group, pos_label=pos_label, sample_weight=sample_weight, zero_division=0
            ),
            "equal_opportunity_difference": metrics["equal_opportunity_difference"](
                y, y_pred, prot_attr="sex", priv_group=priv_group, pos_label=pos_label, sample_weight=sample_weight
            ),
            "average_odds_difference": metrics["average_odds_difference"](
                y, y_pred, prot_attr="sex", priv_group=priv_group, pos_label=pos_label, sample_weight=sample_weight
            ),
            "average_odds_error": metrics["average_odds_error"](
                y, y_pred, prot_attr="sex", priv_group=priv_group, pos_label=pos_label, sample_weight=sample_weight
            ),
            "precision_difference": metrics["difference"](
                precision_score, y, y_pred, prot_attr="sex", priv_group=priv_group, pos_label=pos_label, sample_weight=sample_weight, zero_division=0
            ),
            "precision_ratio": metrics["ratio"](
                precision_score, y, y_pred, prot_attr="sex", priv_group=priv_group, pos_label=pos_label, sample_weight=sample_weight, zero_division=0
            ),
            "consistency_score": metrics["consistency_score"](X, y, n_neighbors=3),
            "mdss_bias_score_full_set": metrics["mdss_bias_score"](y, y_proba, pos_label=pos_label),
            "make_scorer_statistical_parity": stat_parity_scorer(model, X, y),
            "make_scorer_disparate_impact": di_scorer(model, X, y),
        },
        "notes": [
            "All data are synthetic and in-memory.",
            "Protected attributes live in pandas index levels named sex and race.",
            "No AIF360 fetchers or networked datasets are used.",
        ],
    }

    if args.try_ot:
        try:
            prot_attr = pd.Series(X.index.get_level_values("sex"), index=X.index, name="sex")
            result["metrics"]["optional_ot_distance"] = {
                "status": "ok",
                "value": metrics["ot_distance"](
                    y,
                    pd.Series(y_proba, index=y.index, name="score"),
                    prot_attr=prot_attr,
                    pos_label=pos_label,
                    mode="binary",
                    num_iters=100,
                ),
            }
        except Exception as exc:  # optional dependency or shape issues should not fail base smoke
            result["metrics"]["optional_ot_distance"] = {
                "status": "skipped",
                "reason": f"{exc.__class__.__name__}: {exc}",
            }

    print(json.dumps(to_builtin(result), indent=None if args.compact else 2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
