#!/usr/bin/env python3
"""Validate Flow Forecast training configs without starting a training run.

The script checks the registry names, config block presence, device selection,
loader-specific keys, and a few model-family-specific constraints. It also has a
small built-in smoke mode so the parser and validation path can be exercised
without a user-supplied JSON file.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from flood_forecast.device import resolve_torch_device
from flood_forecast.model_dict_function import pytorch_criterion_dict, pytorch_model_dict, pytorch_opt_dict


ALLOWED_MODEL_TYPES = {"PyTorch", "da_rnn"}
CLASSIFICATION_LOADER_NAMES = {"GeneralClassificationLoader", "VariableSequenceLength"}
FORECAST_LOADER_NAMES = {"default", "AutoEncoder", "TemporalLoader", "SeriesIDLoader"}


@dataclass(frozen=True)
class ValidationReport:
    """Summarize the results of one training-config validation run."""

    ok: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def load_config(path: Path) -> dict[str, Any]:
    """Load a JSON config from disk.

    :param path: Path to the JSON file.
    :type path: pathlib.Path
    :return: Parsed JSON object.
    :rtype: dict[str, Any]
    """
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _listify(value: Any) -> list[Any]:
    """Return ``value`` as a list.

    :param value: A scalar, list, or tuple.
    :type value: Any
    :return: A list representation.
    :rtype: list[Any]
    """
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _build_smoke_config() -> dict[str, Any]:
    """Construct a tiny built-in config used by ``--smoke``.

    :return: A minimal but valid-looking config object.
    :rtype: dict[str, Any]
    """
    return {
        "model_name": "DummyTorchModel",
        "model_type": "PyTorch",
        "model_params": {"forecast_length": 3},
        "dataset_params": {
            "class": "default",
            "training_path": "smoke_train.csv",
            "validation_path": "smoke_valid.csv",
            "test_path": "smoke_test.csv",
            "forecast_history": 6,
            "forecast_length": 3,
            "target_col": ["cfs"],
            "relevant_cols": ["cfs", "temp", "precip"],
            "scaler": "StandardScaler",
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
            "test_csv_path": "smoke_test.csv",
            "decoder_params": {"decoder_function": "simple_decode", "unsqueeze_dim": 1},
            "dataset_params": {
                "file_path": "smoke_test.csv",
                "forecast_history": 6,
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


def validate_config(
    config: dict[str, Any],
    *,
    allow_missing_paths: bool = False,
) -> ValidationReport:
    """Validate a training config dictionary.

    :param config: Parsed training config.
    :type config: dict[str, Any]
    :param allow_missing_paths: Treat missing training/validation/test paths as warnings.
    :type allow_missing_paths: bool
    :return: Validation report.
    :rtype: ValidationReport
    """
    errors: list[str] = []
    warnings: list[str] = []

    model_type = config.get("model_type")
    if model_type not in ALLOWED_MODEL_TYPES:
        errors.append(f"unsupported model_type {model_type!r}; choose from {sorted(ALLOWED_MODEL_TYPES)}")

    if model_type == "PyTorch":
        model_name = config.get("model_name")
        if model_name not in pytorch_model_dict:
            errors.append(f"unsupported model_name {model_name!r}; choose a key from the model registry")

    if "device" in config:
        try:
            resolve_torch_device(config["device"])
        except Exception as exc:  # pragma: no cover - validation path.
            errors.append(f"invalid device {config['device']!r}: {exc}")

    dataset_params = config.get("dataset_params") or {}
    training_params = config.get("training_params") or {}
    model_params = config.get("model_params") or {}
    inference_params = config.get("inference_params") or {}

    if not isinstance(dataset_params, dict):
        errors.append("dataset_params must be an object")
    if not isinstance(training_params, dict):
        errors.append("training_params must be an object")
    if not isinstance(model_params, dict):
        errors.append("model_params must be an object")
    if not isinstance(inference_params, dict):
        errors.append("inference_params must be an object")

    required_dataset_keys = ["forecast_history", "forecast_length", "target_col", "relevant_cols", "class"]
    if model_type == "da_rnn":
        required_dataset_keys = ["training_path", "target_col", "forecast_length"]
    for key in required_dataset_keys:
        if key not in dataset_params:
            errors.append(f"dataset_params is missing required key {key!r}")

    if model_type == "PyTorch":
        required_training_keys = ["criterion", "optimizer", "optim_params", "lr", "epochs", "batch_size"]
        for key in required_training_keys:
            if key not in training_params:
                errors.append(f"training_params is missing required key {key!r}")

    if config.get("wandb") not in (False, None) and not isinstance(config.get("wandb"), dict):
        errors.append("wandb must be False or a mapping")

    if "optimizer" in training_params and training_params["optimizer"] not in pytorch_opt_dict:
        errors.append(f"unsupported optimizer {training_params['optimizer']!r}")

    criterion_value = training_params.get("criterion")
    if criterion_value is not None:
        for name in _listify(criterion_value):
            if isinstance(name, str) and name not in pytorch_criterion_dict:
                errors.append(f"unsupported criterion {name!r}")

    if "epochs" in training_params and int(training_params["epochs"]) < 1:
        errors.append("training_params['epochs'] must be positive")
    if "batch_size" in training_params and int(training_params["batch_size"]) < 1:
        errors.append("training_params['batch_size'] must be positive")

    if dataset_params:
        loader_class = dataset_params.get("class", "default")
        if loader_class not in FORECAST_LOADER_NAMES and loader_class not in CLASSIFICATION_LOADER_NAMES:
            warnings.append(f"dataset loader class {loader_class!r} is not one of the common built-in loaders")
        if loader_class == "TemporalLoader" and "temporal_feats" not in dataset_params:
            errors.append("TemporalLoader requires dataset_params['temporal_feats']")
        if loader_class == "SeriesIDLoader" and "series_id_col" not in dataset_params:
            errors.append("SeriesIDLoader requires dataset_params['series_id_col']")
        if loader_class == "GeneralClassificationLoader" and "sequence_length" not in dataset_params:
            errors.append("GeneralClassificationLoader requires dataset_params['sequence_length']")
        if loader_class == "VariableSequenceLength" and "series_marker_column" not in dataset_params:
            errors.append("VariableSequenceLength requires dataset_params['series_marker_column']")
        if loader_class == "AutoEncoder" and "relevant_cols" not in dataset_params:
            errors.append("AutoEncoder requires dataset_params['relevant_cols']")

    if model_type == "PyTorch" and model_params:
        if "NARX" == config.get("model_name"):
            history = int(dataset_params.get("forecast_history", model_params.get("forecast_history", 0)))
            for key in ("n_target_lags", "n_exog_lags"):
                if key in model_params and int(model_params[key]) > history:
                    errors.append(f"{key} must be <= forecast_history")
            if "output_seq_len" in model_params and "forecast_length" in dataset_params:
                if int(model_params["output_seq_len"]) != int(dataset_params["forecast_length"]):
                    warnings.append("NARX output_seq_len and dataset forecast_length differ; confirm this is intentional")
        if config.get("model_name") in {"Informer", "ITransformer"} and dataset_params.get("class") != "TemporalLoader":
            warnings.append("Temporal models usually expect the TemporalLoader")

    if model_type == "PyTorch" and dataset_params.get("class") not in CLASSIFICATION_LOADER_NAMES:
        if not inference_params:
            errors.append("forecasting models should provide inference_params for post-fit evaluation")
        elif "dataset_params" not in inference_params:
            errors.append("inference_params must include a dataset_params block")

    if not allow_missing_paths and model_type == "PyTorch":
        for key in ("training_path", "validation_path", "test_path"):
            path_value = dataset_params.get(key)
            if path_value and not Path(str(path_value)).exists() and not str(path_value).startswith("gs://"):
                errors.append(f"dataset_params[{key!r}] does not exist: {path_value}")

    if "scaler_params" in dataset_params and isinstance(dataset_params["scaler_params"], dict):
        if isinstance(dataset_params["scaler_params"].get("feature_range"), list):
            warnings.append("scaler_params['feature_range'] is a list; the trainer will convert it to a tuple")

    return ValidationReport(ok=not errors, errors=tuple(errors), warnings=tuple(warnings))


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    :return: Argument parser.
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(description="Validate a Flow Forecast training config.")
    parser.add_argument("--config", type=Path, help="Path to a JSON training config.")
    parser.add_argument("--smoke", action="store_true", help="Use a built-in synthetic config instead of a file.")
    parser.add_argument("--allow-missing-paths", action="store_true", help="Treat missing data paths as warnings.")
    parser.add_argument("--show-models", action="store_true", help="Print the registry keys and exit after validation.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the config validator.

    :param argv: Optional argument vector.
    :type argv: list[str] | None
    :return: Process exit status.
    :rtype: int
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.smoke:
        config = _build_smoke_config()
    elif args.config is not None:
        config = load_config(args.config)
    else:
        parser.error("provide either --config or --smoke")

    report = validate_config(config, allow_missing_paths=args.allow_missing_paths or args.smoke)

    print("Training config validation:", "OK" if report.ok else "FAILED")
    for warning in report.warnings:
        print("WARN:", warning)
    for error in report.errors:
        print("ERROR:", error)
    if args.show_models:
        print("model names:", ", ".join(sorted(pytorch_model_dict)))
        print("criteria:", ", ".join(sorted(pytorch_criterion_dict)))
        print("optimizers:", ", ".join(sorted(pytorch_opt_dict)))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
