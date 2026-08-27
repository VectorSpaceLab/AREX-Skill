#!/usr/bin/env python3
"""Tiny no-download ART PyTorch adversarial-accuracy smoke.

Builds a deterministic CPU PyTorchClassifier on synthetic 1x2x2 image-like
inputs, creates bounded FGM or PGD adversarial examples, and reports benign and
adversarial accuracy. This is a workflow sanity check, not a benchmark.

Examples:
    python smoke_pytorch_adv_accuracy.py --help
    python smoke_pytorch_adv_accuracy.py --attack fgm --json
    python smoke_pytorch_adv_accuracy.py --attack pgd --max-iter 3 --json
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import torch

from art.attacks.evasion import FastGradientMethod, ProjectedGradientDescent
from art.estimators.classification import PyTorchClassifier
from art.metrics import adversarial_accuracy


class TinyImageClassifier(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.flatten = torch.nn.Flatten()
        self.linear = torch.nn.Linear(4, 2)
        with torch.no_grad():
            self.linear.weight[:] = torch.tensor(
                [[-1.0, -1.0, -1.0, -1.0], [1.0, 1.0, 1.0, 1.0]], dtype=torch.float32
            )
            self.linear.bias[:] = torch.tensor([1.5, -1.5], dtype=torch.float32)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(self.flatten(x))


def build_fixture() -> tuple[np.ndarray, np.ndarray]:
    # Samples start just below/above the deterministic model's decision boundary
    # at sum(x)=1.5, so a small bounded attack can change adversarial accuracy.
    x = np.array(
        [
            [[[0.30, 0.30], [0.30, 0.20]]],
            [[[0.25, 0.35], [0.30, 0.25]]],
            [[[0.20, 0.30], [0.35, 0.25]]],
            [[[0.35, 0.20], [0.30, 0.25]]],
            [[[0.45, 0.45], [0.45, 0.35]]],
            [[[0.50, 0.40], [0.45, 0.35]]],
            [[[0.40, 0.45], [0.50, 0.35]]],
            [[[0.45, 0.40], [0.35, 0.50]]],
        ],
        dtype=np.float32,
    )
    y_index = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    y = np.eye(2, dtype=np.float32)[y_index]
    return x, y


def make_classifier() -> PyTorchClassifier:
    model = TinyImageClassifier()
    return PyTorchClassifier(
        model=model,
        loss=torch.nn.CrossEntropyLoss(),
        optimizer=torch.optim.SGD(model.parameters(), lr=0.01),
        input_shape=(1, 2, 2),
        nb_classes=2,
        clip_values=(0.0, 1.0),
        channels_first=True,
        device_type="cpu",
    )


def make_attack(classifier: PyTorchClassifier, args: argparse.Namespace):
    if args.attack == "fgm":
        return FastGradientMethod(estimator=classifier, eps=args.eps, eps_step=args.eps, batch_size=4)
    return ProjectedGradientDescent(
        estimator=classifier,
        eps=args.eps,
        eps_step=args.eps_step,
        max_iter=args.max_iter,
        batch_size=4,
        num_random_init=0,
        verbose=False,
    )


def accuracy(classifier: PyTorchClassifier, x: np.ndarray, y: np.ndarray) -> float:
    pred = classifier.predict(x)
    return float(np.mean(np.argmax(pred, axis=1) == np.argmax(y, axis=1)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a tiny CPU ART PyTorch adversarial-accuracy smoke.")
    parser.add_argument("--attack", choices=["fgm", "pgd"], default="fgm", help="Attack to use for the tiny smoke.")
    parser.add_argument("--eps", type=float, default=0.2, help="L-infinity perturbation budget in [0, 1] input scale.")
    parser.add_argument("--eps-step", type=float, default=0.05, help="PGD step size in [0, 1] input scale.")
    parser.add_argument("--max-iter", type=int, default=3, help="PGD iterations for --attack pgd.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    torch.manual_seed(0)
    np.random.seed(0)
    classifier = make_classifier()
    x, y = build_fixture()
    attack = make_attack(classifier, args)
    x_adv = attack.generate(x=x, y=y)

    if x_adv.shape != x.shape:
        raise SystemExit(f"adversarial shape mismatch: {x_adv.shape} != {x.shape}")
    if not np.isfinite(x_adv).all():
        raise SystemExit("adversarial examples contain non-finite values")
    linf = float(np.max(np.abs(x_adv - x)))
    if linf > args.eps + 1e-5:
        raise SystemExit(f"perturbation exceeded eps: {linf} > {args.eps}")

    benign_acc = accuracy(classifier, x, y)
    adv_acc_manual = accuracy(classifier, x_adv, y)
    adv_acc_metric = float(adversarial_accuracy(classifier=classifier, x=x, y=y, attack_crafter=attack))
    result = {
        "tool": "smoke_pytorch_adv_accuracy",
        "attack": args.attack,
        "eps": args.eps,
        "eps_step": args.eps_step if args.attack == "pgd" else args.eps,
        "max_iter": args.max_iter if args.attack == "pgd" else 1,
        "benign_accuracy": benign_acc,
        "adversarial_accuracy_manual": adv_acc_manual,
        "adversarial_accuracy_metric": adv_acc_metric,
        "linf": linf,
        "shape": list(x.shape),
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("ART PyTorch adversarial-accuracy smoke passed")
        for key, value in result.items():
            if key != "tool":
                print(f"{key}: {value}")


if __name__ == "__main__":
    main()
