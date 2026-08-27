#!/usr/bin/env python3
"""Inspect Mask_RCNN API signatures and optional tiny graph build.

This helper does not require the original repository checkout. It imports the
installed `mrcnn` package and reports actionable compatibility signals.
"""

from __future__ import annotations

import argparse
import inspect
import os
import sys
import tempfile


def _version(dist: str) -> str:
    try:
        from importlib.metadata import version
    except Exception:
        try:
            from importlib_metadata import version  # type: ignore
        except Exception:
            return "unknown"
    try:
        return version(dist)
    except Exception:
        return "not-installed"


def main() -> int:
    ap = argparse.ArgumentParser(description="Inspect installed Mask_RCNN APIs.")
    ap.add_argument("--show-signatures", action="store_true", help="Print key API signatures.")
    ap.add_argument("--build-tiny-graph", action="store_true", help="Build a minimal inference graph.")
    args = ap.parse_args()

    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "1")
    print("python", sys.version.split()[0])
    print("mask-rcnn", _version("mask-rcnn"))
    print("tensorflow", _version("tensorflow"))
    print("Keras", _version("Keras"))
    print("keras", _version("keras"))

    try:
        import tensorflow as tf
        import keras
        from mrcnn.config import Config
        from mrcnn import utils, visualize
        from mrcnn import model as modellib
    except Exception as exc:
        print("FAIL import", type(exc).__name__, str(exc))
        print("Use a TensorFlow 1.15 + Keras 2.3 style stack, or route this as a modernization task.")
        return 2

    print("OK import")
    print("tf_version", getattr(tf, "__version__", "unknown"))
    print("keras_version", getattr(keras, "__version__", "unknown"))

    if args.show_signatures:
        for obj in [
            Config.__init__, Config.display,
            utils.Dataset.__init__, utils.Dataset.add_class, utils.Dataset.add_image,
            utils.Dataset.prepare, utils.Dataset.load_image, utils.Dataset.load_mask,
            modellib.MaskRCNN.__init__, modellib.MaskRCNN.load_weights,
            modellib.MaskRCNN.find_last, modellib.MaskRCNN.train, modellib.MaskRCNN.detect,
            visualize.display_instances, visualize.draw_boxes, visualize.display_top_masks,
        ]:
            print(f"{obj.__qualname__} {inspect.signature(obj)}")

    if args.build_tiny_graph:
        class TinyConfig(Config):
            NAME = "tiny"
            GPU_COUNT = 1
            IMAGES_PER_GPU = 1
            NUM_CLASSES = 2
            IMAGE_MIN_DIM = 128
            IMAGE_MAX_DIM = 128
            BACKBONE = "resnet50"

        try:
            config = TinyConfig()
            model = modellib.MaskRCNN(
                mode="inference",
                config=config,
                model_dir=tempfile.mkdtemp(prefix="mask-rcnn-api-check-"),
            )
        except Exception as exc:
            print("FAIL tiny_graph", type(exc).__name__, str(exc))
            return 3
        print("OK tiny_graph", model.keras_model.name, len(model.keras_model.inputs), len(model.keras_model.outputs))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
