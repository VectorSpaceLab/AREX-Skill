#!/usr/bin/env python3
"""Run tiny pomegranate mixture-model and BayesClassifier smoke checks."""

from __future__ import annotations

import torch

from pomegranate.bayes_classifier import BayesClassifier
from pomegranate.distributions import Normal
from pomegranate.gmm import GeneralMixtureModel


def main() -> int:
    torch.manual_seed(0)
    X = torch.tensor(
        [[0.0, 0.2], [0.3, 0.1], [4.8, 5.2], [5.1, 4.7], [5.3, 5.0]],
        dtype=torch.float32,
    )

    gmm = GeneralMixtureModel(
        [Normal(covariance_type="diag"), Normal(covariance_type="diag")],
        init="first-k",
        max_iter=10,
        tol=1e-4,
        random_state=0,
    ).fit(X)
    mixture_labels = gmm.predict(X)
    mixture_probs = gmm.predict_proba(X)
    assert mixture_labels.shape == (len(X),)
    assert mixture_probs.shape == (len(X), 2)

    y = torch.tensor([0, 0, 1, 1, 1])
    classifier = BayesClassifier(
        [Normal(covariance_type="diag"), Normal(covariance_type="diag")]
    ).fit(X, y)
    class_labels = classifier.predict(X)
    class_probs = classifier.predict_proba(X)
    assert class_labels.shape == (len(X),)
    assert class_probs.shape == (len(X), 2)

    print("mixture/classifier smoke passed")
    print("GMM labels:", mixture_labels.detach().cpu().tolist())
    print("BayesClassifier labels:", class_labels.detach().cpu().tolist())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
