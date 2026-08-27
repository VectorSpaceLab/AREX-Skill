#!/usr/bin/env python3
"""Tiny NeuralForecast save/load round-trip.

Purpose:
- Fit a tiny model, save it, reload it, and confirm prediction still works.
- Prove portability without relying on the source checkout.

Prerequisites:
- NeuralForecast installed in the active environment.
- A writable temporary directory.

Example:
    python scripts/check_serialization.py
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["mlp", "nhits"], default="mlp", help="Model to round-trip.")
    parser.add_argument("--h", type=int, default=2, help="Forecast horizon.")
    parser.add_argument("--input-size", type=int, default=4, help="Model input size.")
    parser.add_argument("--steps", type=int, default=1, help="Training steps.")
    return parser


def make_model(name: str, h: int, input_size: int, steps: int):
    from neuralforecast.losses.pytorch import MAE
    if name == "mlp":
        from neuralforecast.models import MLP
        return MLP(h=h, input_size=input_size, max_steps=steps, val_check_steps=1, enable_progress_bar=False, loss=MAE())
    from neuralforecast.models import NHITS
    return NHITS(h=h, input_size=input_size, max_steps=steps, val_check_steps=1, enable_progress_bar=False, loss=MAE())


def main() -> int:
    args = build_parser().parse_args()

    from neuralforecast import NeuralForecast
    from neuralforecast.utils import generate_series

    length = max(20, args.input_size + args.h + 2)
    df = generate_series(n_series=2, min_length=length, max_length=length, equal_ends=True)
    model = make_model(args.model, args.h, args.input_size, args.steps)
    nf = NeuralForecast(models=[model], freq="D")
    nf.fit(df)
    first = nf.predict()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "nf-save"
        nf.save(str(path), overwrite=True)
        restored = NeuralForecast.load(str(path))
        second = restored.predict()

    assert list(first.columns) == list(second.columns)
    assert len(first) == len(second)
    print("serialization round-trip passed")
    print(f"rows={len(first)} columns={list(first.columns)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
