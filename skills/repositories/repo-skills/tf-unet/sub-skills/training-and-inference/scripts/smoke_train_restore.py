#!/usr/bin/env python3
"""Run a tiny tf_unet training, checkpoint, and restore smoke."""

from __future__ import annotations

import argparse
import pathlib
import tempfile

import numpy as np

from tf_unet import unet, util
from tf_unet.image_util import SimpleDataProvider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny tf_unet train/save/restore smoke.")
    parser.add_argument("--size", type=int, default=32, help="Synthetic image size for the smoke dataset.")
    parser.add_argument("--layers", type=int, default=1, help="Number of U-Net layers for the smoke graph.")
    parser.add_argument("--features-root", type=int, default=4, help="Initial feature count for the smoke graph.")
    parser.add_argument("--epochs", type=int, default=1, help="Number of training epochs for the smoke run.")
    parser.add_argument("--training-iters", type=int, default=1, help="Number of iterations per epoch.")
    parser.add_argument("--dropout", type=float, default=1.0, help="Dropout keep probability for the smoke run.")
    return parser.parse_args()


def make_provider(size: int) -> SimpleDataProvider:
    grid = np.linspace(0.0, 1.0, size, dtype=np.float32)
    base_a = np.outer(grid, grid).astype(np.float32)
    base_b = np.outer(grid[::-1], grid).astype(np.float32)
    data = np.stack([base_a, base_b], axis=0)[..., np.newaxis]

    labels = np.zeros((2, size, size, 3), dtype=np.float32)

    mask_a = np.zeros((size, size), dtype=bool)
    mask_a[size // 4 : size // 2, size // 4 : size // 2] = True
    labels[0, ..., 0] = (~mask_a).astype(np.float32)
    labels[0, ..., 1] = mask_a.astype(np.float32)

    mask_b = np.zeros((size, size), dtype=bool)
    mask_b[size // 3 : (2 * size) // 3, size // 3 : (2 * size) // 3] = True
    labels[1, ..., 0] = (~mask_b).astype(np.float32)
    labels[1, ..., 2] = mask_b.astype(np.float32)

    return SimpleDataProvider(data, labels)


def main() -> int:
    args = parse_args()
    provider = make_provider(args.size)

    print(f"provider-channels: {provider.channels}")
    print(f"provider-classes: {provider.n_class}")

    net = unet.Unet(
        channels=provider.channels,
        n_class=provider.n_class,
        layers=args.layers,
        features_root=args.features_root,
        summaries=False,
    )
    trainer = unet.Trainer(
        net,
        batch_size=1,
        verification_batch_size=1,
        optimizer="adam",
        opt_kwargs=dict(learning_rate=0.001),
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = pathlib.Path(tmpdir)
        output_dir = root / "output"
        prediction_dir = root / "prediction"
        checkpoint = trainer.train(
            provider,
            str(output_dir),
            training_iters=args.training_iters,
            epochs=args.epochs,
            dropout=args.dropout,
            display_step=1,
            restore=False,
            prediction_path=str(prediction_dir),
        )

        x_test, y_test = provider(1)
        prediction = net.predict(checkpoint, x_test)
        error = unet.error_rate(prediction, util.crop_to_shape(y_test, prediction.shape))

        print(f"checkpoint: {checkpoint}")
        print(f"prediction-shape: {prediction.shape}")
        print(f"error-rate: {error:.2f}")

    print("tf_unet training smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
