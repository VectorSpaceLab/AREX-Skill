#!/usr/bin/env python3
"""Tiny NeuralForecast fit/predict smoke check.

Purpose:
- Prove that the installed NeuralForecast package can generate a tiny panel,
  fit a very small model, and predict a short horizon.
- Keep the check safe, fast, and runnable from any working directory.

Prerequisites:
- A prepared Python environment with the NeuralForecast package installed.
- No repo checkout is required at runtime.

Example:
    python scripts/core_smoke.py --model mlp --h 2 --input-size 4
"""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["mlp", "nhits"], default="mlp", help="Forecast model to smoke-test.")
    parser.add_argument("--h", type=int, default=2, help="Forecast horizon.")
    parser.add_argument("--input-size", type=int, default=4, help="Model input size.")
    parser.add_argument("--n-series", type=int, default=2, help="Number of synthetic series.")
    parser.add_argument("--length", type=int, default=20, help="Length per series.")
    parser.add_argument("--freq", default="D", help="Panel frequency.")
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

    length = max(args.length, args.input_size + args.h + 2)
    df = generate_series(
        n_series=args.n_series,
        min_length=length,
        max_length=length,
        equal_ends=True,
        freq=args.freq,
    )

    model = make_model(args.model, args.h, args.input_size, args.steps)
    nf = NeuralForecast(models=[model], freq=args.freq)
    nf.fit(df)
    preds = nf.predict()

    print(preds.head().to_string(index=False))
    print(f"rows={len(preds)} columns={list(preds.columns)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
