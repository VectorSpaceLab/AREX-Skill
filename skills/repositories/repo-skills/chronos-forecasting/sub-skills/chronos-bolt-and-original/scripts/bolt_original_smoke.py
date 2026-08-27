#!/usr/bin/env python3
"""Safe Chronos-Bolt/original Chronos import and tiny-forecast smoke.

Default behavior is inspection only: it imports the public API and prints
signatures without loading model weights. A model is loaded only when
--model-id-or-path is supplied. Non-local Hugging Face or S3 identifiers also
require --allow-remote to make network/cloud side effects explicit.
"""

from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path
from typing import Iterable


def parse_quantile_levels(raw: str) -> list[float]:
    try:
        levels = [float(part.strip()) for part in raw.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid comma-separated quantile levels: {raw!r}") from exc
    if not levels:
        raise argparse.ArgumentTypeError("at least one quantile level is required")
    bad = [q for q in levels if q < 0.0 or q > 1.0]
    if bad:
        raise argparse.ArgumentTypeError(f"quantile levels must be in [0, 1], got {bad}")
    return levels


def is_existing_local_path(value: str) -> bool:
    return Path(value).expanduser().exists()


def looks_remote(value: str) -> bool:
    if value.startswith("s3://"):
        return True
    return not is_existing_local_path(value)


def print_signature_table(classes: Iterable[type]) -> None:
    method_names = ["from_pretrained", "predict", "predict_quantiles", "predict_df", "embed", "predict_fev"]
    for cls in classes:
        for method_name in method_names:
            if hasattr(cls, method_name):
                try:
                    sig = inspect.signature(getattr(cls, method_name))
                except (TypeError, ValueError) as exc:
                    print(f"{cls.__name__}.{method_name}: signature unavailable: {exc}")
                else:
                    print(f"{cls.__name__}.{method_name}{sig}")


def inspect_only() -> None:
    import torch
    import chronos
    from chronos import BaseChronosPipeline, ChronosBoltPipeline, ChronosPipeline

    print(f"chronos version: {getattr(chronos, '__version__', 'unknown')}")
    print(f"torch version: {torch.__version__}; cuda_available={torch.cuda.is_available()}")
    print_signature_table([BaseChronosPipeline, ChronosBoltPipeline, ChronosPipeline])


def make_context(context_length: int, input_dtype: str):
    import torch

    if context_length < 2:
        raise ValueError("--context-length must be at least 2")
    base = torch.linspace(1.0, float(context_length), steps=context_length)
    context = torch.stack([base, base.mul(0.5).add(3.0)], dim=0)
    if input_dtype == "bfloat16":
        context = context.to(torch.bfloat16)
    elif input_dtype == "int64":
        context = context.round().to(torch.int64)
    else:
        context = context.to(torch.float32)
    return context


def tensor_summary(name: str, tensor) -> None:
    import torch

    detached = tensor.detach().cpu()
    finite = detached[torch.isfinite(detached)]
    if finite.numel():
        min_value = float(finite.min())
        max_value = float(finite.max())
    else:
        min_value = max_value = float("nan")
    print(
        f"{name}: shape={tuple(detached.shape)} dtype={detached.dtype} "
        f"device={detached.device} finite_min={min_value:.6g} finite_max={max_value:.6g}"
    )


def load_and_forecast(args: argparse.Namespace) -> None:
    from chronos import BaseChronosPipeline, ChronosBoltPipeline, ChronosPipeline

    if looks_remote(args.model_id_or_path) and not args.allow_remote:
        raise SystemExit(
            "Refusing to load a non-local model identifier without --allow-remote. "
            "Use a local model directory or pass --allow-remote to permit HF/S3 downloads."
        )

    load_kwargs = {"device_map": args.device_map}
    if args.torch_dtype != "auto":
        load_kwargs["torch_dtype"] = args.torch_dtype

    pipeline = BaseChronosPipeline.from_pretrained(
        args.model_id_or_path,
        force_s3_download=args.force_s3_download,
        **load_kwargs,
    )

    expected_cls = ChronosBoltPipeline if args.family == "bolt" else ChronosPipeline
    if not isinstance(pipeline, expected_cls):
        raise SystemExit(
            f"Loaded {type(pipeline).__name__}, but --family {args.family!r} expected {expected_cls.__name__}."
        )

    print(f"loaded pipeline: {type(pipeline).__name__}")
    print(f"forecast_type: {pipeline.forecast_type.value}")
    print(f"model_context_length: {pipeline.model_context_length}")
    print(f"model_prediction_length: {pipeline.model_prediction_length}")

    context = make_context(args.context_length, args.input_dtype)
    tensor_summary("context", context)

    if args.family == "bolt":
        raw = pipeline.predict(
            context,
            prediction_length=args.prediction_length,
            limit_prediction_length=args.limit_prediction_length,
        )
        tensor_summary("bolt_predict_quantile_channels", raw)
        quantiles, point = pipeline.predict_quantiles(
            context,
            prediction_length=args.prediction_length,
            quantile_levels=args.quantile_levels,
            limit_prediction_length=args.limit_prediction_length,
        )
        tensor_summary("bolt_predict_quantiles", quantiles)
        tensor_summary("bolt_point_forecast_median_channel", point)
        print(f"training_quantiles: {getattr(pipeline, 'quantiles', None)}")
    else:
        samples = pipeline.predict(
            context,
            prediction_length=args.prediction_length,
            num_samples=args.num_samples,
            limit_prediction_length=args.limit_prediction_length,
        )
        tensor_summary("original_predict_samples", samples)
        quantiles, mean = pipeline.predict_quantiles(
            context,
            prediction_length=args.prediction_length,
            quantile_levels=args.quantile_levels,
            num_samples=args.num_samples,
            limit_prediction_length=args.limit_prediction_length,
        )
        tensor_summary("original_predict_quantiles", quantiles)
        tensor_summary("original_predict_mean", mean)



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect Chronos-Bolt/original public APIs and optionally load a user-supplied model "
            "for a tiny tensor forecast. Default with no model is inspection only."
        )
    )
    parser.add_argument("--inspect-only", action="store_true", help="Only import and print API signatures; do not load a model.")
    parser.add_argument(
        "--model-id-or-path",
        default=None,
        help="Local model directory, Hugging Face model ID, or s3:// URI. Omit for safe inspection only.",
    )
    parser.add_argument("--family", choices=["bolt", "original"], default="bolt", help="Expected model family for optional loading.")
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="Permit non-local Hugging Face/S3 model downloads. Required for remote-looking identifiers.",
    )
    parser.add_argument("--force-s3-download", action="store_true", help="Refresh cached S3 model contents when loading s3:// URIs.")
    parser.add_argument("--device-map", default="cpu", help="Transformers device_map value for model loading; default: cpu.")
    parser.add_argument("--torch-dtype", choices=["auto", "float32", "bfloat16"], default="float32", help="Model dtype hint.")
    parser.add_argument("--input-dtype", choices=["float32", "bfloat16", "int64"], default="float32", help="Tiny synthetic context dtype.")
    parser.add_argument("--context-length", type=int, default=16, help="Synthetic context length; default: 16.")
    parser.add_argument("--prediction-length", type=int, default=3, help="Tiny forecast horizon; default: 3.")
    parser.add_argument("--num-samples", type=int, default=4, help="Original Chronos sample count; ignored for Bolt.")
    parser.add_argument(
        "--quantile-levels",
        type=parse_quantile_levels,
        default=[0.1, 0.5, 0.9],
        help="Comma-separated quantile levels for predict_quantiles; default: 0.1,0.5,0.9.",
    )
    parser.add_argument(
        "--limit-prediction-length",
        action="store_true",
        help="Raise instead of warning when requested horizon exceeds the model default.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    inspect_only()
    if args.inspect_only or not args.model_id_or_path:
        print("inspection complete; no model loaded")
        return 0

    load_and_forecast(args)
    print("tiny forecast smoke complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
