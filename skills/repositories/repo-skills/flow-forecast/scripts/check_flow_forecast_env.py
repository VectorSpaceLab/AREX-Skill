#!/usr/bin/env python3
"""Check the Flow Forecast runtime environment and run a tiny local smoke test.

This script is safe to run from any working directory. It prefers the installed
`flood_forecast` distribution, but accepts `--repo-root` as a fallback for a
local checkout. By default it only prints import/device/registry facts. Use
`--smoke` to build a tiny synthetic CSV in a temporary directory, instantiate
`PyTorchForecast('DummyTorchModel', ...)`, and run a forward pass.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import torch


@dataclass(frozen=True)
class ModuleProbe:
    """Summarize a module import probe."""

    module: str
    available: bool
    detail: str


def _add_repo_root(repo_root: str | None) -> None:
    """Add an explicit repository root to ``sys.path`` if supplied.

    :param repo_root: Optional repository root path.
    :type repo_root: str | None
    :return: None
    :rtype: None
    """
    if repo_root:
        resolved = Path(repo_root).expanduser().resolve()
        if str(resolved) not in sys.path:
            sys.path.insert(0, str(resolved))


def _probe(module_name: str) -> ModuleProbe:
    """Attempt to import one module and record the outcome.

    :param module_name: Dotted module name to import.
    :type module_name: str
    :return: Import result summary.
    :rtype: ModuleProbe
    """
    try:
        module = import_module(module_name)
        return ModuleProbe(module_name, True, getattr(module, "__file__", "imported"))
    except Exception as exc:  # pragma: no cover - diagnostic path.
        return ModuleProbe(module_name, False, f"{type(exc).__name__}: {exc}")


def _build_tiny_csv(tmpdir: Path) -> Path:
    """Write a tiny synthetic CSV that matches the default loader contract.

    :param tmpdir: Temporary directory used for the generated CSV.
    :type tmpdir: pathlib.Path
    :return: Path to the generated CSV file.
    :rtype: pathlib.Path
    """
    rows = []
    start = datetime(2020, 1, 1)
    for idx in range(40):
        stamp = start + timedelta(hours=idx)
        rows.append(
            {
                "datetime": stamp.isoformat(sep=" "),
                "cfs": float(idx + 1),
                "temp": 20.0 + 0.1 * idx,
                "precip": 0.01 * idx,
            }
        )
    path = tmpdir / "flow_forecast_smoke.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _distribution_version(name: str) -> str:
    """Return an installed distribution version or a readable fallback.

    :param name: Distribution name to inspect.
    :type name: str
    :return: The installed version string, or a fallback note.
    :rtype: str
    """
    try:
        return version(name)
    except PackageNotFoundError:
        try:
            module = import_module(name.replace("-", "_"))
        except Exception:
            if name == "flood_forecast":
                try:
                    module = import_module("flood_forecast")
                except Exception:
                    return "not installed"
            else:
                return "not installed"
        return getattr(module, "__version__", "imported-without-package-metadata")


def _summarize_versions(packages: Iterable[str]) -> list[str]:
    """Collect installed distribution versions.

    :param packages: Distribution names to inspect.
    :type packages: Iterable[str]
    :return: Human-readable version lines.
    :rtype: list[str]
    """
    lines: list[str] = []
    for name in packages:
        lines.append(f"{name}=={_distribution_version(name)}")
    return lines


def _run_smoke(device: str) -> None:
    """Run a tiny local model smoke test.

    :param device: Requested device string for the wrapper.
    :type device: str
    :return: None
    :rtype: None
    """
    from flood_forecast.time_model import PyTorchForecast

    with tempfile.TemporaryDirectory() as tmp:
        csv_path = _build_tiny_csv(Path(tmp))
        params: dict[str, Any] = {
            "device": device,
            "metrics": ["MSE"],
            "model_params": {"forecast_length": 3},
            "dataset_params": {
                "forecast_history": 5,
                "forecast_length": 3,
                "class": "default",
                "relevant_cols": ["cfs", "temp", "precip"],
                "target_col": ["cfs"],
                "interpolate": False,
            },
            "training_params": {
                "criterion": "MSE",
                "optimizer": "Adam",
                "optim_params": {},
                "lr": 0.001,
                "epochs": 1,
                "batch_size": 2,
            },
            "wandb": False,
            "GCS": False,
            "inference_params": {"hours_to_forecast": 3},
        }
        forecast = PyTorchForecast("DummyTorchModel", str(csv_path), str(csv_path), str(csv_path), params)
        source, target = forecast.training[0]
        prediction = forecast.model(source.unsqueeze(0).to(forecast.device))
        print("SMOKE model:", forecast.model.__class__.__name__)
        print("SMOKE device:", forecast.device)
        print("SMOKE source shape:", tuple(source.shape))
        print("SMOKE target shape:", tuple(target.shape))
        print("SMOKE prediction shape:", tuple(prediction.shape))


def main(argv: list[str] | None = None) -> int:
    """Run the environment diagnostic.

    :param argv: Optional command-line argument list.
    :type argv: list[str] | None
    :return: Process exit status.
    :rtype: int
    """
    parser = argparse.ArgumentParser(description="Check the Flow Forecast runtime environment.")
    parser.add_argument("--repo-root", help="Optional checkout path to add to sys.path for inspection.")
    parser.add_argument("--device", default="cpu", help="Device to use for the tiny smoke test. Defaults to cpu.")
    parser.add_argument("--smoke", action="store_true", help="Run a tiny synthetic PyTorchForecast smoke test.")
    parser.add_argument("--show-models", action="store_true", help="Print model registry keys and related maps.")
    args = parser.parse_args(argv)

    _add_repo_root(args.repo_root)

    print("Flow Forecast environment check")
    print("Python:", sys.version.replace("\n", " "))
    print("Executable:", sys.executable)
    print("flood_forecast:", _distribution_version("flood_forecast"))
    print("Installed versions:")
    for line in _summarize_versions([
        "torch",
        "numpy",
        "pandas",
        "scikit-learn",
        "plotly",
        "wandb",
        "shap",
        "torchdiffeq",
        "pytorch-tsmixer",
        "google-cloud-storage",
        "tensorboard",
        "einops",
        "jaxtyping",
        "numba",
    ]):
        print(" -", line)

    print("Backends:")
    print(" - torch.cuda.is_available():", torch.cuda.is_available())
    print(" - torch.cuda.device_count():", torch.cuda.device_count())
    mps_backend = getattr(torch.backends, "mps", None)
    mps_available = bool(getattr(mps_backend, "is_available", lambda: False)())
    print(" - torch.backends.mps.is_available():", mps_available)

    probe_targets = [
        "flood_forecast.device",
        "flood_forecast.time_model",
        "flood_forecast.model_dict_function",
        "flood_forecast.preprocessing.pytorch_loaders",
        "flood_forecast.evaluator",
        "flood_forecast.deployment.inference",
        "flood_forecast.da_rnn.train_da",
        "flood_forecast.multi_models.catchment_embedding",
        "flood_forecast.multi_models.contrastive_pretrain",
        "flood_forecast.ode.physics.hydrology",
    ]
    print("Module probes:")
    probes = [_probe(name) for name in probe_targets]
    for probe in probes:
        status = "OK" if probe.available else "ERR"
        print(f" - {status} {probe.module}: {probe.detail}")

    if args.show_models:
        from flood_forecast.model_dict_function import (
            decoding_functions,
            pytorch_criterion_dict,
            pytorch_model_dict,
            pytorch_opt_dict,
        )
        from flood_forecast.pre_dict import interpolate_dict, scaler_dict

        print("Model registry keys:")
        print(" - models:", ", ".join(sorted(pytorch_model_dict.keys())))
        print(" - criteria:", ", ".join(sorted(pytorch_criterion_dict.keys())))
        print(" - optimizers:", ", ".join(sorted(pytorch_opt_dict.keys())))
        print(" - decoders:", ", ".join(sorted(decoding_functions.keys())))
        print(" - scalers:", ", ".join(sorted(scaler_dict.keys())))
        print(" - interpolation helpers:", ", ".join(sorted(interpolate_dict.keys())))

    if args.smoke:
        _run_smoke(args.device)

    return 0 if all(probe.available for probe in probes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
