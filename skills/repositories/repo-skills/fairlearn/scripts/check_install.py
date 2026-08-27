#!/usr/bin/env python3
"""Safe Fairlearn import and optional-backend smoke check.

Run from the generated Fairlearn skill directory:

    python scripts/check_install.py --include-optional
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from collections.abc import Iterable


REQUIRED_IMPORTS = [
    ("fairlearn", "Fairlearn package"),
    ("fairlearn.metrics", "assessment metrics"),
    ("fairlearn.preprocessing", "preprocessing mitigation"),
    ("fairlearn.postprocessing", "postprocessing mitigation"),
    ("fairlearn.reductions", "reductions mitigation"),
    ("fairlearn.adversarial", "adversarial mitigation namespace"),
    ("fairlearn.datasets", "dataset loaders"),
]

OPTIONAL_IMPORTS = [
    ("matplotlib", "plotting helpers"),
    ("torch", "PyTorch adversarial backend"),
    ("tensorflow", "TensorFlow adversarial backend"),
]


def _import_required(module_name: str, label: str) -> None:
    try:
        importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        missing = exc.name or module_name
        raise SystemExit(
            f"Missing required import {missing!r} while checking {label}. "
            "Install Fairlearn in the active environment, for example: "
            "python -m pip install fairlearn"
        ) from exc
    print(f"OK required import: {label} ({module_name})")


def _probe_optional(module_name: str, label: str, *, import_optional: bool) -> None:
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        print(f"MISSING optional import: {label} ({module_name})")
        return
    if not import_optional:
        print(f"FOUND optional import: {label} ({module_name})")
        return
    module = importlib.import_module(module_name)
    version = getattr(module, "__version__", "unknown")
    print(f"OK optional import: {label} ({module_name} {version})")
    if module_name == "torch":
        cuda_available = bool(getattr(module, "cuda", None) and module.cuda.is_available())
        print(f"  torch.cuda.is_available(): {cuda_available}")


def _check_public_symbols() -> None:
    from fairlearn.adversarial import AdversarialFairnessClassifier, AdversarialFairnessRegressor
    from fairlearn.datasets import fetch_acs_income, fetch_adult, fetch_boston
    from fairlearn.metrics import MetricFrame, demographic_parity_difference, selection_rate
    from fairlearn.postprocessing import ThresholdOptimizer
    from fairlearn.preprocessing import CorrelationRemover, PrototypeRepresentationLearner
    from fairlearn.reductions import DemographicParity, ExponentiatedGradient, GridSearch

    symbols: Iterable[object] = [
        MetricFrame,
        selection_rate,
        demographic_parity_difference,
        CorrelationRemover,
        PrototypeRepresentationLearner,
        ThresholdOptimizer,
        DemographicParity,
        ExponentiatedGradient,
        GridSearch,
        AdversarialFairnessClassifier,
        AdversarialFairnessRegressor,
        fetch_adult,
        fetch_acs_income,
        fetch_boston,
    ]
    print("OK public symbols:", ", ".join(getattr(sym, "__name__", str(sym)) for sym in symbols))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="Import optional plotting/adversarial backends when present; missing optional modules do not fail.",
    )
    parser.add_argument(
        "--show-versions",
        action="store_true",
        help="Call fairlearn.show_versions() after import checks.",
    )
    args = parser.parse_args()

    for module_name, label in REQUIRED_IMPORTS:
        _import_required(module_name, label)

    import fairlearn

    print(f"Fairlearn version: {getattr(fairlearn, '__version__', 'unknown')}")
    _check_public_symbols()

    if args.include_optional:
        for module_name, label in OPTIONAL_IMPORTS:
            _probe_optional(module_name, label, import_optional=True)
    else:
        print("Optional imports skipped; rerun with --include-optional to probe them.")

    if args.show_versions:
        print("\n--- fairlearn.show_versions() ---")
        fairlearn.show_versions()

    print("Fairlearn install check completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
