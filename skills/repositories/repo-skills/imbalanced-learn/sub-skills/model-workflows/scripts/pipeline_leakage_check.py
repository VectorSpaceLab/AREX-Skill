#!/usr/bin/env python3
"""Tiny leakage-safe pipeline smoke for imbalanced-learn."""

from __future__ import annotations

from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import train_test_split

from imblearn.pipeline import make_pipeline
from imblearn.under_sampling import RandomUnderSampler


def main() -> int:
    X, y = make_classification(
        n_samples=160,
        n_features=6,
        n_informative=3,
        weights=[0.15, 0.85],
        random_state=0,
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, random_state=0, stratify=y
    )
    model = make_pipeline(
        RandomUnderSampler(random_state=0), LogisticRegression(max_iter=1000)
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    print("balanced_accuracy", round(balanced_accuracy_score(y_test, y_pred), 3))
    print("steps", list(model.named_steps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
