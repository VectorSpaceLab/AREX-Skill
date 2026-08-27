#!/usr/bin/env python3
"""
Safe command-line template for min(DALL·E).

This is a portable, skill-owned replacement for the upstream command-line
script behavior. It defaults to dry run; add --run only when model downloads
and inference are approved.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ASCII_CHARS = list(".,;/IOX")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan or run a min(DALL·E) CLI-style image generation request.")
    parser.add_argument("--run", action="store_true", help="Actually construct MinDalle and generate an image; may download large model files.")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without running generation (default when --run is absent).")

    model_group = parser.add_mutually_exclusive_group()
    model_group.add_argument("--mega", dest="mega", action="store_true", help="Use Mega model settings.")
    model_group.add_argument("--no-mega", dest="mega", action="store_false", help="Use Mini model settings (default).")
    parser.set_defaults(mega=False)

    parser.add_argument("--fp16", action="store_true", help="Shortcut for --dtype float16.")
    parser.add_argument("--dtype", choices=["float32", "float16", "bfloat16"], default="float32", help="Torch dtype; --fp16 overrides this to float16.")
    parser.add_argument("--device", default="auto", help="auto, cpu, cuda, cuda:0, or another torch device after separate validation.")
    parser.add_argument("--text", default="Dali painting of WALL-E", help="Prompt text.")
    parser.add_argument("--seed", type=int, default=-1, help="Positive seeds enable torch.manual_seed.")
    parser.add_argument("--grid-size", type=int, default=1, help="Number of images per side.")
    parser.add_argument("--image-path", default="generated", help="Output .png path, or directory receiving generated.png.")
    parser.add_argument("--models-root", default="pretrained", help="Model asset cache root.")
    parser.add_argument("--top-k", type=int, default=256, help="Top-k token sampling value; source script used --top_k.")
    parser.add_argument("--temperature", type=float, default=1.0, help="Positive sampling temperature.")
    parser.add_argument("--supercondition-factor", type=float, default=16.0, help="Prompt guidance factor.")
    parser.add_argument("--seamless", action="store_true", help="Tile in token space before detokenization.")
    parser.add_argument("--ascii-size", type=int, default=128, help="Width for ASCII preview after --run.")
    return parser


def resolved_image_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_dir():
        return path / "generated.png"
    if path.suffix.lower() != ".png":
        return Path(str(path) + ".png")
    return path


def ascii_from_image(image, size: int = 128) -> str:
    if size < 8:
        size = 8
    gray_pixels = image.resize((size, int(0.55 * size))).convert("L").getdata()
    chars = [ASCII_CHARS[i * len(ASCII_CHARS) // 256] for i in gray_pixels]
    rows = [chars[i * size : (i + 1) * size] for i in range(max(1, int(0.55 * size)))]
    return "\n".join("".join(row) for row in rows)


def validate(args: argparse.Namespace) -> None:
    if args.fp16:
        args.dtype = "float16"
    if args.grid_size < 1:
        raise SystemExit("--grid-size must be >= 1")
    if not (1 <= args.top_k <= 16384):
        raise SystemExit("--top-k must be in 1..16384")
    if args.temperature <= 0:
        raise SystemExit("--temperature must be > 0")
    args.device_for_constructor = None if args.device == "auto" else args.device


def plan(args: argparse.Namespace) -> dict:
    return {
        "will_run": bool(args.run),
        "constructor": {
            "models_root": args.models_root,
            "is_mega": args.mega,
            "is_reusable": False,
            "is_verbose": True,
            "device": args.device_for_constructor,
            "dtype": f"torch.{args.dtype}",
        },
        "generate_image": {
            "text": args.text,
            "seed": args.seed,
            "grid_size": args.grid_size,
            "top_k": args.top_k,
            "temperature": args.temperature,
            "supercondition_factor": args.supercondition_factor,
            "is_seamless": args.seamless,
            "is_verbose": True,
        },
        "output_path": str(resolved_image_path(args.image_path)),
        "warnings": [
            "--run may download tokenizer/model weights and perform expensive inference.",
            "Default model variant matches the source CLI: --no-mega unless --mega is passed.",
            "Use --device cpu --dtype float32 for a portable smoke; use CUDA only with a CUDA PyTorch build.",
        ],
    }


def torch_dtype(name: str):
    import torch

    return {
        "float32": torch.float32,
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
    }[name]


def run(args: argparse.Namespace) -> None:
    try:
        import torch
        from min_dalle import MinDalle
    except ImportError as exc:
        raise SystemExit(f"Cannot import min_dalle runtime dependency: {exc}. Install min-dalle with torch, pillow, numpy, requests, and emoji first.")

    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but torch.cuda.is_available() is False. Use --device cpu/auto or install CUDA-enabled PyTorch.")
    if args.device == "cpu" and args.dtype != "float32":
        print("warning: low-precision CPU generation may fail or be slow; float32 is safer", file=sys.stderr)

    model = MinDalle(
        is_mega=args.mega,
        models_root=args.models_root,
        is_reusable=False,
        is_verbose=True,
        dtype=torch_dtype(args.dtype),
        device=args.device_for_constructor,
    )
    image = model.generate_image(
        text=args.text,
        seed=args.seed,
        grid_size=args.grid_size,
        top_k=args.top_k,
        temperature=args.temperature,
        supercondition_factor=args.supercondition_factor,
        is_seamless=args.seamless,
        is_verbose=True,
    )
    output_path = resolved_image_path(args.image_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print("saving image to", output_path)
    image.save(output_path)
    print(ascii_from_image(image, size=args.ascii_size))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate(args)
    print(json.dumps(plan(args), indent=2, sort_keys=True))
    if not args.run:
        print("dry run only; add --run to construct MinDalle and generate an image")
        return 0
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
