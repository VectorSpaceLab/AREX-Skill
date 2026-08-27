#!/usr/bin/env python3
"""Flag-gated image-hypermodel smoke checks.

The default check builds only HyperImageAugment in fixed mode. ResNet and
Xception require --allow-heavy. HyperEfficientNet additionally requires
--allow-network because its current Keras Applications call can download
ImageNet weights when the cache is cold. Heavy builds are not time-limited by
this process; wrap them in an external timeout.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys


def _ensure_local_checkout_importable(repo_root=None):
    """Prefer an explicitly requested source checkout over installed code."""
    if repo_root:
        root = Path(repo_root).resolve()
        if not (root / "keras_tuner").is_dir():
            raise ValueError(f"--repo-root has no keras_tuner package: {root}")
        sys.path.insert(0, str(root))
        return
    if importlib.util.find_spec("keras_tuner") is not None:
        return
    for parent in Path(__file__).resolve().parents:
        if (parent / "keras_tuner").is_dir():
            sys.path.insert(0, str(parent))
            return


def _shape(keras):
    if keras.backend.image_data_format() == "channels_first":
        return (3, 32, 32)
    return (32, 32, 3)


def _smoke_augment(keras, HyperParameters, HyperImageAugment):
    shape = _shape(keras)
    hp = HyperParameters()
    hypermodel = HyperImageAugment(
        input_shape=shape,
        rotate=[0.1, 0.2],
        translate_x=0.0,
        translate_y=None,
        contrast=None,
        augment_layers=0,
    )
    model = hypermodel.build(hp)
    expected = (None,) + tuple(shape)
    if tuple(model.output_shape) != expected:
        raise AssertionError(
            f"augmentation output {model.output_shape!r} != {expected!r}"
        )
    if model.name != "image_augment":
        raise AssertionError(f"unexpected augmentation model name: {model.name}")
    if hp.get("factor_rotate") != 0.1:
        raise AssertionError(f"unexpected factor_rotate: {hp.values!r}")
    if "factor_translate_y" in hp.values or "factor_contrast" in hp.values:
        raise AssertionError(f"disabled transforms registered: {hp.values!r}")
    print("PASS HyperImageAugment", hp.values, model.output_shape)


def _smoke_feature_model(keras, HyperParameters, hypermodel, expected_name):
    hp = HyperParameters()
    model = hypermodel.build(hp)
    if model.name != expected_name:
        raise AssertionError(f"unexpected model name: {model.name}")
    if not model.inputs:
        raise AssertionError("model has no inputs")
    print("PASS", expected_name, hp.values, model.output_shape)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        help="Optional source checkout to import instead of an installed package.",
    )
    parser.add_argument(
        "--model",
        choices=("augment", "resnet", "xception", "efficientnet", "all"),
        default="augment",
        help="check to run; default is the network-free augmentation check",
    )
    parser.add_argument(
        "--allow-heavy",
        action="store_true",
        help="permit ResNet/Xception/EfficientNet graph construction",
    )
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="permit an EfficientNet build that may fetch ImageNet weights",
    )
    args = parser.parse_args(argv)

    wants_heavy = args.model != "augment"
    wants_efficientnet = args.model in ("efficientnet", "all")
    if wants_heavy and not args.allow_heavy:
        parser.error("use --allow-heavy for architecture builds")
    if wants_efficientnet and not args.allow_network:
        parser.error(
            "HyperEfficientNet may download ImageNet weights; use "
            "--allow-network only after approving that access"
        )

    _ensure_local_checkout_importable(args.repo_root)
    try:
        from keras_tuner import HyperParameters
        from keras_tuner.applications import (
            HyperEfficientNet,
            HyperImageAugment,
            HyperResNet,
            HyperXception,
        )
        from keras_tuner.backend import config, keras
    except Exception as exc:  # pragma: no cover - environment diagnostic
        print(f"IMPORT FAILED: {exc}", file=sys.stderr)
        return 2

    print(
        "backend=",
        config.backend(),
        "image_data_format=",
        keras.backend.image_data_format(),
        sep="",
    )
    shape = _shape(keras)

    if args.model in ("augment", "all"):
        _smoke_augment(keras, HyperParameters, HyperImageAugment)

    if args.model in ("resnet", "all"):
        _smoke_feature_model(
            keras,
            HyperParameters,
            HyperResNet(input_shape=shape, include_top=False),
            "ResNet",
        )

    if args.model in ("xception", "all"):
        _smoke_feature_model(
            keras,
            HyperParameters,
            HyperXception(input_shape=shape, include_top=False),
            "Xception",
        )

    if args.model in ("efficientnet", "all"):
        print(
            "WARNING: EfficientNet build may download ImageNet weights and is "
            "not bounded by this process; use an external timeout.",
            file=sys.stderr,
        )
        _smoke_feature_model(
            keras,
            HyperParameters,
            HyperEfficientNet(input_shape=shape, classes=2),
            "EfficientNet",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
