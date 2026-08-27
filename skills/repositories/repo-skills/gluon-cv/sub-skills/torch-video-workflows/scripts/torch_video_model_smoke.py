#!/usr/bin/env python3
"""Smoke-check GluonCV Torch video model-zoo configs.

This skill-owned helper uses only the installed `gluoncv` package. It does not
read source checkout files, datasets, checkpoints, or model-zoo weights unless
`--pretrained` or `--pretrained-base` is explicitly requested.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a GluonCV Torch action-recognition config and optionally "
            "run a synthetic [N, C, T, H, W] forward pass."
        )
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List registered gluoncv.torch model-zoo names and exit.",
    )
    parser.add_argument(
        "--model",
        default="resnet18_v1b_kinetics400",
        help="Torch model-zoo registry name.",
    )
    parser.add_argument(
        "--classes",
        type=positive_int,
        default=400,
        help="Value for cfg.CONFIG.DATA.NUM_CLASSES.",
    )
    parser.add_argument(
        "--batch-size",
        type=positive_int,
        default=1,
        help="Synthetic batch size N.",
    )
    parser.add_argument(
        "--channels",
        type=positive_int,
        default=3,
        help="Synthetic channel count C; use 3 for RGB video.",
    )
    parser.add_argument(
        "--frames",
        type=positive_int,
        default=1,
        help="Synthetic time dimension T.",
    )
    parser.add_argument(
        "--height",
        type=positive_int,
        default=224,
        help="Synthetic input height.",
    )
    parser.add_argument(
        "--width",
        type=positive_int,
        default=224,
        help="Synthetic input width.",
    )
    parser.add_argument(
        "--num-segment",
        type=positive_int,
        default=1,
        help="Value for cfg.CONFIG.DATA.NUM_SEGMENT when present.",
    )
    parser.add_argument(
        "--num-crop",
        type=positive_int,
        default=1,
        help="Value for cfg.CONFIG.DATA.NUM_CROP when present.",
    )
    parser.add_argument(
        "--pretrained",
        action="store_true",
        help="Set cfg.CONFIG.MODEL.PRETRAINED=True; may require cached/downloaded weights.",
    )
    parser.add_argument(
        "--pretrained-base",
        action="store_true",
        help=(
            "Set cfg.CONFIG.MODEL.PRETRAINED_BASE=True. This may download "
            "backbone weights, but some I3D builders require it for inflation."
        ),
    )
    parser.add_argument(
        "--feature-output",
        action="store_true",
        help="Set cfg.CONFIG.INFERENCE.FEAT=True when the config supports it.",
    )
    parser.add_argument(
        "--cuda",
        action="store_true",
        help="Run on CUDA only if the installed Torch build reports CUDA available.",
    )
    parser.add_argument(
        "--no-forward",
        action="store_true",
        help="Instantiate the model and print config facts without running the tensor forward.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Torch random seed for the synthetic tensor.",
    )
    return parser.parse_args()


def import_runtime() -> tuple[Any, Any, Any]:
    try:
        import torch
        from gluoncv.torch.engine.config import get_cfg_defaults
        from gluoncv.torch.model_zoo import get_model, get_model_list
    except Exception as exc:  # pragma: no cover - diagnostic branch
        message = str(exc)
        print("Failed to import GluonCV Torch runtime.", file=sys.stderr)
        print(f"Original error: {type(exc).__name__}: {message}", file=sys.stderr)
        if "Image.LINEAR" in message or "LINEAR" in message:
            print("Hint: this legacy stack expects Pillow<10.", file=sys.stderr)
        if "torchvision" in message:
            print("Hint: install a torchvision build matching the installed torch version.", file=sys.stderr)
        if "torch" in message.lower() or "pytorch" in message.lower():
            print("Hint: GluonCV's guard expects torch >=1.4,<2.0.", file=sys.stderr)
        raise SystemExit(2) from exc
    return torch, (get_cfg_defaults, get_model), get_model_list


def shape_summary(value: Any) -> Any:
    if hasattr(value, "shape"):
        return tuple(value.shape)
    if isinstance(value, (list, tuple)):
        return [shape_summary(item) for item in value]
    if isinstance(value, dict):
        return {key: shape_summary(item) for key, item in value.items()}
    return type(value).__name__


def main() -> int:
    args = parse_args()
    torch, model_api, get_model_list = import_runtime()
    get_cfg_defaults, get_model = model_api

    names = list(get_model_list())
    if args.list_models:
        print(f"torch_model_count={len(names)}")
        for name in sorted(names):
            print(name)
        return 0

    model_name = args.model.lower()
    if model_name not in {name.lower() for name in names}:
        print(f"Unknown model: {args.model}", file=sys.stderr)
        print("Run with --list-models to see valid registry names.", file=sys.stderr)
        return 2

    if "coot" in model_name or "directpose" in model_name:
        print(
            "This helper is for action-recognition video classifiers with "
            "[N, C, T, H, W] input. Use --no-forward only for non-video registry "
            "instantiation, and consult the references for COOT/DirectPose contracts.",
            file=sys.stderr,
        )
        if not args.no_forward:
            return 2

    cfg = get_cfg_defaults(name="action_recognition")
    cfg.CONFIG.MODEL.NAME = args.model
    cfg.CONFIG.MODEL.PRETRAINED = bool(args.pretrained)
    cfg.CONFIG.MODEL.PRETRAINED_BASE = bool(args.pretrained_base)
    cfg.CONFIG.DATA.NUM_CLASSES = int(args.classes)
    cfg.CONFIG.DATA.CLIP_LEN = int(args.frames)
    cfg.CONFIG.DATA.NUM_SEGMENT = int(args.num_segment)
    cfg.CONFIG.DATA.NUM_CROP = int(args.num_crop)
    if hasattr(cfg.CONFIG, "INFERENCE") and hasattr(cfg.CONFIG.INFERENCE, "FEAT"):
        cfg.CONFIG.INFERENCE.FEAT = bool(args.feature_output)

    if args.pretrained:
        print("warning=pretrained model-zoo weights may require network or cache", file=sys.stderr)
    if args.pretrained_base:
        print("warning=pretrained base weights may require network or cache", file=sys.stderr)

    torch.manual_seed(args.seed)
    device = torch.device("cpu")
    if args.cuda:
        if not torch.cuda.is_available():
            print("CUDA was requested, but torch.cuda.is_available() is False.", file=sys.stderr)
            return 2
        device = torch.device("cuda")

    model = get_model(cfg).eval().to(device)

    print(f"torch_model_count={len(names)}")
    print(f"model={args.model}")
    print(f"device={device}")
    print(f"pretrained={cfg.CONFIG.MODEL.PRETRAINED}")
    print(f"pretrained_base={cfg.CONFIG.MODEL.PRETRAINED_BASE}")
    print(f"num_classes={cfg.CONFIG.DATA.NUM_CLASSES}")
    print(f"clip_len={cfg.CONFIG.DATA.CLIP_LEN}")

    if args.no_forward:
        print("forward=skipped")
        return 0

    input_shape = (args.batch_size, args.channels, args.frames, args.height, args.width)
    x = torch.rand(input_shape, device=device)
    with torch.no_grad():
        output = model(x)
    print(f"input_shape={tuple(x.shape)}")
    print(f"output_shape={shape_summary(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
