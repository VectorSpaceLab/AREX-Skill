#!/usr/bin/env python3
"""No-download smoke for Composer method functional APIs.

Exercises one batch method (MixUp/CutMix) and one model-surgery method
(BlurPool) on random tensors. If torchvision models are unavailable, a tiny
`torch.nn.Sequential` convolutional model is used.
"""

from __future__ import annotations

import sys

import torch
from torch import nn


def _import_composer_functional():
    try:
        from composer import functional as cf
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Composer functional API is unavailable. Install the public package "
            f"with `pip install mosaicml`. Original import error: {exc}",
        ) from exc
    except Exception as exc:  # pragma: no cover - environment-specific import failures
        raise SystemExit(f"Composer import failed before the smoke could run: {exc}") from exc
    return cf


def _tiny_cnn(num_classes: int) -> nn.Module:
    return nn.Sequential(
        nn.Conv2d(3, 32, kernel_size=3, stride=2, padding=1),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(kernel_size=2, stride=2),
        nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
        nn.ReLU(inplace=True),
        nn.AdaptiveAvgPool2d((1, 1)),
        nn.Flatten(),
        nn.Linear(64, num_classes),
    )


def _torchvision_or_tiny(num_classes: int) -> tuple[nn.Module, str]:
    try:
        from torchvision import models

        try:
            model = models.resnet18(weights=None)
        except TypeError:  # older torchvision
            model = models.resnet18(pretrained=False)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model, "torchvision.models.resnet18(weights=None)"
    except Exception:
        return _tiny_cnn(num_classes), "tiny torch.nn.Sequential fallback"


def _count_blur_modules(model: nn.Module) -> int:
    return sum(1 for module in model.modules() if module.__class__.__name__.startswith("Blur"))


def main() -> int:
    cf = _import_composer_functional()

    torch.manual_seed(17)
    batch_size = 8
    num_classes = 10
    images = torch.randn(batch_size, 3, 32, 32)
    labels = torch.arange(batch_size) % num_classes
    reverse_indices = torch.arange(batch_size - 1, -1, -1)

    mixed_images, permuted_labels, mixing = cf.mixup_batch(
        images,
        labels,
        mixing=0.25,
        indices=reverse_indices,
    )
    assert mixed_images.shape == images.shape
    assert torch.equal(permuted_labels, labels[reverse_indices])
    assert abs(float(mixing) - 0.25) < 1e-7

    cutmixed_images, cutmix_labels, keep_area, bbox = cf.cutmix_batch(
        images,
        labels,
        bbox=(4, 4, 20, 20),
        indices=reverse_indices,
    )
    assert cutmixed_images.shape == images.shape
    assert torch.equal(cutmix_labels, labels[reverse_indices])
    assert 0.0 <= float(keep_area) <= 1.0
    assert bbox == (4, 4, 20, 20)

    model, model_source = _torchvision_or_tiny(num_classes=num_classes)
    model.eval()
    blur_modules_before = _count_blur_modules(model)
    cf.apply_blurpool(
        model,
        replace_convs=True,
        replace_maxpools=True,
        blur_first=True,
        min_channels=1,
    )
    blur_modules_after = _count_blur_modules(model)
    assert blur_modules_after > blur_modules_before, "BlurPool did not replace any modules"

    cf.apply_channels_last(model)
    with torch.no_grad():
        logits = model(mixed_images.to(memory_format=torch.channels_last))
    assert logits.shape == (batch_size, num_classes)

    smoothed = cf.smooth_labels(logits, labels, smoothing=0.1)
    assert smoothed.shape == logits.shape
    assert torch.allclose(smoothed.sum(dim=1), torch.ones(batch_size), atol=1e-5)

    print("Composer methods smoke passed")
    print(f"model={model_source}")
    print(f"mixup_mixing={float(mixing):.2f} cutmix_keep_area={float(keep_area):.2f}")
    print(f"blur_modules_before={blur_modules_before} blur_modules_after={blur_modules_after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
