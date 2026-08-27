#!/usr/bin/env python3
"""Validate and smoke-test a Flow Forecast inference configuration.

With ``--smoke`` the script builds a synthetic CSV and a DummyTorchModel config,
then exercises ``InferenceMode.infer_now`` and optional TorchScript export. With
``--config`` it validates a user config and can run the same path against a local
CSV and optional checkpoint.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from flood_forecast.deployment.inference import InferenceMode, convert_to_torch_script
from flood_forecast.model_dict_function import pytorch_model_dict


@dataclass(frozen=True)
class ValidationReport:
    """Summarize inference-config validation."""

    ok: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def _load_json(path: Path) -> dict[str, Any]:
    """Load JSON from disk.

    :param path: JSON path.
    :type path: pathlib.Path
    :return: Parsed config.
    :rtype: dict[str, Any]
    """
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_fixture_csv(path: Path, rows: int = 80) -> Path:
    """Create a tiny synthetic inference CSV.

    :param path: Destination directory.
    :type path: pathlib.Path
    :param rows: Number of hourly rows.
    :type rows: int
    :return: Created CSV path.
    :rtype: pathlib.Path
    """
    start = datetime(2020, 1, 1)
    frame = pd.DataFrame(
        {
            "datetime": [start + timedelta(hours=index) for index in range(rows)],
            "cfs": [10.0 + index for index in range(rows)],
            "temp": [20.0 + 0.1 * index for index in range(rows)],
            "precip": [0.05 * (index % 4) for index in range(rows)],
        }
    )
    csv_path = path / "inference_smoke.csv"
    frame.to_csv(csv_path, index=False)
    return csv_path


def _build_smoke_config(csv_path: Path, device: str) -> dict[str, Any]:
    """Build the synthetic inference config.

    :param csv_path: CSV fixture path.
    :type csv_path: pathlib.Path
    :param device: Torch device string for the smoke model.
    :type device: str
    :return: Config dictionary.
    :rtype: dict[str, Any]
    """
    return {
        "model_name": "DummyTorchModel",
        "model_type": "PyTorch",
        "device": device,
        "model_params": {"forecast_length": 3},
        "dataset_params": {
            "class": "default",
            "training_path": str(csv_path),
            "validation_path": str(csv_path),
            "test_path": str(csv_path),
            "forecast_history": 8,
            "forecast_length": 3,
            "target_col": ["cfs"],
            "relevant_cols": ["cfs", "temp", "precip"],
            "scaler": "StandardScaler",
            "sort_column": "datetime",
        },
        "training_params": {
            "criterion": "MSE",
            "optimizer": "Adam",
            "optim_params": {},
            "lr": 0.001,
            "epochs": 1,
            "batch_size": 2,
        },
        "inference_params": {
            "datetime_start": "2020-01-02",
            "hours_to_forecast": 3,
            "num_prediction_samples": 2,
            "test_csv_path": str(csv_path),
            "decoder_params": {"decoder_function": "simple_decode", "unsqueeze_dim": 1},
            "dataset_params": {
                "file_path": str(csv_path),
                "sort_column": "datetime",
                "forecast_history": 8,
                "forecast_length": 3,
                "relevant_cols": ["cfs", "temp", "precip"],
                "target_col": ["cfs"],
                "scaling": "StandardScaler",
                "interpolate_param": False,
            },
        },
        "metrics": ["MSE"],
        "wandb": False,
        "GCS": False,
    }


def _csv_path_from_config(config: dict[str, Any]) -> str | None:
    """Find the most likely inference CSV path in a config.

    :param config: Inference config.
    :type config: dict[str, Any]
    :return: CSV path string or ``None``.
    :rtype: str | None
    """
    inference_params = config.get("inference_params", {})
    dataset_params = inference_params.get("dataset_params", {}) if isinstance(inference_params, dict) else {}
    return inference_params.get("test_csv_path") or dataset_params.get("file_path") or config.get("csv_path")


def validate_config(config: dict[str, Any], csv_path: str | None, weight_path: str | None) -> ValidationReport:
    """Validate inference config structure and paths.

    :param config: Parsed config.
    :type config: dict[str, Any]
    :param csv_path: Resolved CSV path.
    :type csv_path: str | None
    :param weight_path: Optional checkpoint path.
    :type weight_path: str | None
    :return: Validation report.
    :rtype: ValidationReport
    """
    errors: list[str] = []
    warnings: list[str] = []

    model_name = config.get("model_name")
    if model_name not in pytorch_model_dict:
        errors.append(f"unsupported model_name {model_name!r}")

    for key in ("model_params", "dataset_params", "inference_params"):
        if not isinstance(config.get(key), dict):
            errors.append(f"{key} must be an object")

    dataset_params = config.get("dataset_params", {})
    inference_params = config.get("inference_params", {})
    inference_dataset = inference_params.get("dataset_params", {}) if isinstance(inference_params, dict) else {}
    for key in ("forecast_history", "forecast_length", "target_col", "relevant_cols", "class"):
        if key not in dataset_params:
            warnings.append(f"dataset_params is missing {key!r}; load_model may fail")
    for key in ("forecast_history", "forecast_length", "target_col", "relevant_cols", "interpolate_param"):
        if key not in inference_dataset:
            errors.append(f"inference_params.dataset_params is missing {key!r}")

    if csv_path is None:
        errors.append("no inference CSV path found; provide --csv or inference_params.test_csv_path")
    elif not str(csv_path).startswith("gs://") and not Path(csv_path).exists():
        errors.append(f"inference CSV does not exist: {csv_path}")

    if weight_path and not str(weight_path).startswith("gs://") and not Path(weight_path).exists():
        warnings.append(f"checkpoint path does not exist locally: {weight_path}")

    samples = inference_params.get("num_prediction_samples")
    if samples is not None and int(samples) < 1:
        errors.append("num_prediction_samples must be positive when supplied")

    if "scaler" in inference_dataset:
        warnings.append("use 'scaling' rather than 'scaler' in inference_params.dataset_params")

    return ValidationReport(ok=not errors, errors=tuple(errors), warnings=tuple(warnings))


def _parse_datetime(value: str | None) -> datetime:
    """Parse a CLI/config datetime into a Python datetime.

    :param value: String timestamp or ``None``.
    :type value: str | None
    :return: Parsed datetime.
    :rtype: datetime
    """
    if value is None:
        return datetime(2020, 1, 2)
    return pd.to_datetime(value).to_pydatetime()


def _ensure_torchscript_dims(mode: InferenceMode) -> None:
    """Populate tracing dimensions when the selected model config omitted them.

    :param mode: InferenceMode instance.
    :type mode: flood_forecast.deployment.inference.InferenceMode
    :return: None
    :rtype: None
    """
    model_params = mode.model.params.setdefault("model_params", {})
    if "n_time_series" not in model_params:
        relevant = mode.model.params.get("dataset_params", {}).get("relevant_cols", [])
        if relevant:
            model_params["n_time_series"] = len(relevant)


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI parser.

    :return: Argument parser.
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(description="Validate and smoke-test Flow Forecast inference.")
    parser.add_argument("--config", type=Path, help="Optional saved config JSON.")
    parser.add_argument("--csv", type=Path, help="Optional inference CSV override.")
    parser.add_argument("--weights", type=str, default="", help="Optional checkpoint path override.")
    parser.add_argument("--date", help="Forecast start date override.")
    parser.add_argument("--smoke", action="store_true", help="Use a synthetic DummyTorchModel config.")
    parser.add_argument("--torchscript", action="store_true", help="Also run a TorchScript trace/export check.")
    parser.add_argument("--device", default="cpu", help="Torch device for --smoke. Defaults to cpu.")
    parser.add_argument("--validate-only", action="store_true", help="Validate without instantiating the model.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run validation and optional smoke inference.

    :param argv: Optional argument vector.
    :type argv: list[str] | None
    :return: Process exit status.
    :rtype: int
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        smoke_mode = args.smoke or args.config is None
        if smoke_mode:
            csv_path = _build_fixture_csv(temp_path)
            config = _build_smoke_config(csv_path, args.device)
        else:
            config = _load_json(args.config)
            csv_path = args.csv or _csv_path_from_config(config)
        csv_path_str = str(csv_path) if csv_path is not None else None
        if args.csv is not None:
            csv_path_str = str(args.csv)
            config.setdefault("inference_params", {})["test_csv_path"] = csv_path_str
            config["inference_params"].setdefault("dataset_params", {})["file_path"] = csv_path_str

        weight_path = args.weights or config.get("weight_path", "")
        report = validate_config(config, csv_path_str, weight_path)
        print("Inference config validation:", "OK" if report.ok else "FAILED")
        for warning in report.warnings:
            print("WARN:", warning)
        for error in report.errors:
            print("ERROR:", error)
        if not report.ok or args.validate_only:
            return 0 if report.ok else 1

        inference_params = config["inference_params"]
        mode = InferenceMode(
            forecast_steps=int(inference_params.get("hours_to_forecast", config["dataset_params"]["forecast_length"])),
            num_prediction_samples=int(inference_params.get("num_prediction_samples", 1)),
            model_params=config,
            csv_path=csv_path_str,
            weight_path=weight_path,
        )
        start = _parse_datetime(args.date or inference_params.get("datetime_start"))
        df, tensor, history, forecast_start, _loader, samples = mode.infer_now(start, csv_path=csv_path_str)
        print("Inference rows:", len(df))
        print("Tensor shape:", tuple(tensor.shape) if hasattr(tensor, "shape") else type(tensor))
        print("History shape:", tuple(history.shape) if hasattr(history, "shape") else type(history))
        print("Forecast start index:", forecast_start)
        print("Prediction samples:", len(samples))

        if args.torchscript:
            _ensure_torchscript_dims(mode)
            script_path = temp_path / "flow_forecast_smoke.pt"
            convert_to_torch_script(mode.model, str(script_path))
            print("TorchScript saved:", script_path.name, script_path.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
