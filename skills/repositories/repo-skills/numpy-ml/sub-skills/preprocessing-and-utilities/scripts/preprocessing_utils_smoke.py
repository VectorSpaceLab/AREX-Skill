#!/usr/bin/env python3
"""Run a tiny CPU-only numpy-ml preprocessing and utilities smoke."""
import argparse
import json
import warnings

import numpy as np


def run():
    warnings.filterwarnings("ignore")
    from numpy_ml.preprocessing.general import Standardizer, OneHotEncoder, FeatureHasher
    from numpy_ml.preprocessing.nlp import tokenize_words
    from numpy_ml.preprocessing.dsp import DFT
    from numpy_ml.utils.kernels import RBFKernel
    from numpy_ml.utils.distance_metrics import euclidean
    from numpy_ml.utils.data_structures import PriorityQueue

    X = np.array([[1.0, 2.0], [3.0, 4.0]])
    scaler = Standardizer()
    scaler.fit(X)
    Z = scaler.transform(X)

    encoder = OneHotEncoder()
    Y = encoder.transform(["red", "blue", "red"])
    labels = encoder.inverse_transform(Y)

    hasher = FeatureHasher(n_dim=8, sparse=True)
    H = hasher.encode([{"red": 1, "round": 1}, {"blue": 1}])

    tokens = tokenize_words("Hello, tiny World!", filter_stopwords=False)
    dft = DFT(np.array([1.0, 0.0, -1.0, 0.0]))
    kernel = RBFKernel(sigma=1)(np.array([[1.0, 2.0]]), np.array([[3.0, 4.0]]))
    distance = euclidean(np.array([1.0, 2.0]), np.array([3.0, 4.0]))

    pq = PriorityQueue(capacity=3)
    pq.push("a", priority=1)
    pq.push("b", priority=2)
    popped = pq.pop()

    return {
        "standardized_mean": Z.mean(axis=0).round(6).tolist(),
        "one_hot_shape": list(Y.shape),
        "inverse_labels": labels,
        "feature_hash_shape": list(H.shape),
        "tokens": tokens,
        "dft_result_len": len(dft),
        "rbf_kernel_shape": list(np.asarray(kernel).shape),
        "euclidean": float(distance),
        "priority_queue_pop_key": popped["key"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("numpy-ml preprocessing/utilities smoke passed")
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
