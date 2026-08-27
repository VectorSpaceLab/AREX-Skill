#!/usr/bin/env python3
"""Tiny balanced-ensemble smoke for imbalanced-learn."""

from __future__ import annotations

from collections import Counter

from sklearn.datasets import make_classification
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from imblearn.ensemble import (
    BalancedBaggingClassifier,
    BalancedRandomForestClassifier,
    EasyEnsembleClassifier,
    RUSBoostClassifier,
)


def main() -> int:
    X, y = make_classification(
        n_samples=200,
        n_features=8,
        n_informative=4,
        class_sep=1.5,
        weights=[0.2, 0.8],
        random_state=0,
    )
    print("data", sorted(Counter(y).items()))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, random_state=0, stratify=y
    )

    models = [
        ("balanced_bagging", BalancedBaggingClassifier(DecisionTreeClassifier(), random_state=0)),
        ("balanced_rf", BalancedRandomForestClassifier(n_estimators=10, random_state=0)),
        ("easy_ensemble", EasyEnsembleClassifier(random_state=0)),
        ("rusboost", RUSBoostClassifier(n_estimators=20, random_state=0)),
    ]
    for name, model in models:
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        print(name, pred.shape, round(balanced_accuracy_score(y_test, pred), 3))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
