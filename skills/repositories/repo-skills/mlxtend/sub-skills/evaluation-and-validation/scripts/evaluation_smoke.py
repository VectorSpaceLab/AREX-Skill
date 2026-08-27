#!/usr/bin/env python
"""Deterministic CPU smoke checks for mlxtend.evaluate.

Run examples:
  python evaluation_smoke.py --task metrics
  python evaluation_smoke.py --task all
"""

from __future__ import annotations

import argparse
import warnings

import numpy as np
from sklearn.datasets import load_iris, make_classification
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from mlxtend.evaluate import (
    BootstrapOutOfBag,
    GroupTimeSeriesSplit,
    PredefinedHoldoutSplit,
    RandomHoldoutSplit,
    accuracy_score,
    bias_variance_decomp,
    bootstrap,
    bootstrap_point632_score,
    cochrans_q,
    combined_ftest_5x2cv,
    confusion_matrix,
    create_counterfactual,
    feature_importance_permutation,
    ftest,
    lift_score,
    mcnemar,
    mcnemar_table,
    paired_ttest_5x2cv,
    paired_ttest_kfold_cv,
    paired_ttest_resampled,
    permutation_test,
    proportion_difference,
    scoring,
)

warnings.filterwarnings("ignore", category=RuntimeWarning)


def _assert_probability(value: float) -> None:
    assert np.isfinite(value), value
    assert 0.0 <= float(value) <= 1.0, value


def run_metrics() -> None:
    y_true = np.array([0, 1, 1, 0, 2, 2, 1, 0])
    y_pred = np.array([0, 1, 0, 0, 2, 1, 1, 0])

    acc = accuracy_score(y_true, y_pred, method="standard")
    balanced = accuracy_score(y_true, y_pred, method="balanced")
    cm = confusion_matrix(y_true, y_pred)

    y_bin = np.array([0, 1, 1, 0, 1, 0])
    pred_bin = np.array([0, 1, 0, 0, 1, 1])
    f1 = scoring(y_bin, pred_bin, metric="f1", positive_label=1)
    lift = lift_score(y_bin, pred_bin, binary=True, positive_label=1)
    z_stat, prop_p = proportion_difference(0.80, 0.65, n_1=40, n_2=40)

    assert np.isclose(acc, 0.75)
    assert 0.0 <= balanced <= 1.0
    assert cm.shape == (3, 3)
    _assert_probability(f1)
    assert lift > 0.0
    assert np.isfinite(z_stat)
    _assert_probability(prop_p)

    print(
        "metrics: "
        f"accuracy={acc:.3f} balanced={balanced:.3f} "
        f"cm_shape={cm.shape} f1={f1:.3f} lift={lift:.3f}"
    )


def run_bootstrap() -> None:
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    original, std_err, ci_bounds = bootstrap(
        x, np.mean, num_rounds=25, ci=0.80, seed=7
    )
    assert np.isclose(original, 3.0)
    assert std_err >= 0.0
    assert ci_bounds[0] <= original <= ci_bounds[1]

    X_idx = np.arange(24).reshape(12, 2)
    oob = BootstrapOutOfBag(n_splits=3, random_seed=4)
    oob_splits = list(oob.split(X_idx))
    assert len(oob_splits) == 3
    assert all(train.shape[0] == X_idx.shape[0] for train, _ in oob_splits)

    X, y = make_classification(
        n_samples=60,
        n_features=4,
        n_informative=2,
        n_redundant=0,
        n_clusters_per_class=1,
        flip_y=0.08,
        random_state=9,
    )
    estimator = LogisticRegression(solver="liblinear", random_state=0)
    point632_scores = bootstrap_point632_score(
        estimator, X, y, n_splits=5, method="oob", random_seed=3
    )
    assert point632_scores.shape == (5,)
    assert np.all((point632_scores >= 0.0) & (point632_scores <= 1.0))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=2, stratify=y
    )
    avg_loss, avg_bias, avg_var = bias_variance_decomp(
        DecisionTreeClassifier(max_depth=2, random_state=1),
        X_train,
        y_train,
        X_test,
        y_test,
        loss="0-1_loss",
        num_rounds=5,
        random_seed=2,
    )
    assert 0.0 <= avg_loss <= 1.0
    assert 0.0 <= avg_bias <= 1.0
    assert 0.0 <= avg_var <= 1.0

    perm_p = permutation_test(
        [4, 5, 6], [1, 2, 3], func="x_mean > y_mean", method="exact"
    )
    _assert_probability(perm_p)

    fitted = LogisticRegression(solver="liblinear", random_state=0).fit(
        X_train, y_train
    )
    imp_mean, imp_all = feature_importance_permutation(
        X_test.copy(),
        y_test,
        fitted.predict,
        metric="accuracy",
        num_rounds=2,
        seed=2,
    )
    assert imp_mean.shape == (X_test.shape[1],)
    assert imp_all.shape == (X_test.shape[1], 2)

    iris = load_iris()
    clf = LogisticRegression(max_iter=500, random_state=0).fit(iris.data, iris.target)
    counterfact = create_counterfactual(
        x_reference=iris.data[15],
        y_desired=2,
        model=clf,
        X_dataset=iris.data,
        y_desired_proba=1.0,
        lammbda=10,
        random_seed=123,
    )
    assert counterfact.shape == iris.data[15].shape
    assert np.all(np.isfinite(counterfact))

    print(
        "bootstrap: "
        f"mean={original:.3f} se={std_err:.3f} "
        f"oob_splits={len(oob_splits)} point632_mean={point632_scores.mean():.3f} "
        f"perm_p={perm_p:.3f} importance_shape={imp_all.shape}"
    )


def run_model_comparison() -> None:
    X, y = make_classification(
        n_samples=80,
        n_features=5,
        n_informative=3,
        n_redundant=0,
        n_clusters_per_class=1,
        flip_y=0.10,
        class_sep=0.80,
        random_state=11,
    )
    est1 = DummyClassifier(strategy="most_frequent")
    est2 = LogisticRegression(solver="liblinear", random_state=1)

    t5, p5 = paired_ttest_5x2cv(est1, est2, X, y, scoring="accuracy", random_seed=3)
    fk, pk = paired_ttest_kfold_cv(
        est1, est2, X, y, cv=3, scoring="accuracy", shuffle=True, random_seed=3
    )
    tr, pr = paired_ttest_resampled(
        est1,
        est2,
        X,
        y,
        num_rounds=5,
        test_size=0.35,
        scoring="accuracy",
        random_seed=3,
    )
    f5, pf5 = combined_ftest_5x2cv(
        est1, est2, X, y, scoring="accuracy", random_seed=3
    )

    for stat, pvalue in [(t5, p5), (fk, pk), (tr, pr), (f5, pf5)]:
        assert np.isfinite(stat), stat
        _assert_probability(pvalue)

    y_true = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    y_m0 = np.array([0, 1, 0, 0, 0, 1, 1, 0, 0, 0])
    y_m1 = np.array([0, 0, 1, 1, 0, 1, 1, 0, 0, 0])
    y_m2 = np.array([0, 1, 1, 1, 0, 1, 0, 0, 0, 0])

    table = mcnemar_table(y_true, y_m0, y_m1)
    chi2, mcnemar_p = mcnemar(table, exact=True)
    q_stat, q_p = cochrans_q(y_true, y_m0, y_m1, y_m2)
    f_stat, f_p = ftest(y_true, y_m0, y_m1, y_m2)

    assert chi2 is None
    assert table.shape == (2, 2)
    for stat, pvalue in [(q_stat, q_p), (f_stat, f_p)]:
        assert np.isfinite(stat), stat
        _assert_probability(pvalue)
    _assert_probability(mcnemar_p)

    print(
        "model-comparison: "
        f"5x2_t={t5:.3f}/{p5:.3f} "
        f"kfold_t={fk:.3f}/{pk:.3f} "
        f"combined_f={f5:.3f}/{pf5:.3f} "
        f"mcnemar_p={mcnemar_p:.3f} cochran_p={q_p:.3f}"
    )


def run_time_series() -> None:
    X = np.array(
        [[0], [7], [6], [4], [4], [8], [0], [6], [2], [0], [5], [9], [7], [7], [7], [7]]
    )
    y = np.array([1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0])
    groups = np.array([0, 1, 1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5, 5, 5, 5])

    cv = GroupTimeSeriesSplit(test_size=1, train_size=3)
    splits = list(cv.split(X, y, groups=groups))
    assert cv.get_n_splits() == 3
    assert len(splits) == 3
    assert all(train.size > 0 and test.size > 0 for train, test in splits)

    holdout_X = np.arange(24).reshape(12, 2)
    holdout_y = np.array([0, 1] * 6)
    random_holdout = RandomHoldoutSplit(valid_size=0.25, random_seed=5)
    rh_train, rh_valid = next(random_holdout.split(holdout_X, holdout_y))
    assert random_holdout.get_n_splits() == 1
    assert rh_train.size + rh_valid.size == holdout_X.shape[0]

    predefined = PredefinedHoldoutSplit(valid_indices=[0, 2, 4])
    ph_train, ph_valid = next(predefined.split(holdout_X, holdout_y))
    assert predefined.get_n_splits() == 1
    assert np.array_equal(ph_valid, np.array([0, 2, 4]))
    assert ph_train.size + ph_valid.size == holdout_X.shape[0]

    print(
        "time-series: "
        f"group_splits={len(splits)} first_train={splits[0][0].tolist()} "
        f"first_test={splits[0][1].tolist()} holdout_valid={rh_valid.size}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task",
        choices=("metrics", "bootstrap", "model-comparison", "time-series", "all"),
        default="all",
        help="Smoke-check task to run.",
    )
    args = parser.parse_args()

    if args.task in {"metrics", "all"}:
        run_metrics()
    if args.task in {"bootstrap", "all"}:
        run_bootstrap()
    if args.task in {"model-comparison", "all"}:
        run_model_comparison()
    if args.task in {"time-series", "all"}:
        run_time_series()

    print(f"evaluation smoke completed: task={args.task}")


if __name__ == "__main__":
    main()
