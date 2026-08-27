#!/usr/bin/env python3
"""Small public-API smoke for Kornia image processing."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import torch

import kornia.color as KC
import kornia.enhance as KE
import kornia.filters as KF
import kornia.morphology as KM
from kornia.io import ImageLoadType, load_image, write_image


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but torch.cuda.is_available() is false")
    return torch.device(requested)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--with-io-roundtrip", action="store_true", help="write/read a temporary PNG using kornia.io")
    args = parser.parse_args()

    device = choose_device(args.device)
    torch.manual_seed(0)
    x = torch.linspace(0, 1, 3 * 12 * 16, device=device, dtype=torch.float32).reshape(1, 3, 12, 16)

    gray = KC.rgb_to_grayscale(x)
    assert gray.shape == (1, 1, 12, 16)
    rgb = KC.grayscale_to_rgb(gray)
    assert rgb.shape == x.shape

    blurred = KF.gaussian_blur2d(x, (3, 3), (1.2, 1.2))
    edges = KF.sobel(x)
    assert blurred.shape == x.shape
    assert edges.shape == x.shape

    adjusted = KE.adjust_gamma(blurred.clamp(0, 1), gamma=1.2)
    assert adjusted.shape == x.shape
    assert torch.isfinite(adjusted).all()

    mask = (gray > gray.mean()).float()
    kernel = torch.ones(3, 3, device=device)
    dilated = KM.dilation(mask, kernel)
    eroded = KM.erosion(dilated, kernel)
    assert dilated.shape == mask.shape
    assert eroded.shape == mask.shape

    if args.with_io_roundtrip:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "smoke.png"
            write_image(path, (x[0].detach().cpu().clamp(0, 1) * 255).to(torch.uint8))
            loaded = load_image(path, ImageLoadType.RGB32, device=device)
            assert loaded.shape[0] == 3
            assert loaded.dtype == torch.float32
            assert torch.isfinite(loaded).all()

    print("processing-smoke-ok", f"device={device}")


if __name__ == "__main__":
    main()
