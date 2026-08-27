#!/usr/bin/env python3
"""Tiny CPU-only ART PyTorch evasion smoke.

This script uses synthetic data only. It builds a deterministic PyTorchClassifier,
runs FGM or PGD, and asserts shape, clipping, and perturbation-budget invariants.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np

if (Path.cwd() / "art" / "__init__.py").exists():
    sys.path.insert(0, str(Path.cwd()))


def _one_hot(labels: np.ndarray, nb_classes: int) -> np.ndarray:
    encoded = np.zeros((labels.size, nb_classes), dtype=np.float32)
    encoded[np.arange(labels.size), labels] = 1.0
    return encoded


def build_classifier():
    import torch
    from art.estimators.classification import PyTorchClassifier

    torch.manual_seed(1234)

    model = torch.nn.Sequential(torch.nn.Flatten(), torch.nn.Linear(16, 3))
    with torch.no_grad():
        linear = model[1]
        weight_np = np.stack(
            [
                np.linspace(-0.30, 0.30, 16, dtype=np.float32),
                np.linspace(0.25, -0.20, 16, dtype=np.float32),
                np.r_[np.full(8, 0.12, dtype=np.float32), np.full(8, -0.08, dtype=np.float32)],
            ]
        )
        weight = torch.from_numpy(weight_np)
        linear.weight.copy_(weight)
        linear.bias.copy_(torch.tensor([0.02, -0.01, 0.03], dtype=torch.float32))

    loss = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

    return PyTorchClassifier(
        model=model,
        loss=loss,
        optimizer=optimizer,
        input_shape=(1, 4, 4),
        nb_classes=3,
        clip_values=(0.0, 1.0),
        channels_first=True,
        device_type="cpu",
    )


def run_smoke(attack_name: str, targeted: bool) -> dict[str, float | str | bool]:
    from art.attacks.evasion import FastGradientMethod, ProjectedGradientDescent

    np.random.seed(1234)
    classifier = build_classifier()

    x = np.stack(
        [
            np.linspace(0.05, 0.95, 16, dtype=np.float32).reshape(1, 4, 4),
            np.linspace(0.95, 0.05, 16, dtype=np.float32).reshape(1, 4, 4),
        ],
        axis=0,
    )
    source_labels = np.array([0, 1], dtype=np.int64)
    target_labels = (source_labels + 1) % 3
    y = _one_hot(target_labels if targeted else source_labels, 3)

    eps = 0.20
    if attack_name == "fgm":
        attack = FastGradientMethod(
            classifier,
            eps=eps,
            eps_step=eps,
            targeted=targeted,
            batch_size=2,
            summary_writer=False,
        )
    else:
        attack = ProjectedGradientDescent(
            classifier,
            eps=eps,
            eps_step=0.10,
            max_iter=3,
            targeted=targeted,
            batch_size=2,
            num_random_init=0,
            summary_writer=False,
            verbose=False,
        )

    before = np.argmax(classifier.predict(x), axis=1)
    x_adv = attack.generate(x=x, y=y)
    after = np.argmax(classifier.predict(x_adv), axis=1)

    assert x_adv.shape == x.shape, (x_adv.shape, x.shape)
    assert np.isfinite(x_adv).all()
    assert float(x_adv.min()) >= -1e-6
    assert float(x_adv.max()) <= 1.0 + 1e-6

    linf = float(np.max(np.abs(x_adv - x)))
    mean_abs = float(np.mean(np.abs(x_adv - x)))
    assert linf <= eps + 1e-5, linf
    assert mean_abs > 0.0, "attack produced no perturbation"

    return {
        "attack": attack_name,
        "targeted": targeted,
        "linf": linf,
        "mean_abs": mean_abs,
        "pred_before": ",".join(map(str, before.tolist())),
        "pred_after": ",".join(map(str, after.tolist())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a tiny CPU PyTorch ART evasion smoke on synthetic data.")
    parser.add_argument("--attack", choices=["pgd", "fgm"], default="pgd", help="Attack to run; default: pgd.")
    parser.add_argument(
        "--targeted",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run targeted attack with one-hot target labels; default: true.",
    )
    args = parser.parse_args()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        result = run_smoke(args.attack, args.targeted)

    print("ART PyTorch evasion smoke passed")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
