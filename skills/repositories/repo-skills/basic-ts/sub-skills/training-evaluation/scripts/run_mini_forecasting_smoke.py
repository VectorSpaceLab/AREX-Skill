#!/usr/bin/env python3
"""Run a safe CPU forecasting smoke test for BasicTS.

This helper creates a tiny temporary forecasting dataset, launches one CPU
training epoch with a built-in model, and leaves no dependency on the original
repository checkout.

Example:
    python scripts/run_mini_forecasting_smoke.py
    python scripts/run_mini_forecasting_smoke.py --work-dir /path/to/work-dir --keep-work-dir
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np

from basicts import BasicTSLauncher
from basicts.configs import BasicTSForecastingConfig
from basicts.models.DLinear import DLinear, DLinearConfig


def write_fixture(root: Path, input_len: int, output_len: int, num_features: int) -> Path:
    """Create a tiny forecasting dataset layout under *root* and return it."""

    data_dir = root / "tiny_forecasting_smoke"
    data_dir.mkdir(parents=True, exist_ok=True)

    total_len = max((input_len + output_len) * 6, 60)
    values = np.arange(total_len * num_features, dtype=np.float32).reshape(total_len, num_features)
    timestamps = np.stack(
        [
            np.linspace(0.0, 1.0, total_len, dtype=np.float32),
            np.linspace(0.1, 1.1, total_len, dtype=np.float32),
            np.linspace(0.2, 1.2, total_len, dtype=np.float32),
            np.linspace(0.3, 1.3, total_len, dtype=np.float32),
        ],
        axis=-1,
    )

    train_end = int(total_len * 0.6)
    val_end = int(total_len * 0.8)

    np.save(data_dir / "train_data.npy", values[:train_end])
    np.save(data_dir / "val_data.npy", values[train_end:val_end])
    np.save(data_dir / "test_data.npy", values[val_end:])
    np.save(data_dir / "train_timestamps.npy", timestamps[:train_end])
    np.save(data_dir / "val_timestamps.npy", timestamps[train_end:val_end])
    np.save(data_dir / "test_timestamps.npy", timestamps[val_end:])

    meta = {
        "name": "tiny_forecasting_smoke",
        "shape": list(values.shape),
        "timestamps_shape": list(timestamps.shape),
        "regular_settings": {
            "train_val_test_ratio": [0.6, 0.2, 0.2],
            "norm_each_channel": True,
            "rescale": False,
            "metrics": ["MAE", "MSE"],
            "null_val": None,
        },
    }
    (data_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return data_dir


def run_smoke(work_dir: Path, input_len: int, output_len: int, num_features: int, num_epochs: int, keep_work_dir: bool) -> int:
    fixture_dir = write_fixture(work_dir, input_len, output_len, num_features)
    ckpt_dir = work_dir / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    model_config = DLinearConfig(
        input_len=input_len,
        output_len=output_len,
        num_features=num_features,
        individual=False,
    )

    cfg = BasicTSForecastingConfig(
        model=DLinear,
        model_config=model_config,
        dataset_name=fixture_dir.name,
        input_len=input_len,
        output_len=output_len,
        use_timestamps=True,
        gpus=None,
        num_epochs=num_epochs,
        batch_size=2,
        ckpt_save_dir=str(ckpt_dir),
        dataset_params={
            "data_file_path": str(fixture_dir),
            "use_timestamps": True,
            "memmap": False,
        },
    )

    BasicTSLauncher.launch_training(cfg)

    print(f"Smoke dataset: {fixture_dir}")
    print(f"Checkpoint root: {ckpt_dir}")
    print("Smoke run completed successfully.")

    if not keep_work_dir:
        shutil.rmtree(work_dir, ignore_errors=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe CPU BasicTS forecasting smoke test.")
    parser.add_argument("--work-dir", type=Path, default=None, help="Directory to create the temporary fixture in.")
    parser.add_argument("--keep-work-dir", action="store_true", help="Keep the generated fixture and checkpoints.")
    parser.add_argument("--input-len", type=int, default=8, help="Forecasting input length.")
    parser.add_argument("--output-len", type=int, default=4, help="Forecasting output length.")
    parser.add_argument("--num-features", type=int, default=2, help="Number of feature columns in the fixture.")
    parser.add_argument("--num-epochs", type=int, default=1, help="Training epochs for the smoke test.")
    args = parser.parse_args()

    if args.work_dir is None:
        with tempfile.TemporaryDirectory(prefix="basic-ts-smoke-") as tmp:
            return run_smoke(Path(tmp), args.input_len, args.output_len, args.num_features, args.num_epochs, False)

    args.work_dir.mkdir(parents=True, exist_ok=True)
    return run_smoke(args.work_dir, args.input_len, args.output_len, args.num_features, args.num_epochs, args.keep_work_dir)


if __name__ == "__main__":
    raise SystemExit(main())
