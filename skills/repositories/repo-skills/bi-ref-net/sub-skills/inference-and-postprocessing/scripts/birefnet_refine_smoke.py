#!/usr/bin/env python3
"""CPU-only foreground-refinement smoke test for BiRefNet."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a tiny CPU foreground-refinement smoke test and print output facts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", required=True, help="Explicit BiRefNet checkout root that provides image_proc.py.")
    parser.add_argument("--radius", type=int, default=6, help="Blur radius passed to refine_foreground for the smoke sample.")
    return parser


def _load_refine_foreground(repo_root: Path):
    repo_root = repo_root.expanduser().resolve()
    if not repo_root.is_dir():
        raise FileNotFoundError(f"Repo root does not exist or is not a directory: {repo_root}")
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    try:
        from image_proc import refine_foreground
    except Exception as exc:  # pragma: no cover - surfaced to the user with context
        raise RuntimeError(
            "Could not import image_proc.refine_foreground from --repo-root. Install Pillow, numpy, opencv-python, torch, and torchvision, and confirm the checkout contains image_proc.py."
        ) from exc
    return refine_foreground


def run(args: argparse.Namespace) -> int:
    try:
        import numpy as np
        from PIL import Image, ImageDraw
    except Exception as exc:  # pragma: no cover - surfaced to the user with context
        raise RuntimeError("The smoke test needs numpy and Pillow.") from exc

    refine_foreground = _load_refine_foreground(Path(args.repo_root))

    image = Image.new("RGB", (10, 8), (40, 120, 200))
    image_draw = ImageDraw.Draw(image)
    image_draw.rectangle((2, 2, 7, 5), fill=(220, 180, 40))

    mask = Image.new("L", image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((1, 1, 8, 6), fill=255)

    output = refine_foreground(image, mask, r=args.radius, device="cpu")
    output_array = np.asarray(output)

    if output.mode != "RGB":
        raise AssertionError(f"Expected RGB output, received mode={output.mode}")
    if output.size != image.size:
        raise AssertionError(f"Expected output size {image.size}, received {output.size}")
    if output_array.shape != (image.height, image.width, 3):
        raise AssertionError(f"Unexpected output shape: {output_array.shape}")
    if output_array.dtype != np.uint8:
        raise AssertionError(f"Unexpected output dtype: {output_array.dtype}")

    print("refine_foreground_cpu_smoke=passed")
    print(f"repo_root={Path(args.repo_root).expanduser().resolve()}")
    print("refine_device=cpu")
    print(f"input_mode={image.mode}")
    print(f"input_size={image.size}")
    print(f"mask_mode={mask.mode}")
    print(f"mask_size={mask.size}")
    print(f"output_mode={output.mode}")
    print(f"output_size={output.size}")
    print(f"output_dtype={output_array.dtype}")
    print(f"output_shape={output_array.shape}")
    print(f"output_min={int(output_array.min())}")
    print(f"output_max={int(output_array.max())}")
    print(f"output_mean={float(output_array.mean()):.2f}")
    center_pixel = output_array[output_array.shape[0] // 2, output_array.shape[1] // 2].tolist()
    print(f"center_pixel={center_pixel}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
