#!/usr/bin/env python3
"""Run a tiny CPU-only numpy-ml tabular/model-factorization smoke.

Prerequisites: numpy-ml with NumPy and SciPy. No comparison libraries or data
files are needed. Run from any directory with:
  python tabular_smoke.py
"""
import argparse
import json
import warnings

import numpy as np


def run():
    warnings.filterwarnings("ignore")
    from numpy_ml.linear_models import LinearRegression
    from numpy_ml.trees import DecisionTree
    from numpy_ml.nonparametric import KNN, GPRegression
    from numpy_ml.factorization import NMF

    X = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 2.0]])
    y_reg = np.array([[0.0], [1.0], [1.0], [2.0], [4.0]])
    y_cls = np.array([0, 0, 1, 1, 1])

    linear = LinearRegression()
    linear.fit(X, y_reg)
    linear_pred = linear.predict(X[:2])

    tree = DecisionTree(classifier=True, max_depth=2, seed=7)
    tree.fit(X, y_cls)
    tree_pred = tree.predict(X[:2])

    knn = KNN(k=2, classifier=False)
    knn.fit(X, y_reg.ravel())
    knn_pred = knn.predict(X[:2])

    gp = GPRegression(alpha=1e-5)
    gp.fit(X, y_reg)
    gp_mean, _ = gp.predict(X[:2])

    nmf = NMF(K=2, max_iter=3, tol=1e-4)
    nmf.fit(np.abs(np.random.RandomState(0).rand(4, 3)), n_initializations=1)

    return {
        "linear_prediction_shape": list(np.asarray(linear_pred).shape),
        "tree_prediction_shape": list(np.asarray(tree_pred).shape),
        "knn_prediction_shape": list(np.asarray(knn_pred).shape),
        "gp_mean_shape": list(np.asarray(gp_mean).shape),
        "nmf_W_shape": list(nmf.W.shape),
        "nmf_H_shape": list(nmf.H.shape),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("numpy-ml tabular smoke passed")
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
