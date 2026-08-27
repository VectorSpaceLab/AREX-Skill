#!/usr/bin/env python3
"""Convert a sorted image sequence with RobustVideoMatting and write PNG outputs.

This is a safe wrapper around the repository's ``convert_video`` API for the
image-sequence case. It does not download weights and does not require video
encoding. Pass --repo-root when the local RobustVideoMatting source modules are
not already importable.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = Path(repo_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"--repo-root does not exist: {root}")
    sys.path.insert(0, str(root))


def _resolve_device(requested: str):
    import torch

    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but PyTorch reports no CUDA device. Use --device cpu or install a CUDA-capable torch build.")
    return requested


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RobustVideoMatting convert_video on a directory of sorted image frames.")
    parser.add_argument("--repo-root", help="Optional local RobustVideoMatting checkout to add to sys.path.")
    parser.add_argument("--variant", default="mobilenetv3", choices=["mobilenetv3", "resnet50"], help="Model variant matching the checkpoint.")
    parser.add_argument("--checkpoint", required=True, help="Path to a PyTorch state_dict checkpoint (.pth). No weights are downloaded.")
    parser.add_argument("--input-dir", required=True, help="Directory containing sorted .png/.jpg frames.")
    parser.add_argument("--output-dir", required=True, help="Directory under which composition/alpha/foreground output folders are created.")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"], help="Inference device.")
    parser.add_argument("--downsample-ratio", type=float, help="Optional downsample_ratio in (0,1]; omit to use auto ratio.")
    parser.add_argument("--seq-chunk", type=int, default=1, help="Number of frames per model call.")
    parser.add_argument("--input-resize", type=int, nargs=2, metavar=("WIDTH", "HEIGHT"), help="Optional resize before inference.")
    parser.add_argument("--composition", action="store_true", help="Write RGBA composition PNG sequence.")
    parser.add_argument("--alpha", action="store_true", help="Write alpha PNG sequence.")
    parser.add_argument("--foreground", action="store_true", help="Write foreground PNG sequence.")
    parser.add_argument("--num-workers", type=int, default=0, help="DataLoader workers for reading image sequence.")
    parser.add_argument("--disable-progress", action="store_true", help="Disable tqdm progress bar.")
    args = parser.parse_args()

    if args.downsample_ratio is not None and not (0 < args.downsample_ratio <= 1):
        raise SystemExit("--downsample-ratio must be > 0 and <= 1")
    if args.seq_chunk < 1:
        raise SystemExit("--seq-chunk must be >= 1")
    if args.num_workers < 0:
        raise SystemExit("--num-workers must be >= 0")

    checkpoint = Path(args.checkpoint).expanduser().resolve()
    input_dir = Path(args.input_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    if not checkpoint.is_file():
        raise SystemExit(f"Checkpoint file not found: {checkpoint}")
    if not input_dir.is_dir():
        raise SystemExit(f"Input image directory not found: {input_dir}")
    if not any(input_dir.iterdir()):
        raise SystemExit(f"Input image directory is empty: {input_dir}")

    # Default to the two most common reusable outputs when the user did not choose.
    if not (args.composition or args.alpha or args.foreground):
        args.composition = True
        args.alpha = True

    _add_repo_root(args.repo_root)
    try:
        import torch
        from model import MattingNetwork
        from inference import convert_video
    except ImportError as exc:
        raise SystemExit(
            "Could not import RobustVideoMatting inference modules. Install torch/torchvision/tqdm/Pillow and pass --repo-root if needed. "
            f"Original error: {type(exc).__name__}: {exc}"
        ) from exc

    device = _resolve_device(args.device)
    model = MattingNetwork(args.variant).eval().to(device)
    try:
        state = torch.load(str(checkpoint), map_location=device)
        model.load_state_dict(state)
    except Exception as exc:
        raise SystemExit(f"Failed to load checkpoint into MattingNetwork({args.variant!r}): {type(exc).__name__}: {exc}") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    output_composition = str(output_dir / "composition") if args.composition else None
    output_alpha = str(output_dir / "alpha") if args.alpha else None
    output_foreground = str(output_dir / "foreground") if args.foreground else None

    convert_video(
        model,
        input_source=str(input_dir),
        input_resize=tuple(args.input_resize) if args.input_resize else None,
        downsample_ratio=args.downsample_ratio,
        output_type="png_sequence",
        output_composition=output_composition,
        output_alpha=output_alpha,
        output_foreground=output_foreground,
        seq_chunk=args.seq_chunk,
        num_workers=args.num_workers,
        progress=not args.disable_progress,
    )
    print("Wrote outputs under", output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
