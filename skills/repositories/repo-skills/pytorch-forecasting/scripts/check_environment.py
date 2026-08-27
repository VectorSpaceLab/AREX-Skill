#!/usr/bin/env python3
"""Check a PyTorch Forecasting runtime environment.

This helper is safe to run from any working directory. It imports the installed
package, reports key dependency versions, probes optional extras, and performs a
small CPU tensor check without training or downloading data.
"""

from __future__ import annotations

import argparse
from importlib import metadata, util
import json
import sys


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def module_available(name: str) -> bool:
    return util.find_spec(name) is not None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check imports, versions, optional extras, and torch backend status for PyTorch Forecasting."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a short text report.",
    )
    parser.add_argument(
        "--require-extra",
        action="append",
        default=[],
        choices=["tuning", "mqf2", "matplotlib"],
        help="Fail when a selected optional feature is not importable. May be repeated.",
    )
    args = parser.parse_args()

    report: dict[str, object] = {
        "python": sys.version.split()[0],
        "distributions": {
            "pytorch-forecasting": dist_version("pytorch-forecasting"),
            "torch": dist_version("torch"),
            "lightning": dist_version("lightning"),
            "pandas": dist_version("pandas"),
            "scikit-learn": dist_version("scikit-learn"),
            "scikit-base": dist_version("scikit-base"),
        },
        "imports": {},
        "optional_features": {},
        "torch_backend": {},
        "errors": [],
        "warnings": [],
    }

    errors: list[str] = report["errors"]  # type: ignore[assignment]
    warnings: list[str] = report["warnings"]  # type: ignore[assignment]

    try:
        import pytorch_forecasting as pf
        from pytorch_forecasting import TimeSeriesDataSet
        from pytorch_forecasting.metrics import QuantileLoss, SMAPE

        report["imports"] = {
            "pytorch_forecasting": True,
            "version": getattr(pf, "__version__", None),
            "TimeSeriesDataSet": TimeSeriesDataSet.__name__,
            "QuantileLoss_default_quantiles": QuantileLoss().quantiles,
            "SMAPE": SMAPE.__name__,
        }
    except Exception as exc:  # pragma: no cover - depends on caller env
        errors.append(f"pytorch_forecasting import failed: {type(exc).__name__}: {exc}")
        report["imports"] = {"pytorch_forecasting": False}

    try:
        import torch

        cpu_value = float(torch.zeros(2).sum().item())
        cuda_available = bool(torch.cuda.is_available())
        report["torch_backend"] = {
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "cuda_available": cuda_available,
            "cuda_device_count": int(torch.cuda.device_count()),
            "cpu_tensor_sum": cpu_value,
        }
        if cuda_available:
            report["torch_backend"]["cuda_device_name_0"] = torch.cuda.get_device_name(0)
    except Exception as exc:  # pragma: no cover - depends on caller env
        errors.append(f"torch backend check failed: {type(exc).__name__}: {exc}")

    optional = {
        "tuning": {"modules": ["optuna", "optuna_integration"], "extra": "pytorch-forecasting[tuning]"},
        "mqf2": {"modules": ["cpflows"], "extra": "pytorch-forecasting[mqf2]"},
        "matplotlib": {"modules": ["matplotlib"], "extra": "matplotlib or plotting/docs extras"},
    }
    optional_status: dict[str, object] = {}
    for name, spec in optional.items():
        modules = spec["modules"]  # type: ignore[index]
        available = {module: module_available(module) for module in modules}
        ok = all(available.values())
        optional_status[name] = {"available": ok, "modules": available, "install_hint": spec["extra"]}
        if name in args.require_extra and not ok:
            errors.append(f"required optional feature {name!r} is missing; install {spec['extra']}")
        elif not ok:
            warnings.append(f"optional feature {name!r} is not fully available")
    report["optional_features"] = optional_status

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("PyTorch Forecasting environment check")
        print("Python:", report["python"])
        for name, version in report["distributions"].items():  # type: ignore[union-attr]
            print(f"- {name}: {version or 'not installed'}")
        print("Imports:", report["imports"])
        print("Torch backend:", report["torch_backend"])
        print("Optional features:")
        for name, status in optional_status.items():
            print(f"- {name}: {status}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
