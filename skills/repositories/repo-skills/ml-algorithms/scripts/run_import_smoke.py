#!/usr/bin/env python
"""Safe MLAlgorithms package import and signature smoke check.

Run this from any directory in the Python environment where `mla` is installed.
It imports representative modules, reports dependency versions, inspects key
constructor signatures, and emits compatibility warnings. It does not run native
examples, train models, download data, open plots, or render Gym environments.

Examples:
  python run_import_smoke.py
  python run_import_smoke.py --json
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from importlib import metadata


def dist_version(name: str):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_status(name: str):
    try:
        mod = importlib.import_module(name)
        return {"name": name, "ok": True, "file": getattr(mod, "__file__", None)}
    except Exception as exc:  # keep diagnostic concise for agents
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def signature_status(import_path: str):
    module_name, _, attr = import_path.rpartition(".")
    try:
        module = importlib.import_module(module_name)
        obj = getattr(module, attr)
        return {"object": import_path, "ok": True, "signature": str(inspect.signature(obj))}
    except Exception as exc:
        return {"object": import_path, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def build_report():
    distributions = {
        name: dist_version(name)
        for name in [
            "mla",
            "numpy",
            "scipy",
            "scikit-learn",
            "autograd",
            "matplotlib",
            "seaborn",
            "gym",
            "tqdm",
        ]
    }
    imports = [
        import_status(name)
        for name in [
            "mla",
            "mla.linear_models",
            "mla.knn",
            "mla.naive_bayes",
            "mla.svm.svm",
            "mla.svm.kernerls",
            "mla.ensemble.random_forest",
            "mla.ensemble.gbm",
            "mla.kmeans",
            "mla.gaussian_mixture",
            "mla.pca",
            "mla.tsne",
            "mla.rbm",
            "mla.datasets",
            "mla.neuralnet",
            "mla.neuralnet.layers",
            "mla.neuralnet.optimizers",
            "mla.rl.dqn",
        ]
    ]
    signatures = [
        signature_status(path)
        for path in [
            "mla.linear_models.LinearRegression",
            "mla.linear_models.LogisticRegression",
            "mla.knn.KNNClassifier",
            "mla.naive_bayes.NaiveBayesClassifier",
            "mla.svm.svm.SVM",
            "mla.svm.kernerls.RBF",
            "mla.ensemble.random_forest.RandomForestClassifier",
            "mla.ensemble.gbm.GradientBoostingClassifier",
            "mla.kmeans.KMeans",
            "mla.gaussian_mixture.GaussianMixture",
            "mla.pca.PCA",
            "mla.tsne.TSNE",
            "mla.rbm.RBM",
            "mla.neuralnet.nnet.NeuralNet",
            "mla.neuralnet.layers.basic.Dense",
            "mla.neuralnet.optimizers.Adam",
            "mla.rl.dqn.DQN",
        ]
    ]

    warnings = []
    numpy_version = distributions.get("numpy")
    if numpy_version:
        major_minor = tuple(int(part) for part in numpy_version.split(".")[:2] if part.isdigit())
        if major_minor >= (1, 24):
            warnings.append("NumPy >=1.24 detected: mla.datasets.load_nietzsche() may fail because this package version uses deprecated np.bool.")
    gym_version = distributions.get("gym")
    if gym_version is None:
        warnings.append("gym is not installed: mla.rl.dqn imports or DQN environment setup may fail.")
    else:
        warnings.append("DQN expects legacy Gym reset/step signatures; adapt before using Gymnasium or newer Gym APIs.")

    status = "ok" if all(item["ok"] for item in imports) and all(item["ok"] for item in signatures) else "failed"
    return {
        "status": status,
        "python": sys.version.split()[0],
        "distributions": distributions,
        "imports": imports,
        "signatures": signatures,
        "warnings": warnings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check MLAlgorithms (`mla`) importability and key API signatures.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a human-readable summary.")
    args = parser.parse_args(argv)
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        print(f"python: {report['python']}")
        for name, version in report["distributions"].items():
            print(f"dist {name}: {version or 'missing'}")
        for item in report["imports"]:
            print(f"import {item['name']}: {'ok' if item['ok'] else item['error']}")
        for item in report["signatures"]:
            print(f"signature {item['object']}: {item.get('signature', item.get('error'))}")
        for warning in report["warnings"]:
            print(f"warning: {warning}")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
