#!/usr/bin/env python3
"""Run a tiny CPU-only numpy-ml probabilistic/sequence smoke.

Prerequisites: numpy-ml with NumPy and SciPy. No corpora downloads required.
"""
import argparse
import json
import os
import tempfile
import warnings

import numpy as np


def run():
    warnings.filterwarnings("ignore")
    from numpy_ml.gmm import GMM
    from numpy_ml.hmm import MultinomialHMM
    from numpy_ml.ngram import AdditiveNGram

    rng = np.random.RandomState(1)
    X = np.vstack([rng.normal(0, 0.1, (5, 2)), rng.normal(2, 0.1, (5, 2))])
    gmm = GMM(C=2, seed=1)
    gmm.fit(X, max_iter=2, verbose=False)
    gmm_pred = gmm.predict(X[:2])

    A = np.array([[0.7, 0.3], [0.2, 0.8]])
    B = np.array([[0.6, 0.4], [0.1, 0.9]])
    pi = np.array([0.5, 0.5])
    hmm = MultinomialHMM(A=A, B=B, pi=pi)
    hmm_ll = hmm.log_likelihood(np.array([0, 1, 1]))

    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write("a tiny corpus\na tiny test corpus\n")
        corpus = f.name
    try:
        lm = AdditiveNGram(2, K=1, filter_stopwords=False, filter_punctuation=True)
        lm.train(corpus)
        lp = lm.log_prob(["a", "tiny"], 2)
    finally:
        os.unlink(corpus)

    return {
        "gmm_pred_shape": list(np.asarray(gmm_pred).shape),
        "hmm_log_likelihood": float(hmm_ll),
        "ngram_log_prob": float(lp),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("numpy-ml probabilistic smoke passed")
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
