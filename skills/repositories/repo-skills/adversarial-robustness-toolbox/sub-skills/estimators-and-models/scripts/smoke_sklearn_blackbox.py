#!/usr/bin/env python3
"""No-download smoke check for ART sklearn and black-box classifier wrappers."""

from __future__ import annotations

import argparse
import sys

import numpy as np


def run_smoke(verbose: bool = False) -> None:
    from sklearn.datasets import load_iris
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import MinMaxScaler

    from art.estimators.classification import BlackBoxClassifier, SklearnClassifier
    from art.utils import to_categorical

    iris = load_iris()
    x = iris.data.astype(np.float32)
    y_index = iris.target.astype(np.int64)
    x = MinMaxScaler().fit_transform(x).astype(np.float32)
    nb_classes = int(np.max(y_index)) + 1
    y_one_hot = to_categorical(y_index, nb_classes=nb_classes).astype(np.float32)

    base_model = LogisticRegression(max_iter=300, random_state=7)
    sklearn_classifier = SklearnClassifier(model=base_model, clip_values=(0.0, 1.0))
    sklearn_classifier.fit(x, y_one_hot)

    probe = x[:5]
    sklearn_pred = sklearn_classifier.predict(probe)
    assert sklearn_pred.shape == (len(probe), nb_classes), sklearn_pred.shape
    assert np.isfinite(sklearn_pred).all()
    assert sklearn_classifier.input_shape == (x.shape[1],)

    blackbox_classifier = BlackBoxClassifier(
        predict_fn=base_model.predict_proba,
        input_shape=(x.shape[1],),
        nb_classes=nb_classes,
        clip_values=(0.0, 1.0),
    )
    blackbox_pred = blackbox_classifier.predict(probe)
    assert blackbox_pred.shape == (len(probe), nb_classes), blackbox_pred.shape
    assert np.isfinite(blackbox_pred).all()
    np.testing.assert_allclose(blackbox_pred, sklearn_pred, rtol=1e-5, atol=1e-6)

    try:
        blackbox_classifier.fit(probe, y_one_hot[: len(probe)])
    except NotImplementedError:
        pass
    else:  # pragma: no cover - contract regression guard
        raise AssertionError("BlackBoxClassifier.fit unexpectedly succeeded")

    if verbose:
        print("sklearn prediction shape:", sklearn_pred.shape)
        print("black-box prediction shape:", blackbox_pred.shape)
    print("OK: sklearn and black-box classifier wrappers produced finite matching predictions")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="Print prediction shapes in addition to the OK line.")
    args = parser.parse_args(argv)
    run_smoke(verbose=args.verbose)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - command-line diagnostics
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
