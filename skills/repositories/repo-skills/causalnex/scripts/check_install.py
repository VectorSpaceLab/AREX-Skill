#!/usr/bin/env python3
from __future__ import annotations

import sys
import traceback
from importlib.metadata import PackageNotFoundError, version


def probe(label: str, import_path: str, symbol: str | None = None) -> None:
    module = __import__(import_path, fromlist=[symbol] if symbol else [])
    if symbol:
        getattr(module, symbol)
    print(f"{label}: ok")


def main() -> int:
    try:
        import causalnex

        print(f"causalnex: {version('causalnex')}")
        print(f"module: {causalnex.__file__}")

        probe("network", "causalnex.network", "BayesianNetwork")
        probe("inference", "causalnex.inference", "InferenceEngine")
        probe("discretiser", "causalnex.discretiser", "Discretiser")
        probe("structure", "causalnex.structure", "StructureModel")
        probe("evaluation", "causalnex.evaluation", "roc_auc")
        probe("plots", "causalnex.plots", "plot_structure")
        probe("estimator", "causalnex.estimator", "EMSingleLatentVariable")
        probe("pytorch", "causalnex.structure.pytorch", "from_pandas")

        try:
            import torch

            print(f"torch: {torch.__version__}")
            print(f"cuda_available: {torch.cuda.is_available()}")
        except Exception as exc:  # pragma: no cover - optional dependency probe
            print(f"torch: unavailable ({exc.__class__.__name__})")

        try:
            from causalnex.discretiser.discretiser_strategy import MDLPSupervisedDiscretiserMethod

            MDLPSupervisedDiscretiserMethod()
            print("mdlp: ok")
        except Exception as exc:  # pragma: no cover - optional dependency probe
            print(f"mdlp: unavailable ({exc.__class__.__name__})")

        return 0
    except PackageNotFoundError:
        print("causalnex distribution metadata is missing")
        return 1
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
