#!/usr/bin/env python3
"""Create a tiny BasicTS forecasting dataset fixture.

This helper writes the minimal split-file layout expected by
`BasicTSForecastingDataset` and is safe to run on any machine with NumPy.

Example:
    python scripts/make_tiny_forecasting_dataset.py --output-dir /path/to/output-dir
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def create_fixture(output_dir: Path, dataset_name: str, total_len: int, num_features: int, with_timestamps: bool) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    values = np.arange(total_len * num_features, dtype=np.float32).reshape(total_len, num_features)
    train_end = int(total_len * 0.6)
    val_end = int(total_len * 0.8)

    np.save(output_dir / "train_data.npy", values[:train_end])
    np.save(output_dir / "val_data.npy", values[train_end:val_end])
    np.save(output_dir / "test_data.npy", values[val_end:])

    timestamps_shape = None
    if with_timestamps:
        timestamps = np.stack(
            [
                np.linspace(0.0, 1.0, total_len, dtype=np.float32),
                np.linspace(0.1, 1.1, total_len, dtype=np.float32),
                np.linspace(0.2, 1.2, total_len, dtype=np.float32),
                np.linspace(0.3, 1.3, total_len, dtype=np.float32),
            ],
            axis=-1,
        )
        timestamps_shape = list(timestamps.shape)
        np.save(output_dir / "train_timestamps.npy", timestamps[:train_end])
        np.save(output_dir / "val_timestamps.npy", timestamps[train_end:val_end])
        np.save(output_dir / "test_timestamps.npy", timestamps[val_end:])

    meta = {
        "name": dataset_name,
        "shape": list(values.shape),
        "timestamps_shape": timestamps_shape,
        "regular_settings": {
            "train_val_test_ratio": [0.6, 0.2, 0.2],
            "norm_each_channel": True,
            "rescale": False,
            "metrics": ["MAE", "MSE"],
            "null_val": None,
        },
    }
    (output_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return output_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a tiny BasicTS forecasting dataset fixture.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory to write the fixture into.")
    parser.add_argument("--dataset-name", default="tiny_forecasting_fixture", help="Name written to meta.json.")
    parser.add_argument("--total-len", type=int, default=32, help="Total sequence length before splitting.")
    parser.add_argument("--num-features", type=int, default=2, help="Number of feature columns.")
    parser.add_argument("--with-timestamps", action="store_true", default=True, help="Write timestamp arrays.")
    parser.add_argument("--no-timestamps", action="store_false", dest="with_timestamps", help="Omit timestamp arrays.")
    args = parser.parse_args()

    output = create_fixture(args.output_dir.expanduser().resolve(), args.dataset_name, args.total_len, args.num_features, args.with_timestamps)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
