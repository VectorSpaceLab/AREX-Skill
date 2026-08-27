#!/usr/bin/env python3
"""Tiny CPU smoke for confidence, prototype, and persistence workflows.

Runs a deterministic iris / logistic-regression example and a small save/load round trip.
"""
from __future__ import annotations

import tempfile

import numpy as np
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression

from alibi.confidence import LinearityMeasure, TrustScore
from alibi.explainers import ALE
from alibi.prototypes import ProtoSelect
from alibi.saving import load_explainer, save_explainer
from alibi.utils.kernel import EuclideanDistance


def main() -> int:
    iris = load_iris()
    X = iris.data
    y = iris.target

    clf = LogisticRegression(max_iter=200, random_state=0).fit(X, y)

    ts = TrustScore()
    ts.fit(X, y, classes=3)
    score, closest = ts.score(X[:3], y[:3])

    lm = LinearityMeasure()
    lm.fit(X)
    lin = lm.score(clf.predict_proba, X[:2])

    ps = ProtoSelect(kernel_distance=EuclideanDistance(), eps=0.5, preprocess_fn=lambda x: x)
    ps.fit(X, y)
    summary = ps.summarise(num_prototypes=3)

    ale = ALE(clf.predict_proba, feature_names=iris.feature_names, target_names=iris.target_names.tolist())
    ale_exp = ale.explain(X[:10], features=[0, 1])

    with tempfile.TemporaryDirectory() as tmp:
        save_explainer(ale, tmp)
        loaded = load_explainer(tmp, predictor=clf.predict_proba)

    print('alibi confidence/prototypes smoke: ok')
    print('trust score shape:', score.shape)
    print('closest class shape:', closest.shape)
    print('linearity shape:', np.asarray(lin).shape)
    print('proto keys:', list(summary.data.keys()))
    print('ale features:', len(ale_exp.ale_values))
    print('reloaded type:', type(loaded).__name__)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
