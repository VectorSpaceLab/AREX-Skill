#!/usr/bin/env python3
"""Sample images from a stylegan2_pytorch checkpoint using ModelLoader.

This helper expects the default CLI checkpoint layout:
    <base-dir>/models/<name>/model_<n>.pt
    <base-dir>/models/<name>/.config.json

It writes one image grid and refuses to overwrite existing output unless
--overwrite is supplied.

Example:
    python scripts/sample_from_checkpoint.py --base-dir /path/to/run-base --name default --output-dir /tmp/sg2-samples
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path


def _fail(message: str, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def _checkpoint_number(path: Path) -> int | None:
    match = re.fullmatch(r"model_(\d+)\.pt", path.name)
    return int(match.group(1)) if match else None


def _find_checkpoint(base_dir: Path, name: str, load_from: int) -> Path:
    model_dir = base_dir / "models" / name
    if not model_dir.exists():
        _fail(
            f"Expected checkpoint directory {model_dir} does not exist. "
            "ModelLoader only knows the default base_dir/models/<name> layout."
        )

    if load_from >= 0:
        checkpoint = model_dir / f"model_{load_from}.pt"
        if not checkpoint.exists():
            _fail(f"Requested checkpoint does not exist: {checkpoint}")
        return checkpoint

    numbered = []
    for path in model_dir.glob("model_*.pt"):
        num = _checkpoint_number(path)
        if num is not None:
            numbered.append((num, path))
    if not numbered:
        _fail(f"No model_*.pt checkpoints found in {model_dir}")
    return sorted(numbered)[-1][1]


def _check_cuda() -> None:
    try:
        import torch
    except Exception as exc:
        _fail(f"Could not import torch: {exc}")
    if not torch.cuda.is_available():
        _fail("CUDA is required: stylegan2_pytorch imports and ModelLoader sampling use CUDA.", code=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a sample grid from a stylegan2_pytorch checkpoint.")
    parser.add_argument("--base-dir", required=True, type=Path, help="Run base directory containing models/<name>/.")
    parser.add_argument("--name", default="default", help="Project/run name used during training.")
    parser.add_argument("--load-from", "--load_from", dest="load_from", type=int, default=-1, help="Checkpoint number, or -1 for latest.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for the generated sample grid.")
    parser.add_argument("--output-name", default="sample_grid.png", help="Output image filename.")
    parser.add_argument("--count", type=int, default=4, help="Number of samples to generate.")
    parser.add_argument("--trunc-psi", "--trunc_psi", dest="trunc_psi", type=float, default=0.75, help="Truncation psi passed to noise_to_styles.")
    parser.add_argument("--seed", type=int, default=42, help="Torch random seed.")
    parser.add_argument("--nrow", type=int, help="Grid row width. Defaults to sqrt(count) rounded up.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing output image.")
    args = parser.parse_args()

    if args.count <= 0:
        _fail("--count must be positive")

    base_dir = args.base_dir.resolve()
    checkpoint = _find_checkpoint(base_dir=base_dir, name=args.name, load_from=args.load_from)
    config_path = checkpoint.parent / ".config.json"
    if not config_path.exists():
        _fail(f"Expected config file next to checkpoint: {config_path}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / args.output_name
    if output_path.exists() and not args.overwrite:
        _fail(f"Refusing to overwrite existing output {output_path}; pass --overwrite to replace it.")

    _check_cuda()

    try:
        import torch
        from torchvision.utils import save_image
        from stylegan2_pytorch import ModelLoader
    except Exception as exc:
        _fail(f"Could not import sampling dependencies: {type(exc).__name__}: {exc}")

    torch.manual_seed(args.seed)
    loader = ModelLoader(base_dir=str(base_dir), name=args.name, load_from=args.load_from)
    noise = torch.randn(args.count, 512).cuda()
    styles = loader.noise_to_styles(noise, trunc_psi=args.trunc_psi)
    images = loader.styles_to_images(styles)
    nrow = args.nrow or math.ceil(math.sqrt(args.count))
    save_image(images, str(output_path), nrow=nrow)

    print(f"Loaded checkpoint: {checkpoint}")
    print(f"Wrote sample grid: {output_path}")


if __name__ == "__main__":
    main()
