#!/usr/bin/env python3
"""Tiny Fairlearn PyTorch adversarial mitigation smoke check."""

from __future__ import annotations

import argparse
import sys

import numpy as np

try:
    import torch
except Exception as exc:  # pragma: no cover - exercised only when torch missing
    print(f"PyTorch is required for this smoke script: {exc}", file=sys.stderr)
    raise SystemExit(2)

from fairlearn.adversarial import AdversarialFairnessClassifier
from fairlearn.metrics import MetricFrame, selection_rate
from sklearn.metrics import accuracy_score


class Predictor(torch.nn.Module):
    def __init__(self, n_features: int):
        super().__init__()
        self.layers = torch.nn.Sequential(
            torch.nn.Linear(n_features, 8),
            torch.nn.ReLU(),
            torch.nn.Linear(8, 1),
            torch.nn.Sigmoid(),
        )

    def forward(self, x):
        return self.layers(x)


class Adversary(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = torch.nn.Sequential(
            torch.nn.Linear(1, 4),
            torch.nn.ReLU(),
            torch.nn.Linear(4, 1),
            torch.nn.Sigmoid(),
        )

    def forward(self, x):
        return self.layers(x)


def make_fixture(n_samples: int = 40):
    rng = np.random.default_rng(0)
    sensitive = rng.integers(0, 2, size=n_samples)
    x0 = rng.normal(loc=sensitive * 0.8, scale=0.8, size=n_samples)
    x1 = rng.normal(size=n_samples)
    logits = x0 + 0.4 * x1 - 0.1
    y = (logits > np.median(logits)).astype(int)
    X = np.column_stack([x0, x1]).astype("float32")
    return X, y, sensitive


def run_once(device: str | None, epochs: int) -> None:
    if device:
        if not torch.cuda.is_available():
            raise RuntimeError(f"CUDA device {device!r} requested but torch.cuda.is_available() is False")
        print(f"Running PyTorch adversarial smoke on {device}")
    else:
        print("Running PyTorch adversarial smoke on CPU")

    X, y, sensitive = make_fixture()
    mitigator = AdversarialFairnessClassifier(
        backend="torch",
        predictor_model=Predictor(X.shape[1]),
        adversary_model=Adversary(),
        predictor_optimizer="Adam",
        adversary_optimizer="Adam",
        constraints="demographic_parity",
        # Keep the smoke conservative so CPU and CUDA runs avoid NaNs in BCELoss.
        learning_rate=0.001,
        alpha=0.1,
        epochs=epochs,
        batch_size=len(y),
        shuffle=True,
        random_state=0,
        cuda=device,
    )
    mitigator.fit(X, y, sensitive_features=sensitive)
    pred = mitigator.predict(X)
    if len(pred) != len(y):
        raise AssertionError("Adversarial predictions must preserve sample count")
    mf = MetricFrame(
        metrics={"accuracy": accuracy_score, "selection_rate": selection_rate},
        y_true=y,
        y_pred=pred,
        sensitive_features=sensitive,
    )
    print("Overall metrics:\n", mf.overall)
    print("By-group metrics:\n", mf.by_group)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=1, help="Training epochs for the tiny smoke.")
    parser.add_argument("--cuda", default=None, help="Optional CUDA device string such as cuda:0.")
    args = parser.parse_args()
    run_once(args.cuda, args.epochs)
    print("PyTorch adversarial smoke check completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
