#!/usr/bin/env python3
"""Tiny SecretFlow analytics smoke helper.

This script only imports the direct preprocessing/statistics/ML surfaces and
prints the most important constructor or function signatures.
"""

import inspect

from secretflow.preprocessing import StandardScaler
from secretflow.stats import psi_eval
from secretflow.ml.linear import SSGLM, SSRegression
from secretflow.ml.cluster.kmeans import KMeans
from secretflow.ml.naive_bayes.gnb import GNB
from secretflow.ml.gaussian_process.gaussian_process_classifier import GPC
from secretflow.ml.neighbors.knn import KNNClassifer


def main() -> int:
    print(f"StandardScaler: {inspect.signature(StandardScaler)}")
    print(f"psi_eval: {inspect.signature(psi_eval)}")
    print(f"SSGLM: {inspect.signature(SSGLM)}")
    print(f"SSRegression: {inspect.signature(SSRegression)}")
    print(f"KMeans: {inspect.signature(KMeans)}")
    print(f"GNB: {inspect.signature(GNB)}")
    print(f"GPC: {inspect.signature(GPC)}")
    print(f"KNNClassifer: {inspect.signature(KNNClassifer)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
