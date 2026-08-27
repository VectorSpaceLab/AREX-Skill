#!/usr/bin/env python3
"""Check a Mask_RCNN runtime environment.

Examples:
  python scripts/check_env.py --show-signatures
  python scripts/check_env.py --build-tiny-graph

The script is read-only by default. `--build-tiny-graph` constructs a tiny
inference graph to catch TensorFlow/Keras compatibility issues, but it does not
load weights, download data, train, or run prediction.
"""

from __future__ import annotations

import argparse
import inspect
import os
import sys
import tempfile


def version_of(dist_name: str) -> str:
    try:
        from importlib.metadata import version  # Python 3.8+
    except Exception:  # pragma: no cover - py37 fallback
        try:
            from importlib_metadata import version  # type: ignore
        except Exception:
            return "unknown"
    try:
        return version(dist_name)
    except Exception:
        return "not-installed"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Mask_RCNN import/API/runtime compatibility.")
    parser.add_argument("--show-signatures", action="store_true", help="Print key public API signatures.")
    parser.add_argument("--build-tiny-graph", action="store_true", help="Build a tiny MaskRCNN inference graph.")
    parser.add_argument("--quiet-tf", action="store_true", help="Suppress most TensorFlow C++ logs before import.")
    args = parser.parse_args()

    if args.quiet_tf:
        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

    print("python", sys.version.split()[0])
    print("mask-rcnn distribution", version_of("mask-rcnn"))
    print("tensorflow distribution", version_of("tensorflow"))
    print("Keras distribution", version_of("Keras"))
    print("keras distribution", version_of("keras"))

    try:
        import tensorflow as tf  # noqa: F401
        import keras  # noqa: F401
        import mrcnn
        from mrcnn.config import Config
        from mrcnn import utils
        from mrcnn import visualize
        from mrcnn import model as modellib
    except Exception as exc:
        print("IMPORT_FAILED", type(exc).__name__, str(exc))
        print("Hint: Mask_RCNN is legacy TensorFlow/Keras code. Prefer TensorFlow 1.15.x + Keras 2.3.x, or treat modern Keras failures as a porting task.")
        return 2

    print("mrcnn import ok")
    print("tensorflow version", getattr(tf, "__version__", "unknown"))
    print("keras version", getattr(keras, "__version__", "unknown"))

    try:
        gpus = getattr(tf.config, "list_physical_devices", lambda *_: [])("GPU")
    except Exception:
        try:
            gpus = ["available"] if tf.test.is_gpu_available() else []
        except Exception:
            gpus = []
    print("gpu devices visible", len(gpus))

    if args.show_signatures:
        targets = [
            Config.__init__,
            Config.display,
            utils.Dataset.__init__,
            utils.Dataset.add_class,
            utils.Dataset.add_image,
            utils.Dataset.prepare,
            utils.Dataset.load_image,
            utils.Dataset.load_mask,
            modellib.MaskRCNN.__init__,
            modellib.MaskRCNN.train,
            modellib.MaskRCNN.detect,
            visualize.display_instances,
        ]
        for obj in targets:
            print(f"{obj.__qualname__} {inspect.signature(obj)}")

    if args.build_tiny_graph:
        class SmokeConfig(Config):
            NAME = "smoke"
            GPU_COUNT = 1
            IMAGES_PER_GPU = 1
            NUM_CLASSES = 2
            IMAGE_MIN_DIM = 128
            IMAGE_MAX_DIM = 128
            BACKBONE = "resnet50"

        try:
            config = SmokeConfig()
            model = modellib.MaskRCNN(
                mode="inference",
                config=config,
                model_dir=tempfile.mkdtemp(prefix="mask-rcnn-smoke-"),
            )
            print("tiny graph built", model.keras_model.name, "inputs", len(model.keras_model.inputs), "outputs", len(model.keras_model.outputs))
        except Exception as exc:
            print("TINY_GRAPH_FAILED", type(exc).__name__, str(exc))
            print("Hint: check TensorFlow/Keras compatibility and ensure image dimensions are divisible by 64.")
            return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
