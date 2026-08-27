#!/usr/bin/env python3
"""Smoke-test Lightly SSL building blocks with synthetic inputs only.

This helper checks the core low-level stack without downloads:
- a tiny `LightlyDataset` folder and SimCLR-style collate
- a `SimCLRTransform` on a synthetic PIL image
- a `SimCLRProjectionHead` + `NTXentLoss` + `NNMemoryBankModule` tensor path

If optional extras are missing, the script reports a clear import error rather
than trying to fall back to downloads or a full training loop.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from typing import Any, Iterable


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-test Lightly SSL building blocks with synthetic inputs only. "
            "No downloads, no training loop, and no external datasets are used."
        )
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help=(
            "Tensor device for the head/loss smoke. 'auto' prefers CUDA when "
            "available."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for the synthetic tensors and images.",
    )
    return parser


def _require_dependencies() -> tuple[Any, Any, Any, Any, Any, Any]:
    """Import the required Lightly components with a clear error on failure."""
    try:
        import torch
        from lightly.data import LightlyDataset, SimCLRCollateFunction
        from lightly.loss import NTXentLoss
        from lightly.models.modules import NNMemoryBankModule, SimCLRProjectionHead
        from lightly.transforms import SimCLRTransform
    except Exception as exc:  # pragma: no cover - exercised by import failures
        raise SystemExit(
            "Failed to import the required Lightly components. Install the base "
            "package with 'pip install lightly'. Optional extras are 'lightly[timm]' "
            "for TIMM/MAE/ViT-style modules and 'lightly[video]' for video/PyAV "
            f"support. Import error: {exc}"
        ) from exc

    return (
        torch,
        LightlyDataset,
        SimCLRCollateFunction,
        NTXentLoss,
        NNMemoryBankModule,
        SimCLRProjectionHead,
        SimCLRTransform,
    )


def _resolve_device(choice: str, torch: Any) -> Any:
    """Resolve the requested device."""
    if choice == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if choice == "cuda" and not torch.cuda.is_available():
        raise SystemExit(
            "CUDA was requested with --device cuda, but torch.cuda.is_available() "
            "is False. Install or enable the optional CUDA backend, or rerun with "
            "--device cpu or --device auto."
        )
    return torch.device(choice)


def _make_image(color: tuple[int, int, int], size: tuple[int, int] = (32, 32)):
    """Create a tiny RGB PIL image."""
    from PIL import Image

    return Image.new("RGB", size, color=color)


def _assert_shape(actual: Iterable[int], expected: tuple[int, ...], label: str) -> None:
    """Raise a readable error if a tensor or sequence shape does not match."""
    actual_tuple = tuple(actual)
    if actual_tuple != expected:
        raise RuntimeError(f"{label} shape mismatch: expected {expected}, got {actual_tuple}")


def smoke_dataset_and_collate(lightly_dataset: Any, collate_cls: Any) -> None:
    """Check that LightlyDataset and a SimCLR-style collate agree on arity."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        for idx, color in enumerate(((40, 90, 150), (150, 90, 40))):
            _make_image(color).save(root / f"sample_{idx}.png")

        dataset = lightly_dataset(input_dir=str(root))
        if len(dataset) != 2:
            raise RuntimeError(f"LightlyDataset should contain 2 samples, got {len(dataset)}")

        filenames = dataset.get_filenames()
        if len(filenames) != 2:
            raise RuntimeError(f"Expected 2 filenames, got {len(filenames)}")

        batch = [dataset[i] for i in range(len(dataset))]
        collate = collate_cls(input_size=16, gaussian_blur=0.0)
        views, labels, fnames = collate(batch)

        if len(views) != 2:
            raise RuntimeError(f"SimCLRCollateFunction should return 2 views, got {len(views)}")
        for idx, view in enumerate(views):
            _assert_shape(view.shape, (2, 3, 16, 16), f"collate view {idx}")
        _assert_shape(labels.shape, (2,), "collate labels")
        if len(fnames) != 2:
            raise RuntimeError(f"Expected 2 filenames from collate, got {len(fnames)}")

        print("ok: LightlyDataset + SimCLRCollateFunction")


def smoke_transform(simclr_transform: Any) -> None:
    """Check that SimCLRTransform returns two image views."""
    image = _make_image((100, 120, 140), size=(32, 32))
    transform = simclr_transform(input_size=16, gaussian_blur=0.0)
    views = transform(image)
    if len(views) != 2:
        raise RuntimeError(f"SimCLRTransform should return 2 views, got {len(views)}")
    for idx, view in enumerate(views):
        _assert_shape(view.shape, (3, 16, 16), f"transform view {idx}")

    print("ok: SimCLRTransform")


def smoke_projection_head_and_loss(
    torch: Any,
    device: Any,
    projection_head_cls: Any,
    loss_cls: Any,
    memory_bank_cls: Any,
) -> None:
    """Check a minimal projection-head + contrastive-loss tensor path."""
    torch.manual_seed(0)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(0)

    head = projection_head_cls(input_dim=8, hidden_dim=16, output_dim=4).to(device)
    x0 = torch.randn((4, 8), device=device)
    x1 = torch.randn((4, 8), device=device)

    z0 = head(x0)
    z1 = head(x1)
    _assert_shape(z0.shape, (4, 4), "projection z0")
    _assert_shape(z1.shape, (4, 4), "projection z1")

    loss_fn = loss_cls(temperature=0.5, memory_bank_size=0)
    loss = loss_fn(z0, z1)
    if not torch.isfinite(loss).item():
        raise RuntimeError("NTXentLoss produced a non-finite value")
    loss.backward()

    memory_bank = memory_bank_cls(size=(8, 4)).to(device)
    nearest = memory_bank(z0.detach(), update=True)
    _assert_shape(nearest.shape, (4, 4), "memory-bank nearest neighbours")

    print(f"ok: SimCLRProjectionHead + NTXentLoss + NNMemoryBankModule (loss={float(loss.detach()):.6f})")


def run(device_choice: str, seed: int) -> int:
    """Run all smoke checks."""
    torch, lightly_dataset, collate_cls, loss_cls, memory_bank_cls, projection_head_cls, simclr_transform = (
        _require_dependencies()
    )

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    device = _resolve_device(device_choice, torch)
    smoke_dataset_and_collate(lightly_dataset, collate_cls)
    smoke_transform(simclr_transform)
    smoke_projection_head_and_loss(
        torch=torch,
        device=device,
        projection_head_cls=projection_head_cls,
        loss_cls=loss_cls,
        memory_bank_cls=memory_bank_cls,
    )

    print(f"overall-ok: device={device.type}")
    return 0


def main() -> int:
    """CLI entry point."""
    args = build_parser().parse_args()
    return run(device_choice=args.device, seed=args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
