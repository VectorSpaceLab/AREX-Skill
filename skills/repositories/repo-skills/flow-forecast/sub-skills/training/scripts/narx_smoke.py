#!/usr/bin/env python3
"""Run a tiny NARX smoke test on a synthetic CSV fixture.

The smoke checks the Flow Forecast config contract, model instantiation, forward
pass, and closed-loop inference path on a small local dataset. Pass ``--fit`` to
run a one-epoch miniature training loop through ``train_transformer_style`` while
avoiding the full trainer's optional post-fit SHAP path.
"""

from __future__ import annotations

import argparse
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator

import pandas as pd
import torch

from flood_forecast.evaluator import infer_on_torch_model
from flood_forecast.pytorch_training import train_transformer_style
from flood_forecast.time_model import PyTorchForecast, scaling_function


@contextmanager
def _temp_cwd(path: Path) -> Iterator[None]:
    """Temporarily change the current working directory.

    :param path: Directory to enter.
    :type path: pathlib.Path
    :return: Context manager with no yielded value.
    :rtype: typing.Iterator[None]
    """
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _build_fixture_csv(path: Path, rows: int = 160) -> Path:
    """Write a synthetic river forecast CSV.

    :param path: Destination directory.
    :type path: pathlib.Path
    :param rows: Number of hourly rows to generate.
    :type rows: int
    :return: The created CSV path.
    :rtype: pathlib.Path
    """
    start = datetime(2020, 1, 1)
    data = []
    for index in range(rows):
        stamp = start + timedelta(hours=index)
        data.append(
            {
                "datetime": stamp.isoformat(sep=" "),
                "cfs": 100.0 + 0.5 * index,
                "precip": 0.05 * (index % 7),
                "temp": 10.0 + 0.2 * index,
                "dwpf": 5.0 + 0.1 * index,
            }
        )
    csv_path = path / "narx_smoke.csv"
    pd.DataFrame(data).to_csv(csv_path, index=False)
    return csv_path


def _build_config(csv_path: Path, device: str) -> dict:
    """Construct a tiny NARX config.

    :param csv_path: Fixture CSV path.
    :type csv_path: pathlib.Path
    :param device: Requested torch device string.
    :type device: str
    :return: A training/inference config.
    :rtype: dict
    """
    forecast_history = 24
    forecast_length = 12
    return {
        "model_name": "NARX",
        "model_type": "PyTorch",
        "device": device,
        "model_params": {
            "n_time_series": 4,
            "forecast_history": forecast_history,
            "output_seq_len": forecast_length,
            "n_targets": 1,
            "n_target_lags": forecast_history,
            "n_exog_lags": forecast_history,
            "hidden_size": 32,
            "num_hidden_layers": 1,
            "dropout": 0.0,
            "activation": "tanh",
        },
        "dataset_params": {
            "class": "default",
            "training_path": str(csv_path),
            "validation_path": str(csv_path),
            "test_path": str(csv_path),
            "batch_size": 8,
            "forecast_history": forecast_history,
            "forecast_length": forecast_length,
            "train_start": 0,
            "train_end": 70,
            "valid_start": 70,
            "valid_end": 115,
            "test_start": 115,
            "test_end": 160,
            "sort_column": "datetime",
            "target_col": ["cfs"],
            "relevant_cols": ["cfs", "precip", "temp", "dwpf"],
            "scaler": "StandardScaler",
            "interpolate": False,
        },
        "training_params": {
            "criterion": "MSE",
            "optimizer": "Adam",
            "optim_params": {},
            "lr": 0.001,
            "epochs": 1,
            "batch_size": 8,
        },
        "GCS": False,
        "wandb": False,
        "forward_params": {},
        "metrics": ["MSE"],
        "inference_params": {
            "datetime_start": "2020-01-04",
            "hours_to_forecast": 12,
            "test_csv_path": str(csv_path),
            "decoder_params": {
                "decoder_function": "simple_decode",
                "unsqueeze_dim": 1,
            },
            "dataset_params": {
                "file_path": str(csv_path),
                "sort_column": "datetime",
                "forecast_history": forecast_history,
                "forecast_length": forecast_length,
                "relevant_cols": ["cfs", "precip", "temp", "dwpf"],
                "target_col": ["cfs"],
                "scaling": "StandardScaler",
                "interpolate_param": False,
            },
        },
    }


def _run_forward_smoke(model: PyTorchForecast) -> torch.Tensor:
    """Run one deterministic forward pass.

    :param model: Instantiated Flow Forecast model wrapper.
    :type model: flood_forecast.time_model.PyTorchForecast
    :return: The model prediction tensor.
    :rtype: torch.Tensor
    """
    source, _ = model.training[0]
    with torch.no_grad():
        prediction = model.model(source.unsqueeze(0).to(model.device))
    return prediction.detach().cpu()


def main(argv: list[str] | None = None) -> int:
    """Run the smoke test.

    :param argv: Optional argument vector.
    :type argv: list[str] | None
    :return: Process exit status.
    :rtype: int
    """
    parser = argparse.ArgumentParser(description="Run a tiny NARX smoke test.")
    parser.add_argument("--device", default="cpu", help="Torch device to use. Defaults to cpu.")
    parser.add_argument("--rows", type=int, default=160, help="Number of synthetic hourly rows to generate.")
    parser.add_argument("--fit", action="store_true", help="Run a one-epoch training loop before inference.")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        csv_path = _build_fixture_csv(temp_path, rows=args.rows)
        config = _build_config(csv_path, device=args.device)

        with _temp_cwd(temp_path):
            model = PyTorchForecast(
                config["model_name"],
                config["dataset_params"]["training_path"],
                config["dataset_params"]["validation_path"],
                config["dataset_params"]["test_path"],
                config,
            )
            if args.fit:
                train_transformer_style(
                    model=model,
                    training_params=config["training_params"],
                    takes_target=False,
                    forward_params={},
                    model_filepath="model_save",
                    class2=False,
                )

            config["inference_params"]["dataset_params"]["scaling"] = scaling_function(
                {},
                config["inference_params"]["dataset_params"],
            )["scaling"]
            prediction = _run_forward_smoke(model)
            df, end_tensor, history, forecast_start, loader, samples = infer_on_torch_model(
                model,
                **config["inference_params"],
            )

        print("NARX smoke model:", model.model.__class__.__name__)
        print("Prediction shape:", tuple(prediction.shape))
        print("Inference dataframe rows:", len(df))
        print("Forecast history:", history)
        print("Forecast start index:", forecast_start)
        print("Prediction samples:", len(samples))
        print("End tensor shape:", tuple(end_tensor.shape) if hasattr(end_tensor, "shape") else type(end_tensor))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
