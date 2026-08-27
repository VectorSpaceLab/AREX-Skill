#!/usr/bin/env python3
"""Quick import and backend sanity check for KerasTuner.

Safe by default: it only imports the installed package, prints verified
versions/signatures, and optionally adds a checkout to sys.path when
`--repo-root` is provided.
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import pathlib
import sys


def _add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    repo = pathlib.Path(repo_root).resolve()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))


def _module_version(name: str) -> str:
    spec = importlib.util.find_spec(name)
    if spec is None:
        return "missing"
    try:
        module = __import__(name)
        return getattr(module, "__version__", "present")
    except Exception as exc:  # pragma: no cover - defensive diagnostic
        return f"error:{exc.__class__.__name__}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        help="Optional local checkout to add to sys.path before importing.",
    )
    args = parser.parse_args()
    _add_repo_root(args.repo_root)

    import keras_tuner
    from keras_tuner.backend import config
    from keras_tuner.applications import (
        HyperEfficientNet,
        HyperImageAugment,
        HyperResNet,
        HyperXception,
    )
    from keras_tuner.tuners import (
        BayesianOptimization,
        GridSearch,
        Hyperband,
        RandomSearch,
        SklearnTuner,
    )

    print(f"keras_tuner={keras_tuner.__version__}")
    print(f"backend={config.backend()}")
    print(f"multi_backend={config.multi_backend()}")
    print(f"tensorflow={_module_version('tensorflow')}")
    print(f"scipy={_module_version('scipy')}")
    print(f"sklearn={_module_version('sklearn')}")
    print(f"pandas={_module_version('pandas')}")
    print(f"portpicker={_module_version('portpicker')}")

    signatures = {
        "RandomSearch": RandomSearch,
        "GridSearch": GridSearch,
        "Hyperband": Hyperband,
        "BayesianOptimization": BayesianOptimization,
        "SklearnTuner": SklearnTuner,
        "HyperResNet": HyperResNet,
        "HyperXception": HyperXception,
        "HyperEfficientNet": HyperEfficientNet,
        "HyperImageAugment": HyperImageAugment,
    }
    for name, obj in signatures.items():
        try:
            sig = inspect.signature(obj)
        except Exception as exc:  # pragma: no cover - defensive diagnostic
            sig = f"<{exc.__class__.__name__}: {exc}>"
        print(f"{name}: {sig}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
