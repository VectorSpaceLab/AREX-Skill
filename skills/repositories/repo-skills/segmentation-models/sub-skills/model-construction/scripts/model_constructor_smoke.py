#!/usr/bin/env python3
"""Safe Segmentation Models constructor smoke check.

Defaults are intentionally offline-friendly: encoder_weights=None and no
prediction. Pass --predict to run a single zero-batch forward pass.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict


ARCHITECTURES = {
    "unet": "Unet",
    "linknet": "Linknet",
    "fpn": "FPN",
    "pspnet": "PSPNet",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Segmentation Models Keras model with safe offline defaults.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--architecture",
        default="Unet",
        choices=["Unet", "Linknet", "FPN", "PSPNet", "unet", "linknet", "fpn", "pspnet"],
        help="Model architecture/constructor to exercise.",
    )
    parser.add_argument("--backbone", default="vgg16", help="Backbone name, e.g. resnet18, resnet34, vgg16, mobilenetv2.")
    parser.add_argument("--height", type=int, default=64, help="Input image height.")
    parser.add_argument("--width", type=int, default=64, help="Input image width.")
    parser.add_argument("--channels", type=int, default=3, help="Input channels for channels_last input shape.")
    parser.add_argument("--classes", type=int, default=1, help="Output mask channels/classes.")
    parser.add_argument("--activation", default="sigmoid", help="Final activation, e.g. sigmoid, softmax, linear.")
    parser.add_argument(
        "--framework",
        default="tf.keras",
        choices=["tf.keras", "keras"],
        help="Segmentation Models framework selected before import.",
    )
    parser.add_argument(
        "--encoder-weights",
        default="none",
        choices=["none", "imagenet"],
        help="Encoder initialization. 'imagenet' may use network/cache and expects RGB-compatible input.",
    )
    parser.add_argument(
        "--weights",
        default=None,
        help="Optional path to full segmentation-model weights. Leave unset for construction smoke tests.",
    )
    parser.add_argument(
        "--encoder-freeze",
        action="store_true",
        help="Set encoder/backbone layers non-trainable at construction time.",
    )
    parser.add_argument(
        "--downsample-factor",
        type=int,
        default=8,
        choices=[4, 8, 16],
        help="PSPNet downsample factor; ignored for other architectures.",
    )
    parser.add_argument(
        "--predict",
        action="store_true",
        help="Run one zero-valued batch through model.predict after construction.",
    )
    parser.add_argument(
        "--show-traceback",
        action="store_true",
        help="Print a full traceback for unexpected errors.",
    )
    return parser.parse_args()


def fail(message: str, exc: BaseException | None = None, show_traceback: bool = False) -> int:
    print("ERROR: " + message, file=sys.stderr)
    if exc is not None:
        print(f"Exception: {type(exc).__name__}: {exc}", file=sys.stderr)
    if show_traceback and exc is not None:
        import traceback

        traceback.print_exception(type(exc), exc, exc.__traceback__)
    return 2


def recovery_hint(exc: BaseException) -> str:
    text = str(exc)
    lower = text.lower()
    if "wrong shape" in lower or "input shape" in lower and "psp" in lower:
        return "PSPNet requires concrete H/W divisible by 6 * downsample_factor; try --height 96 --width 96 for --downsample-factor 8."
    if "unsupported factor" in lower:
        return "PSPNet downsample_factor must be 4, 8, or 16."
    if "unsupported pooling type" in lower:
        return "PSPNet pooling type must be avg or max."
    if "decoder block type" in lower:
        return "Unet/Linknet decoder_block_type must be upsampling or transpose."
    if "aggregation parameter" in lower:
        return "FPN pyramid_aggregation must be sum or concat."
    if "unknown" in lower and "model" in lower or "not exist" in lower or "no such" in lower:
        return "Check the backbone name; use exact lowercase names such as resnet18, resnet34, vgg16, mobilenetv2, efficientnetb0."
    if "download" in lower or "url" in lower or "http" in lower:
        return "Avoid network by using --encoder-weights none, or pre-cache ImageNet weights before using --encoder-weights imagenet."
    if "channel" in lower and "3" in lower:
        return "ImageNet encoder weights are RGB-oriented; use --encoder-weights none for non-3-channel inputs or map channels to 3 externally."
    if "tensorflow" in lower or "keras" in lower or "efficientnet" in lower or "classification" in lower:
        return "Install a compatible TensorFlow/Keras backend and set --framework before import; modern environments usually use --framework tf.keras."
    return "Check framework selection, backbone spelling, input shape divisibility, encoder_weights, and constructor-specific options."


def validate_args(args: argparse.Namespace) -> None:
    if args.height <= 0 or args.width <= 0 or args.channels <= 0:
        raise ValueError("--height, --width, and --channels must be positive integers.")
    if args.classes <= 0:
        raise ValueError("--classes must be a positive integer.")
    if args.encoder_weights == "imagenet" and args.channels != 3:
        raise ValueError("--encoder-weights imagenet expects 3 input channels; use --encoder-weights none for non-RGB smoke tests.")


def import_segmentation_models(framework: str):
    os.environ["SM_FRAMEWORK"] = framework
    try:
        import segmentation_models as sm  # noqa: WPS433 - framework must be selected first
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Could not import segmentation_models after setting SM_FRAMEWORK="
            f"{framework!r}. Install segmentation-models and the requested Keras/TensorFlow backend."
        ) from exc
    return sm


def build_model(sm: Any, args: argparse.Namespace):
    arch_key = args.architecture.lower()
    ctor_name = ARCHITECTURES[arch_key]
    constructor = getattr(sm, ctor_name)
    encoder_weights = None if args.encoder_weights == "none" else args.encoder_weights
    kwargs: Dict[str, Any] = {
        "backbone_name": args.backbone,
        "input_shape": (args.height, args.width, args.channels),
        "classes": args.classes,
        "activation": args.activation,
        "weights": args.weights,
        "encoder_weights": encoder_weights,
        "encoder_freeze": args.encoder_freeze,
    }
    if ctor_name == "PSPNet":
        kwargs["downsample_factor"] = args.downsample_factor
    return constructor(**kwargs)


def main() -> int:
    args = parse_args()
    try:
        validate_args(args)
        sm = import_segmentation_models(args.framework)
        model = build_model(sm, args)
        print("OK: constructed Segmentation Models model")
        print(f"  framework: {sm.framework()}")
        print(f"  architecture: {ARCHITECTURES[args.architecture.lower()]}")
        print(f"  backbone: {args.backbone}")
        print(f"  input_shape: {model.input_shape}")
        print(f"  output_shape: {model.output_shape}")
        print(f"  encoder_weights: {args.encoder_weights}")
        if args.predict:
            import numpy as np

            x = np.zeros((1, args.height, args.width, args.channels), dtype="float32")
            y = model.predict(x, verbose=0)
            print(f"OK: predict output shape: {tuple(y.shape)}")
        return 0
    except Exception as exc:  # pragma: no cover - CLI diagnostics
        hint = recovery_hint(exc)
        return fail(f"model construction smoke check failed. Hint: {hint}", exc, args.show_traceback)


if __name__ == "__main__":
    raise SystemExit(main())
