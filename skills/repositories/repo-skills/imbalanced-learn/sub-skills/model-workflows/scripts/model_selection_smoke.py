#!/usr/bin/env python3
"""Tiny InstanceHardnessCV smoke for imbalanced-learn."""

from __future__ import annotations

from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_validate

from imblearn.model_selection import InstanceHardnessCV


def main() -> int:
    X, y = make_classification(
        n_samples=180,
        n_features=6,
        n_informative=3,
        weights=[0.9, 0.1],
        class_sep=2,
        random_state=0,
    )
    clf = LogisticRegression(max_iter=1000)
    ih_cv = InstanceHardnessCV(estimator=clf, n_splits=3)
    result = cross_validate(clf, X, y, cv=ih_cv, scoring="balanced_accuracy")
    print("test_scores", [round(v, 3) for v in result["test_score"]])
    print("std", round(result["test_score"].std(), 3))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
