#!/usr/bin/env python3
"""Safe Chronos Forecasting API smoke helper.

By default this script imports Chronos, prints key public signatures, and reports
CPU/CUDA backend visibility. It does not download or load any model unless a
model anchor is supplied explicitly.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import inspect
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect Chronos Forecasting APIs and optionally load a user-supplied model.")
    parser.add_argument(
        "--model-id-or-path",
        default=None,
        help="Optional local path, Hugging Face model ID, or s3:// URI to load. Omit for no-download inspect mode.",
    )
    parser.add_argument("--device-map", default="cpu", help="device_map forwarded to from_pretrained when loading a model.")
    parser.add_argument(
        "--torch-dtype",
        default="auto",
        choices=["auto", "float32", "bfloat16"],
        help="Optional torch_dtype forwarded when loading a model.",
    )
    parser.add_argument("--force-s3-download", action="store_true", help="Forward force_s3_download=True for explicit s3:// model anchors.")
    parser.add_argument("--show-signatures", action="store_true", help="Print a fuller set of public method signatures.")
    return parser


def print_signature(obj, method_name: str) -> None:
    if not hasattr(obj, method_name):
        return
    try:
        print(f"{obj.__name__}.{method_name}{inspect.signature(getattr(obj, method_name))}")
    except Exception as exc:  # noqa: BLE001 - diagnostic output
        print(f"{obj.__name__}.{method_name}: signature unavailable: {exc}")


def inspect_environment(show_signatures: bool) -> int:
    print("Chronos Forecasting API smoke: inspect mode")
    try:
        print(f"chronos-forecasting distribution: {metadata.version('chronos-forecasting')}")
    except metadata.PackageNotFoundError:
        print("chronos-forecasting distribution: not installed")

    try:
        import torch
        import chronos
        from chronos import BaseChronosPipeline, Chronos2Pipeline, ChronosBoltPipeline, ChronosPipeline
    except Exception as exc:  # noqa: BLE001
        print(f"import_status=failed: {exc}", file=sys.stderr)
        return 1

    print(f"chronos import: ok version={getattr(chronos, '__version__', 'unknown')}")
    print(f"torch={torch.__version__} torch_cuda={torch.version.cuda} cuda_available={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        try:
            print(f"cuda_device_count={torch.cuda.device_count()} cuda_device_0={torch.cuda.get_device_name(0)}")
        except Exception as exc:  # noqa: BLE001
            print(f"cuda_detail_unavailable={exc}")

    print("public_exports=BaseChronosPipeline, Chronos2Pipeline, ChronosBoltPipeline, ChronosPipeline")
    for cls, methods in [
        (BaseChronosPipeline, ["from_pretrained", "predict_df", "predict_fev"]),
        (Chronos2Pipeline, ["predict", "predict_quantiles", "predict_df", "fit"]),
        (ChronosBoltPipeline, ["predict", "predict_quantiles"]),
        (ChronosPipeline, ["predict", "predict_quantiles"]),
    ]:
        for method in methods:
            print_signature(cls, method)
    if show_signatures:
        for cls in [Chronos2Pipeline, ChronosBoltPipeline, ChronosPipeline]:
            for method in ["from_pretrained", "embed", "predict_fev", "save_pretrained"]:
                print_signature(cls, method)
    print("smoke_status=passed")
    return 0


def load_model(args: argparse.Namespace) -> int:
    from chronos import BaseChronosPipeline

    load_kwargs = {"device_map": args.device_map}
    if args.torch_dtype != "auto":
        load_kwargs["torch_dtype"] = args.torch_dtype
    if str(args.model_id_or_path).startswith("s3://") and args.force_s3_download:
        load_kwargs["force_s3_download"] = True

    print(f"loading_model={args.model_id_or_path!r}")
    pipeline = BaseChronosPipeline.from_pretrained(args.model_id_or_path, **load_kwargs)
    print(f"loaded_type={type(pipeline).__name__}")
    print(f"forecast_type={pipeline.forecast_type.value}")
    for attr in ["model_context_length", "model_prediction_length"]:
        try:
            print(f"{attr}={getattr(pipeline, attr)}")
        except Exception as exc:  # noqa: BLE001
            print(f"{attr}=unavailable:{exc}")
    if hasattr(pipeline, "quantiles"):
        print(f"quantiles={getattr(pipeline, 'quantiles')}")
    print("model_load_status=passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.model_id_or_path:
        return load_model(args)
    return inspect_environment(args.show_signatures)


if __name__ == "__main__":
    raise SystemExit(main())
