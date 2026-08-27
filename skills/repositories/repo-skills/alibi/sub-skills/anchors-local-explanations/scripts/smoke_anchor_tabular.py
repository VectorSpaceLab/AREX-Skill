#!/usr/bin/env python3
"""Tiny CPU smoke for AnchorTabular.

Runs a deterministic iris / logistic-regression example and prints a compact summary.
"""
from __future__ import annotations

import sys

from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression

from alibi.explainers import AnchorTabular


def main() -> int:
    iris = load_iris()
    X = iris.data
    y = iris.target

    clf = LogisticRegression(max_iter=200, random_state=0).fit(X, y)
    explainer = AnchorTabular(clf.predict_proba, feature_names=iris.feature_names)
    explainer.fit(X, disc_perc=(25, 50, 75))
    exp = explainer.explain(X[0], threshold=0.95)

    print('alibi anchor tabular smoke: ok')
    print('anchor:', getattr(exp, 'anchor', []))
    print('precision:', getattr(exp, 'precision', None))
    print('coverage:', getattr(exp, 'coverage', None))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
