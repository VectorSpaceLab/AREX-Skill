#!/usr/bin/env python3
"""Offline shape smoke test for segmentation_models_pytorch models."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def _none_or_string(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if normalized.lower() in {"", "none", "null", "offline"}:
        return None
    return normalized


def _shape(value: Any) -> list[int] | None:
    shape = getattr(value, "shape", None)
    if shape is None:
        return None
    return [int(dim) for dim in shape]


def _json_result(payload: dict[str, Any], exit_code: int) -> int:
    print(json.dumps(payload, sort_keys=True))
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a segmentation_models_pytorch model, run one deterministic "
            "NCHW forward pass, and print a JSON shape report. Defaults avoid "
            "pretrained weight downloads by passing encoder_weights=None."
        )
    )
    parser.add_argument(
        "--arch",
        default="unet",
        help="Architecture key for smp.create_model, for example unet, fpn, deeplabv3plus, segformer, or dpt.",
    )
    parser.add_argument(
        "--encoder",
        default=None,
        help="Encoder name. Defaults to resnet18, or tu-vit_tiny_patch16_224 for dpt.",
    )
    parser.add_argument(
        "--encoder-weights",
        default="none",
        help="Encoder weights name. Use none/offline/null to pass None and avoid downloads. Default: none.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Force encoder_weights=None even if --encoder-weights is provided.",
    )
    parser.add_argument("--in-channels", type=int, default=3, help="Input tensor channels. Default: 3.")
    parser.add_argument("--classes", type=int, default=1, help="Segmentation mask output channels. Default: 1.")
    parser.add_argument("--height", type=int, default=None, help="Input tensor height. Defaults to 64, or 224 for dpt.")
    parser.add_argument("--width", type=int, default=None, help="Input tensor width. Defaults to 64, or 224 for dpt.")
    parser.add_argument(
        "--aux",
        action="store_true",
        help="Enable an auxiliary classification head and validate tuple output.",
    )
    parser.add_argument("--aux-classes", type=int, default=2, help="Auxiliary label output classes. Default: 2.")
    parser.add_argument(
        "--dynamic-img-size",
        action="store_true",
        help="Pass dynamic_img_size=True for DPT/timm encoders that support dynamic image sizes.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    arch = args.arch.lower()
    encoder_name = args.encoder or ("tu-vit_tiny_patch16_224" if arch == "dpt" else "resnet18")
    encoder_weights = None if args.offline else _none_or_string(args.encoder_weights)
    height = args.height if args.height is not None else (224 if arch == "dpt" else 64)
    width = args.width if args.width is not None else (224 if arch == "dpt" else 64)

    if args.in_channels <= 0 or args.classes <= 0 or height <= 0 or width <= 0:
        return _json_result(
            {
                "ok": False,
                "error_type": "ArgumentError",
                "error": "--in-channels, --classes, --height, and --width must be positive integers.",
            },
            2,
        )

    try:
        import torch
        import segmentation_models_pytorch as smp
    except Exception as exc:  # pragma: no cover - depends on runtime installation
        return _json_result(
            {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "stage": "import",
            },
            2,
        )

    try:
        torch.manual_seed(0)
        aux_params = None
        if args.aux:
            aux_params = {
                "pooling": "avg",
                "dropout": 0.0,
                "activation": None,
                "classes": args.aux_classes,
            }

        model_kwargs: dict[str, Any] = {}
        if arch == "dpt" and args.dynamic_img_size:
            model_kwargs["dynamic_img_size"] = True

        model = smp.create_model(
            arch=arch,
            encoder_name=encoder_name,
            encoder_weights=encoder_weights,
            in_channels=args.in_channels,
            classes=args.classes,
            aux_params=aux_params,
            **model_kwargs,
        ).eval()

        sample = torch.zeros(1, args.in_channels, height, width)
        with torch.inference_mode():
            output = model(sample)

        if isinstance(output, tuple):
            mask = output[0]
            label = output[1] if len(output) > 1 else None
            output_type = "tuple"
        else:
            mask = output
            label = None
            output_type = "tensor"

        payload = {
            "ok": True,
            "version": getattr(smp, "__version__", None),
            "arch": arch,
            "encoder_name": encoder_name,
            "encoder_weights": encoder_weights,
            "input_shape": [1, args.in_channels, height, width],
            "mask_shape": _shape(mask),
            "label_shape": _shape(label),
            "output_type": output_type,
            "model_class": type(model).__name__,
            "model_name": getattr(model, "name", None),
            "requires_divisible_input_shape": bool(getattr(model, "requires_divisible_input_shape", False)),
            "encoder_output_stride": getattr(getattr(model, "encoder", None), "output_stride", None),
            "aux_enabled": bool(args.aux),
        }
        return _json_result(payload, 0)
    except Exception as exc:
        return _json_result(
            {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "stage": "model_forward",
                "arch": arch,
                "encoder_name": encoder_name,
                "encoder_weights": encoder_weights,
                "input_shape": [1, args.in_channels, height, width],
            },
            2,
        )


if __name__ == "__main__":
    raise SystemExit(main())
