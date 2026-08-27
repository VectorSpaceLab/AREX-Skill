#!/usr/bin/env python3
"""Inspect a segmentation_models_pytorch encoder or preprocessing config as JSON.

Defaults avoid pretrained weight downloads: encoder weights default to None and
preprocessing parameters are queried only when --include-preprocessing or
--preprocessing-only is set.
"""

from __future__ import annotations

import argparse
import json
import traceback
import warnings
from typing import Any


def parse_weight(value: str | None) -> Any:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"none", "null", "false", "0"}:
        return None
    if normalized in {"true", "1", "yes"}:
        return True
    return value


def safe_exception(error: BaseException) -> dict[str, str]:
    message = str(error).splitlines()[0] if str(error) else error.__class__.__name__
    return {"type": error.__class__.__name__, "message": message}


def inspect_preprocessing(smp: Any, encoder_name: str, pretrained: str) -> dict[str, Any]:
    params = smp.encoders.get_preprocessing_params(encoder_name, pretrained=pretrained)
    return {
        "ok": True,
        "pretrained": pretrained,
        "params": params,
    }


def inspect_encoder(
    smp: Any,
    encoder_name: str,
    weights: Any,
    depth: int,
    output_stride: int,
    in_channels: int,
) -> dict[str, Any]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        encoder = smp.encoders.get_encoder(
            encoder_name,
            in_channels=in_channels,
            depth=depth,
            weights=weights,
            output_stride=output_stride,
        )

    return {
        "ok": True,
        "weights": weights,
        "depth": depth,
        "output_stride_requested": output_stride,
        "encoder_class": encoder.__class__.__name__,
        "output_stride_effective": getattr(encoder, "output_stride", None),
        "out_channels": list(getattr(encoder, "out_channels", [])),
        "warnings": [
            {
                "type": warning.category.__name__,
                "message": str(warning.message),
            }
            for warning in caught
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect an SMP encoder and/or preprocessing params. By default this "
            "does not request pretrained weights or preprocessing metadata."
        )
    )
    parser.add_argument("encoder_name", help="SMP encoder name, e.g. resnet34 or tu-resnet18")
    parser.add_argument(
        "--weights",
        default="none",
        help=(
            "Encoder weights for get_encoder. Use 'none' for offline random init "
            "(default), 'true' for tu- pretrained weights, or a native string such as imagenet."
        ),
    )
    parser.add_argument(
        "--pretrained",
        default="imagenet",
        help="Pretrained key for get_preprocessing_params on native encoders (default: imagenet).",
    )
    parser.add_argument("--depth", type=int, default=5, help="Encoder depth for get_encoder (default: 5).")
    parser.add_argument(
        "--output-stride",
        type=int,
        default=32,
        help="Requested encoder output stride for get_encoder (default: 32).",
    )
    parser.add_argument(
        "--in-channels",
        type=int,
        default=3,
        help="Input channel count for get_encoder (default: 3).",
    )
    parser.add_argument(
        "--include-preprocessing",
        action="store_true",
        help="Also query get_preprocessing_params; this may need cached or network-accessible pretrained config.",
    )
    parser.add_argument(
        "--preprocessing-only",
        action="store_true",
        help="Only query preprocessing params; skip encoder construction.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Include get_encoder_names count and a short sample in the JSON output.",
    )
    parser.add_argument(
        "--traceback",
        action="store_true",
        help="Include a traceback string for debugging. Tracebacks may contain local installation paths.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    output: dict[str, Any] = {
        "encoder_name": args.encoder_name,
        "mode": "preprocessing-only" if args.preprocessing_only else "encoder",
    }

    try:
        import segmentation_models_pytorch as smp
    except Exception as error:  # pragma: no cover - depends on caller environment
        output["import"] = {"ok": False, "error": safe_exception(error)}
        if args.traceback:
            output["import"]["traceback"] = traceback.format_exc()
        print(json.dumps(output, indent=2, sort_keys=True))
        return 2

    if args.list:
        try:
            names = smp.encoders.get_encoder_names()
            output["registry"] = {"ok": True, "count": len(names), "sample": names[:25]}
        except Exception as error:
            output["registry"] = {"ok": False, "error": safe_exception(error)}

    exit_code = 0

    if not args.preprocessing_only:
        try:
            output["encoder"] = inspect_encoder(
                smp=smp,
                encoder_name=args.encoder_name,
                weights=parse_weight(args.weights),
                depth=args.depth,
                output_stride=args.output_stride,
                in_channels=args.in_channels,
            )
        except Exception as error:
            output["encoder"] = {"ok": False, "error": safe_exception(error)}
            if args.traceback:
                output["encoder"]["traceback"] = traceback.format_exc()
            exit_code = 1

    if args.preprocessing_only or args.include_preprocessing:
        try:
            output["preprocessing"] = inspect_preprocessing(
                smp=smp,
                encoder_name=args.encoder_name,
                pretrained=args.pretrained,
            )
        except Exception as error:
            output["preprocessing"] = {"ok": False, "error": safe_exception(error)}
            if args.traceback:
                output["preprocessing"]["traceback"] = traceback.format_exc()
            exit_code = 1

    print(json.dumps(output, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
