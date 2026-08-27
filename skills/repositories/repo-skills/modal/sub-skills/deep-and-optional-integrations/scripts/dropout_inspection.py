#!/usr/bin/env python3
"""CPU-only inspection helper for modAL.dropout optional dependencies.

This script intentionally performs no training, downloads, credential access, or
file writes. It imports torch, skorch, and modAL.dropout from the active Python
environment, builds a tiny in-memory PyTorch module, demonstrates modAL's
set_dropout_mode layer-index behavior, and prints PASS on success.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, List


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect optional torch/skorch/modAL.dropout imports and dropout "
            "layer indexes without training or downloading data."
        )
    )
    parser.add_argument(
        "--list-layers",
        action="store_true",
        help="Print the tiny demonstration model's module indexes and class names.",
    )
    parser.add_argument(
        "--layer-index",
        action="append",
        type=int,
        default=[],
        help=(
            "Dropout module index to toggle in the demonstration model. "
            "May be supplied more than once. If omitted, all dropout layers are toggled."
        ),
    )
    parser.add_argument(
        "--demo-bad-index",
        action="store_true",
        help="Demonstrate and recover from the expected KeyError for a non-dropout layer index.",
    )
    return parser.parse_args(list(argv))


def import_optional_stack():
    try:
        import torch
        from torch import nn
        from skorch import NeuralNetClassifier
        import modAL.dropout as modal_dropout
    except Exception as exc:  # pragma: no cover - exercised by missing optional deps
        print(
            "FAIL optional import: torch, skorch, and modAL.dropout must be "
            f"available in the active Python environment ({type(exc).__name__}: {exc})",
            file=sys.stderr,
        )
        return None
    return torch, nn, NeuralNetClassifier, modal_dropout


def main(argv: Iterable[str] = ()) -> int:
    args = parse_args(argv)
    imported = import_optional_stack()
    if imported is None:
        return 1

    torch, nn, NeuralNetClassifier, modal_dropout = imported
    torch.set_num_threads(1)

    class TinyDropoutNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.features = nn.Sequential(
                nn.Linear(4, 6),
                nn.ReLU(),
                nn.Dropout(0.25),
            )
            self.head = nn.Sequential(
                nn.Linear(6, 3),
                nn.Dropout(0.5),
                nn.Linear(3, 2),
            )

        def forward(self, x):
            return self.head(self.features(x))

    model = TinyDropoutNet()
    modules = list(model.modules())
    dropout_indexes: List[int] = [
        idx for idx, module in enumerate(modules)
        if module.__class__.__name__.startswith("Dropout")
    ]

    # Instantiate the expected skorch wrapper shape without initialize(), fit(),
    # data allocation beyond the model class reference, or training.
    skorch_net = NeuralNetClassifier(
        TinyDropoutNet,
        max_epochs=1,
        train_split=None,
        verbose=0,
        device="cpu",
    )

    if args.list_layers:
        print("Demonstration module indexes:")
        for idx, module in enumerate(modules):
            marker = "  <-- dropout" if idx in dropout_indexes else ""
            print(f"  {idx}: {module.__class__.__name__}{marker}")

    if not dropout_indexes:
        print("FAIL demonstration model unexpectedly has no dropout layers", file=sys.stderr)
        return 2

    try:
        modal_dropout.set_dropout_mode(model, [], train_mode=False)
        selected = args.layer_index or []
        if selected:
            modal_dropout.set_dropout_mode(model, selected, train_mode=True)
            for idx in selected:
                module = modules[idx]
                if not module.__class__.__name__.startswith("Dropout"):
                    raise AssertionError(f"index {idx} did not point to a Dropout layer")
                if module.training is not True:
                    raise AssertionError(f"dropout layer {idx} was not set to train mode")
            checked = selected
        else:
            modal_dropout.set_dropout_mode(model, [], train_mode=True)
            for idx in dropout_indexes:
                if modules[idx].training is not True:
                    raise AssertionError(f"dropout layer {idx} was not toggled by empty index list")
            checked = dropout_indexes

        if args.demo_bad_index:
            bad_index = next(
                idx for idx, module in enumerate(modules)
                if not module.__class__.__name__.startswith("Dropout")
            )
            try:
                modal_dropout.set_dropout_mode(model, [bad_index], train_mode=True)
            except KeyError as exc:
                print(f"Expected bad-index recovery: {exc}")
            else:  # pragma: no cover - would mean modAL behavior changed
                print("FAIL non-dropout index did not raise KeyError", file=sys.stderr)
                return 3

    except Exception as exc:
        print(f"FAIL dropout inspection: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(
        "PASS dropout_inspection: imported torch/skorch/modAL.dropout; "
        f"skorch wrapper={skorch_net.__class__.__name__}; "
        f"dropout_indexes={dropout_indexes}; checked={checked}; device=cpu"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
