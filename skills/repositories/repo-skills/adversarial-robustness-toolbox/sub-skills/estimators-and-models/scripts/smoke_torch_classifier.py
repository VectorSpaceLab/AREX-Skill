#!/usr/bin/env python3
"""No-download CPU smoke check for ART PyTorchClassifier."""

from __future__ import annotations

import argparse
import sys

import numpy as np


def run_smoke(skip_fit: bool = False, verbose: bool = False) -> None:
    import torch

    from art.estimators.classification import PyTorchClassifier
    from art.utils import to_categorical

    torch.manual_seed(13)
    np.random.seed(13)

    model = torch.nn.Sequential(
        torch.nn.Linear(4, 6),
        torch.nn.ReLU(),
        torch.nn.Linear(6, 3),
    )
    loss = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.05)

    classifier = PyTorchClassifier(
        model=model,
        loss=loss,
        optimizer=optimizer,
        input_shape=(4,),
        nb_classes=3,
        clip_values=(0.0, 1.0),
        device_type="cpu",
    )

    x = np.array(
        [
            [0.00, 0.10, 0.20, 0.30],
            [0.20, 0.30, 0.40, 0.50],
            [0.50, 0.40, 0.30, 0.20],
            [0.90, 0.80, 0.10, 0.00],
            [0.05, 0.25, 0.75, 0.95],
            [0.60, 0.10, 0.50, 0.40],
        ],
        dtype=np.float32,
    )
    y_index = np.array([0, 1, 2, 2, 1, 0], dtype=np.int64)
    y_one_hot = to_categorical(y_index, nb_classes=3).astype(np.float32)

    if not skip_fit:
        classifier.fit(x, y_one_hot, batch_size=3, nb_epochs=1, verbose=False)

    probe = x[:2]
    pred = classifier.predict(probe)
    assert pred.shape == (len(probe), 3), pred.shape
    assert np.isfinite(pred).all()

    grad = classifier.loss_gradient(probe, y_one_hot[: len(probe)])
    assert grad.shape == probe.shape, grad.shape
    assert np.isfinite(grad).all()

    if verbose:
        print("prediction shape:", pred.shape)
        print("loss_gradient shape:", grad.shape)
    print("OK: PyTorchClassifier predicted and returned finite input-shaped loss gradients on CPU")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-fit", action="store_true", help="Skip the one-epoch tiny fit and only test predict/gradient.")
    parser.add_argument("--verbose", action="store_true", help="Print prediction and gradient shapes in addition to the OK line.")
    args = parser.parse_args(argv)
    run_smoke(skip_fit=args.skip_fit, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - command-line diagnostics
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
