#!/usr/bin/env python3
"""Tiny import/build/save/restore smoke for tf_unet."""

from __future__ import annotations

import argparse
import pathlib
import tempfile

try:
    from importlib.metadata import version as distribution_version
except ImportError:  # Python 3.7 compatibility
    from importlib_metadata import version as distribution_version

import tensorflow as tf

from tf_unet import image_gen, unet, util


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny tf_unet environment smoke.")
    parser.add_argument("--size", type=int, default=32, help="Synthetic image size for the toy generator.")
    parser.add_argument("--border", type=int, default=5, help="Toy-generator border to keep the smoke tiny.")
    parser.add_argument("--layers", type=int, default=1, help="Number of U-Net layers for the smoke graph.")
    parser.add_argument("--features-root", type=int, default=4, help="Initial feature count for the smoke graph.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print(f"tf-unet distribution: {distribution_version('tf-unet')}")
    print(f"tensorflow: {tf.__version__}")

    provider = image_gen.GrayScaleDataProvider(args.size, args.size, cnt=1, border=args.border)
    x_test, y_test = provider(1)
    print(f"provider-shape: {x_test.shape} {y_test.shape}")

    net = unet.Unet(
        channels=provider.channels,
        n_class=provider.n_class,
        layers=args.layers,
        features_root=args.features_root,
        summaries=False,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint = pathlib.Path(tmpdir) / "model.ckpt"
        with tf.Session() as sess:
            sess.run(tf.global_variables_initializer())
            net.save(sess, str(checkpoint))

        prediction = net.predict(str(checkpoint), x_test)
        cropped = util.crop_to_shape(y_test, prediction.shape)
        print(f"prediction-shape: {prediction.shape}")
        print(f"offset: {net.offset}")
        print(f"error-rate: {unet.error_rate(prediction, cropped):.2f}")

    print("tf_unet smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
