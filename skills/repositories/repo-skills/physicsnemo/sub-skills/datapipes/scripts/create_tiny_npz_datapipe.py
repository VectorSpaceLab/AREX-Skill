#!/usr/bin/env python3
"""Create and exercise a tiny PhysicsNeMo NPZ datapipe.

The script creates a temporary NPZ fixture, reads it with NumpyReader,
wraps it in Dataset/DataLoader, and prints a tiny batch summary. It is safe
on CPU and can optionally move the dataset to CUDA if available.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np


def build_fixture(path: Path) -> None:
    x = np.arange(24, dtype=np.float32).reshape(6, 4)
    y = (x.sum(axis=1, keepdims=True) * 0.1).astype(np.float32)
    np.savez(path, x=x, y=y)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="Target dataset device.")
    parser.add_argument("--keep-temp", action="store_true", help="Keep the temporary fixture directory.")
    args = parser.parse_args()

    work = Path(tempfile.mkdtemp(prefix="physicsnemo-dp-"))
    try:
        fixture = work / "tiny.npz"
        build_fixture(fixture)

        from physicsnemo.datapipes import DataLoader, Dataset, Normalize, NumpyReader

        device = args.device
        if device == "cuda":
            try:
                import torch

                if not torch.cuda.is_available():
                    device = "cpu"
            except Exception:
                device = "cpu"

        reader = NumpyReader(fixture, fields=["x", "y"])
        sample, metadata = reader[0]
        dataset = Dataset(
            reader,
            transforms=[
                Normalize(
                    input_keys=["x", "y"],
                    method="mean_std",
                    means={"x": 0.0, "y": 0.0},
                    stds={"x": 1.0, "y": 1.0},
                )
            ],
            device=device,
            num_workers=0,
        )
        loader = DataLoader(dataset, batch_size=2, shuffle=False, prefetch_factor=0, use_streams=False)
        batch = next(iter(loader))
        if isinstance(batch, tuple):
            payload, batch_meta = batch
        else:
            payload, batch_meta = batch, None

        summary = {
            "fixture": str(fixture),
            "device": device,
            "reader_sample_keys": list(sample.keys()),
            "reader_metadata_keys": list(metadata.keys()) if isinstance(metadata, dict) else None,
            "batch_type": type(payload).__name__,
            "batch_keys": list(payload.keys()) if hasattr(payload, "keys") else None,
            "batch_metadata": batch_meta,
        }
        print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    finally:
        if args.keep_temp:
            print(f"Temporary directory kept at: {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
