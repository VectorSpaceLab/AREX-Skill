#!/usr/bin/env python3
"""Tiny Darts torch model smoke.

Default mode imports torch/Darts and constructs a small TCNModel. Use --train to
run one CPU epoch on generated data. Training uses a temporary directory and
removes it automatically.
"""
from __future__ import annotations

import argparse
import json
import tempfile

import numpy as np
import pandas as pd


def run(train: bool = False) -> dict:
    import torch
    from darts import TimeSeries
    from darts.models import TCNModel

    dates = pd.date_range("2024-01-01", periods=40, freq="D")
    values = np.sin(np.arange(40) / 3.0).astype("float32")
    series = TimeSeries.from_times_and_values(dates, values, columns=["signal"])

    result = {
        "status": "ok",
        "torch_version": torch.__version__,
        "cuda_available": bool(torch.cuda.is_available()),
        "trained": False,
    }

    with tempfile.TemporaryDirectory(prefix="darts-torch-smoke-") as work_dir:
        model = TCNModel(
            input_chunk_length=12,
            output_chunk_length=3,
            n_epochs=1,
            batch_size=4,
            num_filters=2,
            kernel_size=2,
            random_state=42,
            force_reset=True,
            save_checkpoints=False,
            work_dir=work_dir,
            pl_trainer_kwargs={
                "accelerator": "cpu",
                "devices": 1,
                "enable_progress_bar": False,
                "enable_model_summary": False,
                "logger": False,
            },
        )
        result["model_class"] = type(model).__name__
        if train:
            model.fit(series, verbose=False)
            forecast = model.predict(3)
            assert len(forecast) == 3
            result.update(
                {
                    "trained": True,
                    "forecast_length": len(forecast),
                    "forecast_components": list(map(str, forecast.components)),
                }
            )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", action="store_true", help="run one CPU training epoch")
    args = parser.parse_args()
    print(json.dumps(run(train=args.train), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
