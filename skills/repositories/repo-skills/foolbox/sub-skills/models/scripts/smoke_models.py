#!/usr/bin/env python3
"""Run a dependency-light Foolbox model, sample, accuracy, and plot smoke check.

The helper intentionally uses only a toy NumPy callable and Foolbox's bundled
sample assets. It resolves no repository files and does not require PyTorch,
TensorFlow, or JAX. Use ``--plot`` to exercise the lazy Matplotlib path with a
headless backend; an output path can be supplied with ``--plot-output``.
"""

from __future__ import annotations

import argparse
import os
from typing import Any, Optional, Sequence


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser without importing optional runtimes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        choices=("imagenet", "cifar10", "cifar100", "mnist", "fashionMNIST"),
        default="cifar10",
        help="bundled Foolbox dataset name (default: cifar10)",
    )
    parser.add_argument(
        "--batchsize",
        type=int,
        default=4,
        help="number of bundled samples to load (default: 4)",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=32,
        help="square resize used for ImageNet samples (default: 32)",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="also call foolbox.plot.images using Matplotlib's Agg backend",
    )
    parser.add_argument(
        "--plot-output",
        default=None,
        help="optional image path; implies --plot and saves the generated figure",
    )
    return parser


class ToyNumPyModel:
    """Return three deterministic scores from an NHWC image batch."""

    def __call__(self, inputs: Any) -> Any:
        import numpy as np

        values = np.asarray(inputs)
        if values.ndim != 4:
            raise ValueError("expected an image batch with four dimensions")
        mean = values.mean(axis=(1, 2, 3))
        return np.stack((mean, -mean, np.zeros_like(mean)), axis=-1)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Execute the smoke check and return a shell-friendly status code."""
    args = build_parser().parse_args(argv)
    if args.batchsize < 1:
        raise SystemExit("--batchsize must be positive")
    if args.size < 1:
        raise SystemExit("--size must be positive")
    if args.plot_output:
        args.plot = True
    if args.plot:
        # Foolbox imports plotting lazily, so this is early enough for pyplot.
        os.environ.setdefault("MPLBACKEND", "Agg")

    import foolbox as fb

    fmodel = fb.NumPyModel(
        ToyNumPyModel(), bounds=(0, 1), data_format="channels_last"
    )
    images, labels = fb.samples(
        fmodel,
        dataset=args.dataset,
        batchsize=args.batchsize,
        shape=(args.size, args.size),
        data_format="channels_last",
    )
    accuracy = fb.accuracy(fmodel, images, labels)
    logits = fmodel(images)
    print(
        "NumPyModel smoke passed: "
        f"images={images.shape}, labels={labels.shape}, "
        f"logits={logits.shape}, accuracy={accuracy:.3f}"
    )

    if args.plot:
        import foolbox.plot as plot
        import matplotlib.pyplot as plt

        plot.images(
            images,
            n=min(args.batchsize, 4),
            data_format="channels_last",
            bounds=fmodel.bounds,
            ncols=2,
        )
        if args.plot_output:
            parent = os.path.dirname(os.path.abspath(args.plot_output))
            os.makedirs(parent, exist_ok=True)
            plt.savefig(args.plot_output)
            print(f"plot saved: {args.plot_output}")
        plt.close("all")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
