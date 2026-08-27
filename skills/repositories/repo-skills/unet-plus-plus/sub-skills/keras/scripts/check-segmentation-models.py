#!/usr/bin/env python3
"""Safe Keras segmentation-model smoke.

This helper builds tiny Unet/Nestnet/Xnet/FPN/PSPNet models with
encoder_weights=None so it can verify the legacy stack without downloading
pretrained weights or training on real data.
"""

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the legacy Keras segmentation-models runtime")
    parser.add_argument(
        "--backbone",
        default="vgg16",
        help="Backbone name to use for the smoke models.",
    )
    args = parser.parse_args()

    import keras  # type: ignore
    import tensorflow as tf  # type: ignore
    from segmentation_models import Unet, Nestnet, Xnet, FPN, PSPNet  # type: ignore

    print(f"keras={keras.__version__}")
    print(f"tensorflow={tf.__version__}")

    builders = [
        ("Unet", Unet, (64, 64, 3)),
        ("Nestnet", Nestnet, (64, 64, 3)),
        ("Xnet", Xnet, (64, 64, 3)),
        ("FPN", FPN, (64, 64, 3)),
        ("PSPNet", PSPNet, (48, 48, 3)),
    ]

    for name, builder, shape in builders:
        model = builder(
            backbone_name=args.backbone,
            encoder_weights=None,
            classes=1,
            activation="sigmoid",
            input_shape=shape,
        )
        print(f"{name}: {model.name} -> {model.output_shape}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
