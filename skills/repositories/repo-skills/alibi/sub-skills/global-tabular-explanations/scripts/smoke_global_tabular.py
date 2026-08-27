#!/usr/bin/env python3
"""Tiny CPU smoke for Alibi global tabular explanation workflows.

Runs a deterministic iris / logistic-regression smoke that touches ALE,
partial dependence, PD variance, and permutation importance.
"""
from __future__ import annotations

import sys

from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression

from alibi.explainers import ALE, PartialDependence, PartialDependenceVariance, PermutationImportance


def main() -> int:
    iris = load_iris()
    X = iris.data
    y = iris.target
    feature_names = iris.feature_names
    target_names = iris.target_names.tolist()

    clf = LogisticRegression(max_iter=200, random_state=0).fit(X, y)

    ale = ALE(clf.predict_proba, feature_names=feature_names, target_names=target_names)
    ale_exp = ale.explain(X[:10], features=[0, 1])

    pd = PartialDependence(clf.predict_proba, feature_names=feature_names, target_names=target_names)
    pd_exp = pd.explain(X[:10], features=[0, 1], kind='average', grid_resolution=5)

    pdv = PartialDependenceVariance(clf.predict_proba, feature_names=feature_names, target_names=target_names)
    pdv_importance = pdv.explain(X[:10], method='importance', features=[0, 1])
    pdv_interaction = pdv.explain(X[:10], method='interaction', features=[(0, 1)])

    pfi = PermutationImportance(clf.predict, score_fns='accuracy', feature_names=feature_names)
    pfi_exp = pfi.explain(X[:20], y[:20], features=[0, 1], method='estimate', kind='difference', n_repeats=3)

    print('alibi global tabular smoke: ok')
    print('ALE features:', len(ale_exp.ale_values))
    print('PD features:', len(pd_exp.pd_values))
    print('PD variance importance rows:', len(pdv_importance.feature_importance))
    print('PD variance interaction rows:', len(pdv_interaction.feature_interaction))
    print('Permutation metrics:', len(pfi_exp.feature_importance))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
