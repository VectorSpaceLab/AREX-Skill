#!/usr/bin/env python3
"""Tiny deterministic smoke checks for MedicalZooPytorch loss contracts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np
import torch


def _ensure_medical_zoo_importable() -> None:
    """Import installed package first; otherwise find a nearby repo root."""
    try:
        import lib.losses3D  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        if (parent / "lib" / "losses3D" / "__init__.py").is_file():
            sys.path.insert(0, str(parent))
            return

    raise RuntimeError(
        "Could not import MedicalZooPytorch `lib.losses3D`. "
        "Install/make the package importable, or run this script from a "
        "MedicalZooPytorch checkout with its repo root on PYTHONPATH."
    )


_ensure_medical_zoo_importable()

from lib.losses3D import (  # noqa: E402
    BCEDiceLoss,
    ContrastiveLoss,
    DiceLoss,
    DiceLoss2D,
    GeneralizedDiceLoss,
    PixelWiseCrossEntropyLoss,
    TagsAngularLoss,
    WeightedCrossEntropyLoss,
    WeightedSmoothL1Loss,
    create_loss,
)
from lib.losses3D.VAEloss import loss_vae  # noqa: E402


def _device(use_cuda: bool) -> torch.device:
    if use_cuda and torch.cuda.is_available():
        return torch.device("cuda")
    if use_cuda:
        print("[skip] --cuda requested, but CUDA is not available; running CPU smoke instead")
    return torch.device("cpu")


def _segmentation_fixture(device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
    logits = torch.linspace(-0.8, 0.8, steps=32, device=device, dtype=torch.float32)
    logits = logits.view(1, 4, 2, 2, 2).clone().detach().requires_grad_(True)
    target = torch.tensor(
        [[[[0, 1], [2, 3]], [[1, 2], [3, 0]]]],
        device=device,
        dtype=torch.long,
    )
    return logits, target


def _contrastive_fixture(device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
    embeddings = torch.tensor(
        [[
            [[[0.10, 0.15], [0.20, 0.25]], [[0.80, 0.85], [0.90, 0.95]]],
            [[[0.90, 0.85], [0.80, 0.75]], [[0.20, 0.15], [0.10, 0.05]]],
        ]],
        device=device,
        dtype=torch.float32,
    ).requires_grad_(True)
    # Contiguous instance ids are required because ContrastiveLoss uses ids as one-hot indices.
    target = torch.tensor(
        [[[[0, 0], [0, 1]], [[1, 1], [0, 1]]]],
        device=device,
        dtype=torch.long,
    )
    return embeddings, target


def _require_scalar(name: str, value: torch.Tensor) -> float:
    assert isinstance(value, torch.Tensor), f"{name} did not return a torch.Tensor"
    assert value.ndim == 0, f"{name} should return a scalar tensor, got shape {tuple(value.shape)}"
    assert torch.isfinite(value).item(), f"{name} returned a non-finite value"
    item = float(value.detach().cpu().item())
    print(f"[ok] {name}: scalar={item:.6f}")
    return item


def _require_tuple(name: str, value: object, expected_score_shape: Tuple[int, ...]) -> None:
    assert isinstance(value, tuple) and len(value) == 2, f"{name} should return (loss, scores)"
    loss, scores = value
    _require_scalar(name, loss)
    scores_array = np.asarray(scores)
    assert scores_array.shape == expected_score_shape, (
        f"{name} side score shape {scores_array.shape} != {expected_score_shape}"
    )
    assert np.isfinite(scores_array).all(), f"{name} returned non-finite side scores"
    print(f"[ok] {name}: side_score_shape={scores_array.shape}")


def _expect_unsupported(names: Iterable[str]) -> None:
    for name in names:
        try:
            create_loss(name)
        except RuntimeError as exc:
            message = str(exc)
            assert "Unsupported loss function" in message and "Supported losses" in message
            print(f"[ok] create_loss({name!r}) rejected with supported-loss guidance")
        else:
            raise AssertionError(f"create_loss({name!r}) unexpectedly succeeded")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cuda", action="store_true", help="run on CUDA when available")
    args = parser.parse_args()

    torch.manual_seed(1234)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(1234)

    device = _device(args.cuda)
    logits, target = _segmentation_fixture(device)

    _require_tuple(
        "DiceLoss(classes=4, softmax)",
        DiceLoss(classes=4, sigmoid_normalization=False).to(device)(logits, target),
        (4,),
    )
    _require_tuple(
        "GeneralizedDiceLoss(classes=4, softmax)",
        GeneralizedDiceLoss(classes=4, sigmoid_normalization=False).to(device)(logits, target),
        (),
    )
    _require_tuple(
        "BCEDiceLoss(classes=4)",
        BCEDiceLoss(classes=4).to(device)(logits, target),
        (4,),
    )

    _require_scalar(
        "WeightedCrossEntropyLoss",
        WeightedCrossEntropyLoss(ignore_index=-1).to(device)(logits, target),
    )
    pixel_weights = torch.ones_like(target, dtype=torch.float32, device=device)
    class_weights = torch.ones(4, dtype=torch.float32, device=device)
    _require_scalar(
        "PixelWiseCrossEntropyLoss",
        PixelWiseCrossEntropyLoss(class_weights=class_weights).to(device)(logits, target, pixel_weights),
    )

    smooth_logits = logits.clone().detach().requires_grad_(True)
    smooth_loss = WeightedSmoothL1Loss(classes=4, threshold=0.5, initial_weight=0.25).to(device)(
        smooth_logits, target
    )
    _require_scalar("WeightedSmoothL1Loss", smooth_loss)
    smooth_loss.backward()
    assert smooth_logits.grad is not None and torch.isfinite(smooth_logits.grad).all()
    print("[ok] WeightedSmoothL1Loss backward")

    tag_inputs = [logits.detach().clone() + offset for offset in (0.0, 0.05, 0.10)]
    tag_targets = [target, target, target]
    _require_scalar("TagsAngularLoss", TagsAngularLoss(classes=4).to(device)(tag_inputs, tag_targets))

    embeddings, instance_target = _contrastive_fixture(device)
    _require_scalar("ContrastiveLoss", ContrastiveLoss().to(device)(embeddings, instance_target))

    dice2d_logits = logits.detach()[0, :, 0, :, :].clone().requires_grad_(True)
    dice2d_target = target[:, 0, :, :]
    _require_tuple("DiceLoss2D", DiceLoss2D(classes=4).to(device)(dice2d_logits, dice2d_target), (4,))

    recon = torch.full((1, 1, 2, 2, 2), 0.4, dtype=torch.float32, device=device)
    original = torch.full_like(recon, 0.3)
    mu = torch.zeros((1, 2), dtype=torch.float32, device=device)
    logvar = torch.zeros_like(mu)
    _require_scalar("loss_vae(type='L1')", loss_vae(recon, original, mu, logvar, type="L1"))

    _require_scalar("create_loss('CrossEntropyLoss')", create_loss("CrossEntropyLoss").to(device)(logits, target))
    _require_tuple("create_loss('DiceLoss')", create_loss("DiceLoss").to(device)(logits, target), (4,))
    _expect_unsupported(["ContrastiveLoss", "DiceLoss2D", "NotALoss"])

    print(f"[done] MedicalZooPytorch loss smoke checks passed on {device.type}")


if __name__ == "__main__":
    main()
