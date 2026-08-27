#!/usr/bin/env python3
"""Check a Segmentation Models Python environment.

This helper performs import/framework/backbone checks and can optionally build a
small offline model with encoder_weights=None. It uses no external data and does
not download pretrained weights unless the caller modifies the defaults.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Segmentation Models import, framework, backbones, and optional tiny model construction.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--framework", choices=("tf.keras", "keras"), default="tf.keras", help="Framework to select before import.")
    parser.add_argument("--build-model", action="store_true", help="Also build a tiny Unet with encoder_weights=None.")
    parser.add_argument("--predict", action="store_true", help="With --build-model, run one zero-valued prediction.")
    parser.add_argument("--backbone", default="resnet18", help="Backbone for the optional tiny model.")
    parser.add_argument("--height", type=int, default=32, help="Tiny model input height.")
    parser.add_argument("--width", type=int, default=32, help="Tiny model input width.")
    parser.add_argument("--channels", type=int, default=3, help="Tiny model input channels.")
    return parser.parse_args()


def fail(message: str, exc: BaseException | None = None) -> int:
    print("ERROR: " + message, file=sys.stderr)
    if exc is not None:
        print(f"Exception: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 2


def import_runtime(framework: str) -> tuple[Any, Any | None]:
    os.environ["SM_FRAMEWORK"] = framework
    try:
        import segmentation_models as sm  # noqa: WPS433 - framework must be selected first
    except Exception as exc:  # pragma: no cover - environment-specific diagnostic path
        raise RuntimeError(
            "Could not import segmentation_models. Install segmentation-models plus a compatible "
            f"{framework} backend, and set SM_FRAMEWORK before import."
        ) from exc

    keras = None
    if framework == "tf.keras":
        try:
            from tensorflow import keras as tf_keras  # noqa: WPS433

            keras = tf_keras
        except Exception:
            keras = None
    elif framework == "keras":
        try:
            import keras as standalone_keras  # noqa: WPS433

            keras = standalone_keras
        except Exception:
            keras = None
    return sm, keras


def build_tiny_model(sm: Any, keras: Any | None, args: argparse.Namespace) -> None:
    if args.height <= 0 or args.width <= 0 or args.channels <= 0:
        raise ValueError("height, width, and channels must be positive")
    model = sm.Unet(
        args.backbone,
        input_shape=(args.height, args.width, args.channels),
        classes=1,
        activation="sigmoid",
        encoder_weights=None,
    )
    print("model_input_shape=", model.input_shape)
    print("model_output_shape=", model.output_shape)
    if args.predict:
        import numpy as np

        pred = model.predict(np.zeros((1, args.height, args.width, args.channels), dtype="float32"), verbose=0)
        print("predict_shape=", tuple(pred.shape))
    if keras is not None:
        keras.backend.clear_session()


def main() -> int:
    args = parse_args()
    try:
        sm, keras = import_runtime(args.framework)
        print("segmentation_models_version=", getattr(sm, "__version__", "unknown"))
        print("segmentation_models_framework=", sm.framework())
        backbones = list(sm.get_available_backbone_names())
        print("backbone_count=", len(backbones))
        print("first_backbones=", ",".join(backbones[:8]))
        if keras is not None:
            print("image_data_format=", keras.backend.image_data_format())
        else:
            print("image_data_format=unavailable")
        if args.build_model:
            build_tiny_model(sm, keras, args)
        print("OK: Segmentation Models environment check passed")
        return 0
    except Exception as exc:  # pragma: no cover - CLI diagnostic path
        return fail("Segmentation Models environment check failed", exc)


if __name__ == "__main__":
    raise SystemExit(main())
