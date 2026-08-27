#!/usr/bin/env python3
"""Tiny Albumentations + PyTorch dataset template and shape checker."""

from __future__ import annotations

import argparse
from typing import Any


def load_runtime() -> tuple[Any, Any, Any, Any, Any]:
    """Import optional runtime dependencies after argparse can show --help."""
    try:
        import albumentations as A
        import numpy as np
        import torch
        from albumentations.pytorch import ToTensor3D, ToTensorV2
    except ImportError as exc:  # pragma: no cover - depends on optional environment
        raise SystemExit(
            "PyTorch tensor transforms require albumentations and torch. Install with: "
            'pip install "albumentations[pytorch]"'
        ) from exc
    return A, np, torch, ToTensorV2, ToTensor3D


def build_2d_transform(
    albumentations_module: Any,
    to_tensor_v2: Any,
    *,
    transpose_mask: bool = False,
    normalize: bool = True,
) -> Any:
    transforms: list[Any] = [albumentations_module.Resize(32, 32)]
    if normalize:
        transforms.append(
            albumentations_module.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        )
    transforms.append(to_tensor_v2(transpose_mask=transpose_mask))
    return albumentations_module.Compose(transforms, strict=True, seed=137)


def make_tiny_dataset_class(albumentations_module: Any, numpy_module: Any, torch_module: Any, to_tensor_v2: Any) -> type:
    """Create an in-memory dataset showing where Albumentations belongs in __getitem__."""

    class TinySegmentationDataset(torch_module.utils.data.Dataset):
        def __init__(self, transform: Any | None = None) -> None:
            self.transform = transform or build_2d_transform(albumentations_module, to_tensor_v2)
            self.image = numpy_module.arange(64 * 48 * 3, dtype=numpy_module.uint8).reshape(64, 48, 3)
            self.mask = numpy_module.zeros((64, 48), dtype=numpy_module.uint8)
            self.mask[16:48, 12:36] = 1

        def __len__(self) -> int:
            return 1

        def __getitem__(self, index: int) -> dict[str, Any]:
            if index != 0:
                raise IndexError(index)
            sample = self.transform(image=self.image.copy(), mask=self.mask.copy())
            return {"image": sample["image"], "mask": sample["mask"]}

    return TinySegmentationDataset


def check_2d(transpose_mask: bool, normalize: bool) -> None:
    albumentations_module, numpy_module, torch_module, to_tensor_v2, _to_tensor_3d = load_runtime()
    dataset_class = make_tiny_dataset_class(albumentations_module, numpy_module, torch_module, to_tensor_v2)
    transform = build_2d_transform(
        albumentations_module,
        to_tensor_v2,
        transpose_mask=transpose_mask,
        normalize=normalize,
    )
    sample = dataset_class(transform)[0]
    image = sample["image"]
    mask = sample["mask"]
    print(f"image shape={tuple(image.shape)} dtype={image.dtype}")
    print(f"mask shape={tuple(mask.shape)} dtype={mask.dtype}")
    assert tuple(image.shape) == (3, 32, 32)
    assert tuple(mask.shape) == (32, 32)
    if normalize:
        assert image.dtype.is_floating_point
    else:
        assert image.dtype == torch_module.uint8


def check_3d() -> None:
    albumentations_module, numpy_module, _torch_module, _to_tensor_v2, to_tensor_3d = load_runtime()
    transform = albumentations_module.Compose([to_tensor_3d(p=1)], strict=True)
    volume = numpy_module.zeros((8, 16, 12, 2), dtype=numpy_module.uint8)
    mask3d = numpy_module.zeros((8, 16, 12), dtype=numpy_module.uint8)
    sample = transform(volume=volume, mask3d=mask3d)
    print(f"volume shape={tuple(sample['volume'].shape)} dtype={sample['volume'].dtype}")
    print(f"mask3d shape={tuple(sample['mask3d'].shape)} dtype={sample['mask3d'].dtype}")
    assert tuple(sample["volume"].shape) == (2, 8, 16, 12)
    assert tuple(sample["mask3d"].shape) == (1, 8, 16, 12)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny Albumentations PyTorch tensor-conversion smoke check.",
    )
    parser.add_argument("--mode", choices=("2d", "3d"), default="2d", help="Which tensor conversion example to run.")
    parser.add_argument(
        "--transpose-mask",
        action="store_true",
        help="Pass transpose_mask=True to ToTensorV2. The built-in 2D mask is H,W, so its shape remains H,W.",
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Skip Normalize to demonstrate that ToTensorV2 preserves uint8 image values.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "2d":
        check_2d(transpose_mask=args.transpose_mask, normalize=not args.no_normalize)
    else:
        check_3d()
    print("ok")


if __name__ == "__main__":
    main()
