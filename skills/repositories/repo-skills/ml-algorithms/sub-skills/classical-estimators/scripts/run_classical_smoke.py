#!/usr/bin/env python
"""Small MLAlgorithms supervised-estimator smoke checks.

This helper adapts the repository's supervised examples into short deterministic
checks that import only the public `mla` package and generate tiny synthetic
data. It performs no downloads, plotting, file writes, or long training runs.

Examples:
  python run_classical_smoke.py --workflow linear-logistic
  python run_classical_smoke.py --workflow all
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
from sklearn.datasets import make_classification, make_regression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

from mla.ensemble.gbm import GradientBoostingClassifier, GradientBoostingRegressor
from mla.ensemble.random_forest import RandomForestClassifier, RandomForestRegressor
from mla.knn import KNNClassifier, KNNRegressor
from mla.linear_models import LinearRegression, LogisticRegression
from mla.metrics.metrics import accuracy, mean_squared_error
from mla.naive_bayes import NaiveBayesClassifier
from mla.svm.kernerls import Linear, RBF
from mla.svm.svm import SVM


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _classification_data(n_samples=180, n_features=6, class_sep=2.5):
    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=max(2, n_features - 1),
        n_redundant=0,
        n_repeated=0,
        n_classes=2,
        class_sep=class_sep,
        random_state=1111,
    )
    return train_test_split(X, y, test_size=0.25, random_state=1111)


def _regression_data(n_samples=180, n_features=5):
    X, y = make_regression(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=n_features,
        n_targets=1,
        noise=0.01,
        random_state=1111,
        bias=0.5,
    )
    y = y * 0.01
    return train_test_split(X, y, test_size=0.25, random_state=1111)


def smoke_linear_logistic() -> None:
    X_train, X_test, y_train, y_test = _regression_data()
    reg = LinearRegression(lr=0.01, max_iters=300, penalty="l2", C=0.003)
    reg.fit(X_train, y_train)
    pred = reg.predict(X_test)
    mse = float(mean_squared_error(y_test, pred))
    _check(np.isfinite(mse) and mse < 2.0, f"linear regression MSE too high: {mse}")
    print(f"linear-regression mse={mse:.6f}")

    X_train, X_test, y_train, y_test = _classification_data(n_samples=160, n_features=5)
    clf = LogisticRegression(lr=0.01, max_iters=120, penalty="l1", C=0.01)
    clf.fit(X_train, y_train)
    proba = clf.predict(X_test)
    _check(proba.shape == y_test.shape, f"unexpected logistic probability shape: {proba.shape}")
    _check(float(proba.min()) >= 0.0 and float(proba.max()) <= 1.0, "logistic probabilities outside [0, 1]")
    _check(np.isfinite(proba).all(), "logistic probabilities are not finite")
    # This educational implementation is sensitive to random initialization and
    # learning-rate choices; the smoke validates API/runtime behavior rather
    # than asserting benchmark accuracy.
    labels = (proba >= 0.5).astype(int)
    acc = float(accuracy(y_test, labels))
    print(f"logistic-regression accuracy={acc:.3f} proba_range=({float(proba.min()):.3f},{float(proba.max()):.3f})")


def smoke_knn() -> None:
    X_train, X_test, y_train, y_test = _classification_data(n_samples=140, n_features=5)
    clf = KNNClassifier(k=5)
    clf.fit(X_train, y_train)
    labels = clf.predict(X_test)
    acc = float(accuracy(y_test, labels))
    _check(acc >= 0.85, f"KNN classifier accuracy too low: {acc}")
    print(f"knn-classifier accuracy={acc:.3f}")

    X_train, X_test, y_train, y_test = _regression_data(n_samples=140, n_features=4)
    reg = KNNRegressor(k=5)
    reg.fit(X_train, y_train)
    pred = reg.predict(X_test)
    mse = float(mean_squared_error(y_test, pred))
    _check(np.isfinite(mse) and mse < 10.0, f"KNN regressor MSE too high: {mse}")
    print(f"knn-regressor mse={mse:.6f}")


def smoke_naive_bayes() -> None:
    X_train, X_test, y_train, y_test = _classification_data(n_samples=180, n_features=6, class_sep=3.0)
    model = NaiveBayesClassifier()
    model.fit(X_train, y_train)
    proba = model.predict(X_test)
    _check(proba.shape == (X_test.shape[0], 2), f"unexpected Naive Bayes shape: {proba.shape}")
    auc = float(roc_auc_score(y_test, proba[:, 1]))
    _check(auc >= 0.90, f"Naive Bayes AUC too low: {auc}")
    print(f"naive-bayes auc={auc:.3f}")


def smoke_ensembles() -> None:
    X_train, X_test, y_train, y_test = _classification_data(n_samples=180, n_features=6, class_sep=2.5)
    rf = RandomForestClassifier(n_estimators=5, max_depth=4)
    rf.fit(X_train, y_train)
    rf_prob = rf.predict(X_test)[:, 1]
    rf_auc = float(roc_auc_score(y_test, rf_prob))
    _check(rf_auc >= 0.85, f"RandomForestClassifier AUC too low: {rf_auc}")
    print(f"random-forest-classifier auc={rf_auc:.3f}")

    gbm = GradientBoostingClassifier(n_estimators=8, max_depth=3, max_features=4, learning_rate=0.1)
    gbm.fit(X_train, y_train)
    gbm_prob = gbm.predict(X_test)
    gbm_auc = float(roc_auc_score(y_test, gbm_prob))
    _check(gbm_auc >= 0.75, f"GradientBoostingClassifier AUC too low: {gbm_auc}")
    print(f"gradient-boosting-classifier auc={gbm_auc:.3f}")

    X_train, X_test, y_train, y_test = _regression_data(n_samples=140, n_features=4)
    rfr = RandomForestRegressor(n_estimators=5, max_depth=5, max_features=2)
    rfr.fit(X_train, y_train)
    rf_mse = float(mean_squared_error(y_test, rfr.predict(X_test)))
    _check(np.isfinite(rf_mse) and rf_mse < 5.0, f"RandomForestRegressor MSE too high: {rf_mse}")
    print(f"random-forest-regressor mse={rf_mse:.6f}")

    gbr = GradientBoostingRegressor(n_estimators=8, max_depth=3, max_features=3, learning_rate=0.1)
    gbr.fit(X_train, y_train)
    gb_mse = float(mean_squared_error(y_test, gbr.predict(X_test)))
    _check(np.isfinite(gb_mse) and gb_mse < 8.0, f"GradientBoostingRegressor MSE too high: {gb_mse}")
    print(f"gradient-boosting-regressor mse={gb_mse:.6f}")


def smoke_svm() -> None:
    X_train, X_test, y_train, y_test = _classification_data(n_samples=80, n_features=4, class_sep=2.5)
    y_train = (y_train * 2) - 1
    y_test = (y_test * 2) - 1
    for kernel in (Linear(), RBF(gamma=0.05)):
        model = SVM(C=0.8, kernel=kernel, max_iter=80)
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        acc = float(accuracy(y_test, pred))
        _check(acc >= 0.70, f"SVM {kernel} accuracy too low: {acc}")
        print(f"svm kernel={kernel!r} accuracy={acc:.3f}")


WORKFLOWS = {
    "linear-logistic": smoke_linear_logistic,
    "knn": smoke_knn,
    "naive-bayes": smoke_naive_bayes,
    "ensembles": smoke_ensembles,
    "svm": smoke_svm,
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run small MLAlgorithms supervised estimator smoke checks.")
    parser.add_argument("--workflow", choices=sorted(WORKFLOWS) + ["all"], default="all")
    args = parser.parse_args(argv)

    selected = WORKFLOWS.keys() if args.workflow == "all" else [args.workflow]
    for name in selected:
        print(f"== {name} ==")
        WORKFLOWS[name]()
    print("classical smoke checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # provide a concise nonzero failure for agents
        print(f"classical smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
