#!/usr/bin/env python3
"""Run a deterministic, model-free smoke test for Kornia losses and metrics."""

from __future__ import annotations

import argparse

import kornia
import torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="auto",
        help="Execution device. 'auto' prefers CUDA when available.",
    )
    return parser.parse_args()


def resolve_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise SystemExit("--device cuda requested, but CUDA is unavailable")
    return torch.device(requested)


def require_finite(name: str, value: torch.Tensor) -> None:
    if not torch.isfinite(value).all().item():
        raise AssertionError(f"{name} contains a non-finite value: {value}")


def main() -> None:
    args = parse_args()
    device = resolve_device(args.device)
    torch.manual_seed(0)

    # Use values in [0, 1] and a non-identical reference so PSNR is finite.
    image = torch.linspace(0.05, 0.95, steps=25, device=device, dtype=torch.float32).reshape(1, 1, 5, 5)
    reference = (image * 0.9 + 0.04).clamp(0.0, 1.0)

    ssim_map = kornia.metrics.ssim(image, reference, window_size=3, max_val=1.0)
    ssim_value = kornia.losses.ssim_loss(image, reference, window_size=3, max_val=1.0, reduction="mean")
    psnr_value = kornia.metrics.psnr(image, reference, max_val=1.0)
    psnr_objective = kornia.losses.psnr_loss(image, reference, max_val=1.0)

    assert ssim_map.shape == image.shape, (ssim_map.shape, image.shape)
    assert ssim_value.shape == torch.Size([])
    assert psnr_value.shape == torch.Size([])
    assert psnr_objective.shape == torch.Size([])
    for name, value in (
        ("ssim_map", ssim_map),
        ("ssim_loss", ssim_value),
        ("psnr", psnr_value),
        ("psnr_loss", psnr_objective),
    ):
        require_finite(name, value)

    # Train on raw multiclass logits, then discretize only for mean IoU.
    logits = torch.tensor(
        [
            [
                [[3.0, -1.0, 0.2], [2.0, -0.5, 0.0]],
                [[-1.0, 3.0, 0.1], [-0.5, 2.5, 0.4]],
                [[0.0, -1.0, 2.5], [0.1, -0.5, 2.0]],
            ]
        ],
        device=device,
        dtype=torch.float32,
        requires_grad=True,
    )
    labels = torch.tensor([[[0, 1, 2], [0, 1, 2]]], device=device, dtype=torch.int64)

    dice_value = kornia.losses.dice_loss(logits, labels, average="micro")
    focal_value = kornia.losses.focal_loss(logits, labels, alpha=0.25, gamma=2.0, reduction="mean")
    train_objective = dice_value + 0.1 * focal_value
    assert dice_value.shape == torch.Size([])
    assert focal_value.shape == torch.Size([])
    assert train_objective.shape == torch.Size([])
    require_finite("dice_loss", dice_value)
    require_finite("focal_loss", focal_value)

    train_objective.backward()
    if logits.grad is None:
        raise AssertionError("the differentiable segmentation objective produced no gradient")
    require_finite("logits.grad", logits.grad)

    predicted_labels = logits.detach().argmax(dim=1).to(torch.int64)
    iou_by_class = kornia.metrics.mean_iou(predicted_labels, labels, num_classes=3)
    assert iou_by_class.shape == (1, 3), iou_by_class.shape
    require_finite("mean_iou", iou_by_class)

    print(f"device={device}")
    print(f"ssim_loss={ssim_value.item():.6f} psnr={psnr_value.item():.6f} psnr_loss={psnr_objective.item():.6f}")
    print(f"dice_loss={dice_value.item():.6f} focal_loss={focal_value.item():.6f} mean_iou={iou_by_class.tolist()}")
    print("loss/metric smoke: OK")


if __name__ == "__main__":
    main()
