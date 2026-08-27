#!/usr/bin/env python3
"""Tiny CPU smoke for Alibi base workflows.

This helper is deterministic and safe by default.
It exercises the base tabular explanation path on the iris dataset.
"""
from __future__ import annotations

import sys
from typing import Any

import numpy as np
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression

from alibi.explainers import ALE, AnchorTabular, PartialDependence, PermutationImportance


def _run_smoke() -> dict[str, Any]:
    iris = load_iris()
    X = iris.data
    y = iris.target
    feature_names = iris.feature_names
    target_names = iris.target_names.tolist()

    clf = LogisticRegression(max_iter=200, random_state=0).fit(X, y)

    ale = ALE(clf.predict_proba, feature_names=feature_names, target_names=target_names)
    ale_exp = ale.explain(X[:12], features=[0, 1])

    pd = PartialDependence(clf.predict_proba, feature_names=feature_names, target_names=target_names)
    pd_exp = pd.explain(X[:12], features=[0, 1], kind='average', grid_resolution=5)

    pfi = PermutationImportance(clf.predict, score_fns='accuracy', feature_names=feature_names)
    pfi_exp = pfi.explain(X[:20], y[:20], features=[0, 1], method='estimate', kind='difference', n_repeats=3)

    anchor = AnchorTabular(clf.predict_proba, feature_names=feature_names)
    anchor.fit(X, disc_perc=(25, 50, 75))
    anchor_exp = anchor.explain(X[0], threshold=0.95)

    return {
        'ale_features': len(ale_exp.ale_values),
        'pd_features': len(pd_exp.pd_values),
        'pfi_metrics': len(pfi_exp.feature_importance),
        'anchor_terms': len(getattr(anchor_exp, 'anchor', [])),
    }


def main() -> int:
    try:
        results = _run_smoke()
    except Exception as exc:  # pragma: no cover - diagnostic helper
        print(f'core smoke failed: {exc}', file=sys.stderr)
        raise

    print('alibi core smoke: ok')
    for key, value in results.items():
        print(f'- {key}: {value}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
