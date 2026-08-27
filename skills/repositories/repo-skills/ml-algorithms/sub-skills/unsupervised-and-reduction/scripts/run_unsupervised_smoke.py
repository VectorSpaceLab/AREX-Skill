#!/usr/bin/env python
"""Small MLAlgorithms unsupervised/reduction smoke checks.

This helper adapts the repository's clustering, reduction, and RBM examples
into short deterministic checks that use only synthetic data. It performs no
plotting, downloads, or long training runs.

Examples:
  python run_unsupervised_smoke.py --workflow kmeans
  python run_unsupervised_smoke.py --workflow all
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
from sklearn.datasets import make_blobs, make_classification

from mla.gaussian_mixture import GaussianMixture
from mla.kmeans import KMeans
from mla.pca import PCA
from mla.rbm import RBM
from mla.tsne import TSNE


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def smoke_kmeans() -> None:
    X, y = make_blobs(n_samples=120, centers=3, n_features=2, random_state=42)
    model = KMeans(K=3, max_iters=40, init="++")
    model.fit(X)
    labels = model.predict()
    _check(labels.shape == (X.shape[0],), f"unexpected KMeans label shape: {labels.shape}")
    _check(len(set(labels.astype(int).tolist())) == 3, "KMeans did not produce 3 clusters")
    print(f"kmeans clusters={sorted(set(labels.astype(int).tolist()))}")


def smoke_gmm() -> None:
    X, _ = make_blobs(n_samples=120, centers=3, n_features=2, random_state=42)
    model = GaussianMixture(K=3, init="kmeans", max_iters=35)
    model.fit(X)
    assignments = model.predict(X)
    _check(assignments.shape == (X.shape[0],), f"unexpected GMM assignment shape: {assignments.shape}")
    _check(len(model.likelihood) >= 1, "GMM likelihood history is empty")
    print(f"gmm assignments={sorted(set(assignments.astype(int).tolist()))} likelihood_steps={len(model.likelihood)}")


def smoke_pca() -> None:
    X, _ = make_classification(n_samples=120, n_features=12, n_informative=6, random_state=42)
    X_train, X_test = X[:80], X[80:]
    model = PCA(4, solver="svd")
    model.fit(X_train)
    train_4 = model.transform(X_train)
    test_4 = model.transform(X_test)
    _check(train_4.shape == (80, 4), f"unexpected PCA train shape: {train_4.shape}")
    _check(test_4.shape == (40, 4), f"unexpected PCA test shape: {test_4.shape}")
    print(f"pca shapes={train_4.shape}->{test_4.shape}")


def smoke_tsne() -> None:
    X, _ = make_classification(n_samples=60, n_features=8, n_informative=4, random_state=42)
    embedding = TSNE(n_components=2, perplexity=8.0, max_iter=100, learning_rate=150).fit_transform(X)
    _check(embedding.shape == (60, 2), f"unexpected t-SNE shape: {embedding.shape}")
    print(f"tsne shape={embedding.shape}")


def smoke_rbm() -> None:
    X = np.random.RandomState(42).uniform(0, 1, (60, 8))
    model = RBM(n_hidden=4, learning_rate=0.05, batch_size=10, max_epochs=3)
    model.fit(X)
    features = model.predict(X)
    _check(features.shape == (60, 4), f"unexpected RBM feature shape: {features.shape}")
    _check(len(model.errors) == 3, f"unexpected RBM error history length: {len(model.errors)}")
    print(f"rbm features={features.shape} errors={len(model.errors)}")


WORKFLOWS = {
    "kmeans": smoke_kmeans,
    "gmm": smoke_gmm,
    "pca": smoke_pca,
    "tsne": smoke_tsne,
    "rbm": smoke_rbm,
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run small MLAlgorithms unsupervised/reduction smoke checks.")
    parser.add_argument("--workflow", choices=sorted(WORKFLOWS) + ["all"], default="all")
    args = parser.parse_args(argv)

    selected = WORKFLOWS.keys() if args.workflow == "all" else [args.workflow]
    for name in selected:
        print(f"== {name} ==")
        WORKFLOWS[name]()
    print("unsupervised smoke checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"unsupervised smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
