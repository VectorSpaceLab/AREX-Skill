#!/usr/bin/env python3
"""Quick pomegranate installation and backend smoke check.

Run with the Python environment that should use pomegranate:

    python check_env.py
    python check_env.py --cuda
"""

from __future__ import annotations

import argparse
from importlib.metadata import version


def main() -> int:
    parser = argparse.ArgumentParser(description="Check pomegranate imports and optional CUDA availability.")
    parser.add_argument("--cuda", action="store_true", help="Require CUDA and allocate a tiny CUDA tensor.")
    args = parser.parse_args()

    import torch
    import pomegranate
    from pomegranate.distributions import Normal, Categorical
    from pomegranate.gmm import GeneralMixtureModel
    from pomegranate.bayes_classifier import BayesClassifier
    from pomegranate.bayesian_network import BayesianNetwork
    from pomegranate.factor_graph import FactorGraph
    from pomegranate.hmm import DenseHMM, SparseHMM
    from pomegranate.kmeans import KMeans
    from pomegranate.markov_chain import MarkovChain

    imported = [
        Normal,
        Categorical,
        GeneralMixtureModel,
        BayesClassifier,
        BayesianNetwork,
        FactorGraph,
        DenseHMM,
        SparseHMM,
        KMeans,
        MarkovChain,
    ]
    print(f"pomegranate metadata version: {version('pomegranate')}")
    print(f"pomegranate module version: {getattr(pomegranate, '__version__', 'unknown')}")
    print(f"torch version: {torch.__version__}; torch cuda tag: {torch.version.cuda}")
    print("imported classes:", ", ".join(cls.__name__ for cls in imported))

    if args.cuda:
        if not torch.cuda.is_available():
            raise SystemExit("CUDA was requested but torch.cuda.is_available() is false")
        x = torch.empty((1,), device="cuda")
        print(f"CUDA smoke: {torch.cuda.get_device_name(0)} {torch.cuda.get_device_capability(0)} {x.device}")
    else:
        print(f"CUDA available: {torch.cuda.is_available()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
