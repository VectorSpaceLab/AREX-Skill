#!/usr/bin/env python3
"""Safe tiny PyTorch smoke for ResNeSt.

This helper stays offline by default, uses pretrained=False unless requested,
and can optionally run a tiny Split-Attention smoke.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterable

SUPPORTED_MODELS = (
    "resnest50",
    "resnest101",
    "resnest200",
    "resnest269",
    "resnest50_fast_1s1x64d",
    "resnest50_fast_2s1x64d",
    "resnest50_fast_4s1x64d",
    "resnest50_fast_1s2x40d",
    "resnest50_fast_2s2x40d",
    "resnest50_fast_4s2x40d",
    "resnest50_fast_1s4x24d",
    "resnet50",
    "resnet101",
    "resnet152",
)

PRETRAINED_MODELS = {
    "resnest50",
    "resnest101",
    "resnest200",
    "resnest269",
    "resnest50_fast_1s1x64d",
    "resnest50_fast_2s1x64d",
    "resnest50_fast_4s1x64d",
    "resnest50_fast_1s2x40d",
    "resnest50_fast_2s2x40d",
    "resnest50_fast_4s2x40d",
    "resnest50_fast_1s4x24d",
}


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}")
    return parsed


def import_torch():
    try:
        import torch  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "ERROR: torch is required for this smoke. Install the PyTorch runtime and retry."
        ) from exc
    return torch


def import_resnest():
    try:
        import resnest.torch as resnest_torch  # type: ignore
        from resnest.torch.models.build import get_model  # type: ignore
        from resnest.torch.models.splat import SplAtConv2d  # type: ignore
    except ModuleNotFoundError as exc:
        missing = getattr(exc, "name", None) or str(exc)
        if missing in {"resnest", "fvcore", "iopath"}:
            raise SystemExit(
                "ERROR: the ResNeSt PyTorch package or one of its required support libraries is missing. "
                "Install the package requirements and retry."
            ) from exc
        raise SystemExit(f"ERROR: failed to import the ResNeSt PyTorch surface: {missing}") from exc
    return resnest_torch, get_model, SplAtConv2d


def choose_device(torch, requested: str):
    if requested == "cpu":
        return torch.device("cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise SystemExit("ERROR: --device cuda was requested but CUDA is not available.")
        return torch.device("cuda")
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    raise SystemExit(f"ERROR: unknown device selector {requested!r}")


def resolve_factory(resnest_torch, get_model, model_name: str):
    factory = getattr(resnest_torch, model_name, None)
    if factory is not None:
        return factory
    try:
        return get_model(model_name)
    except Exception as exc:  # registry KeyError or other lookup failure
        raise SystemExit(
            f"ERROR: unknown model {model_name!r}. Use one of the supported names from --help."
        ) from exc


def run_model_smoke(torch, model, batch_size: int, image_size: int, classes: int, device):
    x = torch.zeros(batch_size, 3, image_size, image_size, device=device)
    try:
        with torch.no_grad():
            y = model(x)
    except RuntimeError as exc:
        raise SystemExit(
            f"ERROR: {model.__class__.__name__} failed on a {image_size}x{image_size} tensor. "
            f"Try a larger image size such as 64. Original error: {exc}"
        ) from exc

    expected = (batch_size, classes)
    actual = tuple(y.shape)
    if actual != expected:
        raise SystemExit(
            f"ERROR: expected output shape {expected} but got {actual}. "
            "Check the selected class count and model factory."
        )
    return actual


def run_splat_smoke(torch, SplAtConv2d, batch_size: int, device):
    layer = SplAtConv2d(4, 4, kernel_size=3, padding=1, radix=2, groups=1, bias=False)
    layer = layer.to(device)
    x = torch.zeros(batch_size, 4, 8, 8, device=device)
    try:
        with torch.no_grad():
            y = layer(x)
    except RuntimeError as exc:
        raise SystemExit(
            "ERROR: SplAtConv2d failed on the tiny smoke tensor. "
            "Check radix/groups compatibility and retry. Original error: "
            f"{exc}"
        ) from exc
    expected = (batch_size, 4, 8, 8)
    actual = tuple(y.shape)
    if actual != expected:
        raise SystemExit(
            f"ERROR: expected Split-Attention output shape {expected} but got {actual}."
        )
    return actual


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a safe tiny ResNeSt PyTorch smoke without downloading weights by default.")
    parser.add_argument(
        "--model",
        default="resnest50",
        choices=SUPPORTED_MODELS,
        help="Model factory name to instantiate.",
    )
    parser.add_argument(
        "--image-size",
        type=positive_int,
        default=64,
        help="Square input size for the tiny forward smoke.",
    )
    parser.add_argument(
        "--batch-size",
        type=positive_int,
        default=1,
        help="Batch size for the tiny forward smoke.",
    )
    parser.add_argument(
        "--classes",
        type=positive_int,
        default=1000,
        help="Classifier output size to request from the factory.",
    )
    parser.add_argument(
        "--pretrained",
        action="store_true",
        help="Load pretrained weights. This may download via the PyTorch Hub cache.",
    )
    parser.add_argument(
        "--check-splat",
        action="store_true",
        help="Also run a tiny SplAtConv2d smoke.",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="cpu",
        help="Device used for the smoke.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    torch = import_torch()
    resnest_torch, get_model, SplAtConv2d = import_resnest()

    if args.pretrained:
        print(
            "WARNING: --pretrained may download official weights through the PyTorch Hub cache.",
            file=sys.stderr,
        )
        if args.classes != 1000:
            parser.error("pretrained weights in this release are ImageNet-1000 weights; keep --classes 1000")
        if args.model not in PRETRAINED_MODELS:
            parser.error(
                f"pretrained weights are not published for {args.model!r}; choose a ResNeSt core or fast factory"
            )

    device = choose_device(torch, args.device)
    factory = resolve_factory(resnest_torch, get_model, args.model)

    model_kwargs = {}
    if args.classes != 1000:
        model_kwargs["num_classes"] = args.classes

    try:
        model = factory(pretrained=args.pretrained, **model_kwargs)
    except Exception as exc:
        if args.pretrained:
            raise SystemExit(
                f"ERROR: failed to load pretrained weights for {args.model!r}. "
                "Check network access, PyTorch Hub cache state, and classifier size."
            ) from exc
        raise

    model = model.to(device)
    model.eval()

    output_shape = run_model_smoke(torch, model, args.batch_size, args.image_size, args.classes, device)

    result = {
        "device": str(device),
        "model": args.model,
        "pretrained": bool(args.pretrained),
        "input_shape": [args.batch_size, 3, args.image_size, args.image_size],
        "output_shape": list(output_shape),
    }

    if args.check_splat:
        splat_shape = run_splat_smoke(torch, SplAtConv2d, args.batch_size, device)
        result["splat_input_shape"] = [args.batch_size, 4, 8, 8]
        result["splat_output_shape"] = list(splat_shape)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
