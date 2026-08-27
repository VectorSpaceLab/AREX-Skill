#!/usr/bin/env python3
"""Cross-module no-download smoke for core Kornia public APIs."""

from __future__ import annotations

import argparse

import torch

import kornia.augmentation as KA
import kornia.color as KC
import kornia.filters as KF
import kornia.geometry as KG
import kornia.losses as KL
import kornia.metrics as KM
from kornia.feature import match_nn
from kornia.models.sam import SamConfig
from kornia.models.rt_detr import RTDETRConfig


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but torch.cuda.is_available() is false")
    return torch.device(requested)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args()
    device = choose_device(args.device)

    torch.manual_seed(0)
    x = torch.rand(2, 3, 16, 20, device=device)
    gray = KC.rgb_to_grayscale(x)
    assert gray.shape == (2, 1, 16, 20)

    blur = KF.gaussian_blur2d(x, (3, 3), (1.0, 1.0))
    assert blur.shape == x.shape and torch.isfinite(blur).all()

    aug = KA.AugmentationSequential(KA.RandomHorizontalFlip(p=1.0), data_keys=["input"]).to(device)
    aug_out = aug(x)
    assert aug_out.shape == x.shape

    resized = KG.resize(x, (8, 10))
    assert resized.shape == (2, 3, 8, 10)

    desc1 = torch.tensor([[0.0, 0.0], [1.0, 1.0]], device=device)
    desc2 = torch.tensor([[1.0, 1.0], [0.0, 0.0]], device=device)
    dists, idxs = match_nn(desc1, desc2)
    assert dists.shape == (2, 1) and idxs.shape == (2, 2)

    y = x.clone().detach().requires_grad_(True)
    loss = KL.ssim_loss(y, x.detach(), window_size=3)
    loss.backward()
    assert y.grad is not None and torch.isfinite(y.grad).all()

    pred = torch.tensor([[0, 1], [1, 0]], device=device)
    target = torch.tensor([[0, 1], [0, 0]], device=device)
    iou = KM.mean_iou(pred[None], target[None], num_classes=2)
    assert iou.shape[-1] == 2

    # Config construction only; no model weights or downloads.
    assert SamConfig("mobile_sam").model_type is not None
    assert RTDETRConfig("resnet18d", num_classes=2).num_classes == 2

    print("kornia-api-smoke-ok", f"device={device}")


if __name__ == "__main__":
    main()
