#!/usr/bin/env python3
"""Safe Chronos-2 smoke helper.

Default behavior is inspect-only: no model is loaded and no remote download is
triggered. Provide --model-id-or-path to load a user-supplied Chronos-2 model and
run a tiny synthetic DataFrame forecast.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import inspect
import sys
from typing import Iterable


def _parse_quantiles(text: str) -> list[float]:
    try:
        values = [float(part.strip()) for part in text.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid comma-separated quantiles: {text!r}") from exc
    if not values:
        raise argparse.ArgumentTypeError("at least one quantile is required")
    bad = [q for q in values if not 0.0 < q < 1.0]
    if bad:
        raise argparse.ArgumentTypeError(f"quantiles must be strictly between 0 and 1; got {bad}")
    return values


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect Chronos-2 APIs without loading by default, or run a tiny "
            "DataFrame forecast when --model-id-or-path is explicitly provided."
        )
    )
    parser.add_argument(
        "--model-id-or-path",
        default=None,
        help=(
            "Explicit Chronos-2 model anchor to load: local directory, Hugging Face ID, or s3:// URI. "
            "Omit this option for safe inspect-only mode."
        ),
    )
    parser.add_argument(
        "--inspect-only",
        action="store_true",
        help="Do not load a model even if --model-id-or-path is supplied.",
    )
    parser.add_argument("--device-map", default="cpu", help='device_map forwarded to from_pretrained, e.g. "cpu", "cuda", or "auto".')
    parser.add_argument(
        "--torch-dtype",
        default="auto",
        choices=["auto", "float32", "bfloat16"],
        help="Optional dtype forwarded as torch_dtype when not 'auto'. Use float32 for conservative CPU smokes.",
    )
    parser.add_argument("--prediction-length", type=int, default=4, help="Tiny synthetic forecast horizon.")
    parser.add_argument("--history-length", type=int, default=16, help="Synthetic history length per item.")
    parser.add_argument("--batch-size", type=int, default=8, help="Prediction batch size.")
    parser.add_argument("--context-length", type=int, default=None, help="Optional inference context_length override.")
    parser.add_argument("--cross-learning", action="store_true", help="Enable Chronos-2 cross_learning for the tiny forecast.")
    parser.add_argument(
        "--quantiles",
        type=_parse_quantiles,
        default=[0.1, 0.5, 0.9],
        help="Comma-separated quantile levels, default: 0.1,0.5,0.9.",
    )
    parser.add_argument(
        "--force-s3-download",
        action="store_true",
        help="Forward force_s3_download=True for explicit s3:// model anchors.",
    )
    return parser


def _print_lines(lines: Iterable[str]) -> None:
    for line in lines:
        print(line)


def inspect_chronos() -> int:
    _print_lines(
        [
            "Chronos-2 smoke helper: inspect-only mode",
            "No model was loaded; no remote download was requested.",
        ]
    )
    try:
        version = metadata.version("chronos-forecasting")
        print(f"chronos-forecasting distribution: {version}")
    except metadata.PackageNotFoundError:
        print("chronos-forecasting distribution: not installed in this Python environment")

    try:
        from chronos import BaseChronosPipeline, Chronos2Pipeline
    except Exception as exc:  # noqa: BLE001 - human-facing smoke script
        print(f"chronos import: failed: {exc}")
        return 0

    print("chronos import: ok")
    for cls, method_names in [
        (BaseChronosPipeline, ["from_pretrained"]),
        (
            Chronos2Pipeline,
            ["from_pretrained", "predict", "predict_quantiles", "predict_df", "predict_fev", "embed", "fit", "save_pretrained"],
        ),
    ]:
        for name in method_names:
            if hasattr(cls, name):
                try:
                    print(f"{cls.__name__}.{name}{inspect.signature(getattr(cls, name))}")
                except Exception as exc:  # noqa: BLE001
                    print(f"{cls.__name__}.{name}: signature unavailable: {exc}")
    return 0


def make_synthetic_frames(history_length: int, prediction_length: int):
    import numpy as np
    import pandas as pd

    if history_length < 2:
        raise ValueError("history_length must be at least 2")
    if prediction_length < 1:
        raise ValueError("prediction_length must be at least 1")

    rows = []
    future_rows = []
    base_time = pd.Timestamp("2024-01-01 00:00:00")
    for item_idx, item_id in enumerate(["A", "B"]):
        history_times = pd.date_range(base_time, periods=history_length, freq="h")
        future_times = pd.date_range(history_times[-1] + pd.Timedelta(hours=1), periods=prediction_length, freq="h")
        trend = np.linspace(0.0, 1.0, history_length)
        seasonal = np.sin(np.arange(history_length) / 3.0)
        target = 10.0 + item_idx * 5.0 + trend + seasonal
        temperature = 20.0 + item_idx + np.cos(np.arange(history_length) / 4.0)
        promo = np.where(np.arange(history_length) % 5 == 0, "yes", "no")
        for ts, y, temp, promo_value in zip(history_times, target, temperature, promo):
            rows.append(
                {
                    "item_id": item_id,
                    "timestamp": ts,
                    "sales": float(y),
                    "temperature": float(temp),
                    "promo": str(promo_value),
                }
            )
        future_temperature = 20.0 + item_idx + np.cos((np.arange(prediction_length) + history_length) / 4.0)
        future_promo = np.where((np.arange(prediction_length) + history_length) % 5 == 0, "yes", "no")
        for ts, temp, promo_value in zip(future_times, future_temperature, future_promo):
            future_rows.append(
                {
                    "item_id": item_id,
                    "timestamp": ts,
                    "temperature": float(temp),
                    "promo": str(promo_value),
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(future_rows)


def run_forecast(args: argparse.Namespace) -> int:
    from chronos import BaseChronosPipeline, Chronos2Pipeline

    load_kwargs = {"device_map": args.device_map}
    if args.torch_dtype != "auto":
        load_kwargs["torch_dtype"] = args.torch_dtype
    if str(args.model_id_or_path).startswith("s3://") and args.force_s3_download:
        load_kwargs["force_s3_download"] = True

    print(f"Loading model anchor: {args.model_id_or_path!r}")
    pipeline = BaseChronosPipeline.from_pretrained(args.model_id_or_path, **load_kwargs)
    print(f"Loaded pipeline type: {type(pipeline).__name__}")
    if not isinstance(pipeline, Chronos2Pipeline):
        raise SystemExit("Loaded model is not a Chronos2Pipeline; use a Chronos-2 model anchor.")

    print(f"model_context_length={pipeline.model_context_length}")
    print(f"model_prediction_length={pipeline.model_prediction_length}")
    print(f"model_quantiles={pipeline.quantiles}")

    context_df, future_df = make_synthetic_frames(args.history_length, args.prediction_length)
    forecast = pipeline.predict_df(
        context_df,
        future_df=future_df,
        id_column="item_id",
        timestamp_column="timestamp",
        target="sales",
        prediction_length=args.prediction_length,
        quantile_levels=args.quantiles,
        batch_size=args.batch_size,
        context_length=args.context_length,
        cross_learning=args.cross_learning,
    )
    print(f"forecast_shape={forecast.shape}")
    print("forecast_columns=" + ",".join(map(str, forecast.columns)))
    print(forecast.head(min(len(forecast), 8)).to_string(index=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.inspect_only or not args.model_id_or_path:
        return inspect_chronos()
    return run_forecast(args)


if __name__ == "__main__":
    raise SystemExit(main())
