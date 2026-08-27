#!/usr/bin/env python3
"""Small package smoke for the imbalanced-learn runtime skill.

This script checks core imports and a few tiny end-to-end behaviors without
running the repository's native test suite.
"""

from __future__ import annotations

from collections import Counter

from sklearn.datasets import make_classification, load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import train_test_split

from imblearn import FunctionSampler
from imblearn.combine import SMOTEENN
from imblearn.datasets import make_imbalance
from imblearn.ensemble import BalancedRandomForestClassifier
from imblearn.metrics import classification_report_imbalanced, geometric_mean_score
from imblearn.model_selection import InstanceHardnessCV
from imblearn.over_sampling import RandomOverSampler, SMOTE
from imblearn.pipeline import make_pipeline
from imblearn.under_sampling import RandomUnderSampler


def _maybe_run_optional_batch_generators(X, y):
    try:
        from imblearn.keras import BalancedBatchGenerator
        from imblearn.tensorflow import balanced_batch_generator
    except Exception as exc:  # pragma: no cover - optional backend path
        print("optional_batch_generators_skipped", type(exc).__name__)
        return

    gen = BalancedBatchGenerator(
        X,
        y,
        sampler=RandomUnderSampler(random_state=0),
        batch_size=16,
        random_state=0,
    )
    xb, yb = gen[0]
    print("keras_batch", xb.shape, yb.shape, sorted(Counter(yb).items()))

    tf_gen, steps = balanced_batch_generator(
        X,
        y,
        sampler=RandomUnderSampler(random_state=0),
        batch_size=16,
        random_state=0,
    )
    xb2, yb2 = next(tf_gen)
    print("tf_steps", steps, xb2.shape, yb2.shape, sorted(Counter(yb2).items()))


def main() -> int:
    X, y = make_classification(
        n_samples=120,
        n_features=6,
        n_informative=3,
        weights=[0.2, 0.8],
        random_state=0,
    )

    X_ros, y_ros = RandomOverSampler(random_state=0).fit_resample(X, y)
    print("ros", X_ros.shape, sorted(Counter(y_ros).items()))

    X_smote, y_smote = SMOTE(random_state=0).fit_resample(X, y)
    print("smote", X_smote.shape, sorted(Counter(y_smote).items()))

    X_combo, y_combo = SMOTEENN(random_state=0).fit_resample(X, y)
    print("smoteenn", X_combo.shape, sorted(Counter(y_combo).items()))

    pipe = make_pipeline(
        RandomUnderSampler(random_state=0),
        LogisticRegression(max_iter=1000),
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, random_state=0, stratify=y
    )
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    print("pipe_bal_acc", round(balanced_accuracy_score(y_test, y_pred), 3))
    print("pipe_gmean", round(geometric_mean_score(y_test, y_pred), 3))
    print(
        "report_has_avg",
        "avg / total" in classification_report_imbalanced(y_test, y_pred),
    )

    iris = load_iris(as_frame=True)
    X_imb, y_imb = make_imbalance(
        iris.data, iris.target, sampling_strategy={0: 10}, random_state=42
    )
    print("make_imbalance", X_imb.shape, len(y_imb))

    sampler = FunctionSampler(func=lambda X, y: (X[:10], y[:10]))
    X_fun, y_fun = sampler.fit_resample(X, y)
    print("function_sampler", X_fun.shape, len(y_fun))

    clf = BalancedRandomForestClassifier(n_estimators=10, random_state=0)
    clf.fit(X_train, y_train)
    print("brf", clf.predict(X_test).shape)

    ih_cv = InstanceHardnessCV(LogisticRegression(max_iter=1000), n_splits=3)
    folds = list(ih_cv.split(X_train, y_train))
    print("ihcv_folds", len(folds))

    _maybe_run_optional_batch_generators(X, y)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
