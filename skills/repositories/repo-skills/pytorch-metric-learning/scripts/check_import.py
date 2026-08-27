#!/usr/bin/env python3
"""Quick import smoke check for the PyTorch Metric Learning package."""

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError, version


MODULES = [
    "pytorch_metric_learning",
    "pytorch_metric_learning.losses",
    "pytorch_metric_learning.miners",
    "pytorch_metric_learning.reducers",
    "pytorch_metric_learning.regularizers",
    "pytorch_metric_learning.samplers",
    "pytorch_metric_learning.trainers",
    "pytorch_metric_learning.testers",
    "pytorch_metric_learning.datasets",
    "pytorch_metric_learning.utils.accuracy_calculator",
    "pytorch_metric_learning.utils.inference",
]


def main() -> int:
    try:
        import pytorch_metric_learning as pml
        import torch
        import torchvision
        import faiss
    except ModuleNotFoundError as exc:
        print(
            "missing import: {}\nIf you need evaluation or inference, install pytorch-metric-learning[with-hooks-cpu] plus a compatible torch/torchvision pair.".format(
                exc.name
            ),
            file=sys.stderr,
        )
        return 1

    for module_name in MODULES:
        __import__(module_name)

    try:
        dist_version = version("pytorch-metric-learning")
    except PackageNotFoundError:
        dist_version = "not-found"

    print(f"pytorch-metric-learning={pml.__version__}")
    print(f"distribution-version={dist_version}")
    print(f"torch={torch.__version__}")
    print(f"torchvision={torchvision.__version__}")
    print(f"faiss={faiss.__version__}")
    print("imports-ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
