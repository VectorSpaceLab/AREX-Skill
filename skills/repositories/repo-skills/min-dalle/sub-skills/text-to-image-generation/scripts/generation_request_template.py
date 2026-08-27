#!/usr/bin/env python3
"""
Safe min(DALL·E) generation request template.

Default behavior is a dry run: it prints the planned MinDalle constructor and
method call without importing min_dalle, constructing a model, downloading
weights, or running inference. Add --run only after model-cache, network,
device, and memory preconditions are acceptable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan or run a min(DALL·E) text-to-image request safely.")
    run_group = parser.add_mutually_exclusive_group()
    run_group.add_argument("--dry-run", dest="run", action="store_false", help="Print the planned call without importing min_dalle or downloading assets (default).")
    run_group.add_argument("--run", dest="run", action="store_true", help="Construct MinDalle and run generation; may download large model assets.")
    parser.set_defaults(run=False)

    parser.add_argument("--text", default="Dali painting of WALL-E", help="Prompt text.")
    parser.add_argument("--models-root", default="pretrained", help="Directory containing or receiving min-dalle model assets.")
    parser.add_argument("--output-dir", default="generated", help="Directory for generated image files when --run is used.")
    parser.add_argument("--image-name", default="generated", help="Base filename without extension for generated images.")
    parser.add_argument("--grid-size", type=int, default=1, help="Number of images per side; total images are grid_size squared.")
    parser.add_argument("--seed", type=int, default=-1, help="Positive seeds call torch.manual_seed; 0 or negative values leave sampling random.")
    parser.add_argument("--top-k", type=int, default=256, help="Keep the top-k image token logits before sampling; valid range is 1..16384.")
    parser.add_argument("--temperature", type=float, default=1.0, help="Positive sampling temperature.")
    parser.add_argument("--supercondition-factor", type=float, default=16.0, help="Prompt-conditioning guidance factor.")
    parser.add_argument("--seamless", action="store_true", help="Tile in token space before detokenization.")

    model_group = parser.add_mutually_exclusive_group()
    model_group.add_argument("--mega", dest="mega", action="store_true", default=True, help="Use DALL·E Mega weights/settings (default).")
    model_group.add_argument("--no-mega", dest="mega", action="store_false", help="Use smaller Mini weights/settings.")

    reuse_group = parser.add_mutually_exclusive_group()
    reuse_group.add_argument("--reusable", dest="reusable", action="store_true", default=True, help="Keep encoder/decoder/detokenizer resident for repeated prompts (default).")
    reuse_group.add_argument("--non-reusable", dest="reusable", action="store_false", help="Load/delete major modules across phases to reduce residency for one-shot runs.")

    parser.add_argument("--device", default="auto", help="auto, cpu, cuda, or cuda:N.")
    parser.add_argument("--dtype", choices=["float32", "float16", "bfloat16"], default="float32", help="Torch dtype for model/autocast.")
    parser.add_argument("--progressive-outputs", action="store_true", help="Use stream APIs and save intermediate frames.")
    parser.add_argument("--tensor-output", action="store_true", help="Save individual 256x256 images from generate_images* tensor batches instead of a PIL grid.")
    return parser


def normalize_args(args: argparse.Namespace) -> None:
    if args.grid_size < 1:
        raise SystemExit("--grid-size must be >= 1")
    if not (1 <= args.top_k <= 16384):
        raise SystemExit("--top-k must be in 1..16384 for min-dalle image-token sampling")
    if args.temperature <= 0:
        raise SystemExit("--temperature must be > 0")
    args.dry_run = not args.run
    if args.device == "auto":
        args.device_for_constructor = None
    else:
        args.device_for_constructor = args.device


def plan_dict(args: argparse.Namespace) -> dict[str, Any]:
    method = "generate_images_stream" if args.tensor_output and args.progressive_outputs else \
        "generate_images" if args.tensor_output else \
        "generate_image_stream" if args.progressive_outputs else \
        "generate_image"
    return {
        "will_run": bool(args.run),
        "constructor": {
            "models_root": args.models_root,
            "dtype": f"torch.{args.dtype}",
            "device": args.device_for_constructor if args.device_for_constructor is not None else None,
            "is_mega": args.mega,
            "is_reusable": args.reusable,
            "is_verbose": True,
        },
        "method": method,
        "generation_kwargs": {
            "text": args.text,
            "seed": args.seed,
            "grid_size": args.grid_size,
            "is_seamless": args.seamless,
            "temperature": args.temperature,
            "top_k": args.top_k,
            "supercondition_factor": args.supercondition_factor,
            "is_verbose": True,
            "progressive_outputs": args.progressive_outputs,
        },
        "outputs": {
            "output_dir": args.output_dir,
            "image_name": args.image_name,
            "tensor_output": args.tensor_output,
        },
        "warnings": [
            "Constructing MinDalle initializes tokenizer assets and may contact the model host.",
            "Running generation can download large .pt files and consume substantial CPU/GPU memory.",
            "Use grid_size=1 and --no-mega for the smallest full-generation smoke.",
            "Use float32 on CPU unless a separate runtime check proves lower precision is safe.",
        ],
    }


def torch_dtype(dtype_name: str):
    import torch

    try:
        return {
            "float32": torch.float32,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
        }[dtype_name]
    except (AttributeError, KeyError) as exc:
        raise SystemExit(f"Invalid --dtype {dtype_name!r}; use float32, float16, or bfloat16 with a PyTorch build that exposes it.") from exc


def resolve_device(device_arg: str, torch):
    if device_arg == "auto":
        return None
    try:
        device = torch.device(device_arg)
    except Exception as exc:
        raise SystemExit(f"Invalid --device {device_arg!r}: {exc}. Use auto, cpu, cuda, or cuda:N.") from exc
    if device.type not in {"cpu", "cuda"}:
        raise SystemExit(f"Invalid --device {device_arg!r}: min-dalle generation is verified for cpu and cuda only.")
    if device.type == "cuda":
        if not torch.cuda.is_available():
            raise SystemExit("CUDA was requested but torch.cuda.is_available() is False. Use --device cpu/auto or install a CUDA-enabled PyTorch build.")
        if device.index is not None and device.index >= torch.cuda.device_count():
            raise SystemExit(f"CUDA device index {device.index} is unavailable; torch sees {torch.cuda.device_count()} device(s).")
    return device_arg


def save_pil(image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    print(f"saved {path}")


def save_tensor_batch(batch, output_dir: Path, image_name: str, step: int | None = None) -> None:
    from PIL import Image
    import torch

    output_dir.mkdir(parents=True, exist_ok=True)
    for i, image_tensor in enumerate(batch):
        array = image_tensor.detach().clamp(0, 255).to(torch.uint8).cpu().numpy()
        suffix = f"_step_{step:03d}_{i:02d}" if step is not None else f"_{i:02d}"
        path = output_dir / f"{image_name}{suffix}.png"
        Image.fromarray(array).save(path)
        print(f"saved {path}")


def run_generation(args: argparse.Namespace) -> None:
    try:
        import torch
    except ImportError as exc:
        raise SystemExit("Cannot import torch. Install a PyTorch build for the target CPU/GPU environment before --run.") from exc

    resolved_device = resolve_device(args.device, torch)
    dtype = torch_dtype(args.dtype)
    if args.device == "cpu" and args.dtype in {"float16", "bfloat16"}:
        print("warning: float16/bfloat16 on CPU may be unsupported or slow; float32 is safer", file=sys.stderr)

    try:
        from min_dalle import MinDalle
    except ImportError as exc:
        raise SystemExit(f"Cannot import min_dalle runtime dependency: {exc}. Install min-dalle with torch, pillow, numpy, requests, and emoji first.") from exc

    model = MinDalle(
        models_root=args.models_root,
        dtype=dtype,
        device=resolved_device,
        is_mega=args.mega,
        is_reusable=args.reusable,
        is_verbose=True,
    )
    generation_kwargs = dict(
        text=args.text,
        seed=args.seed,
        grid_size=args.grid_size,
        is_seamless=args.seamless,
        temperature=args.temperature,
        top_k=args.top_k,
        supercondition_factor=args.supercondition_factor,
        is_verbose=True,
    )
    output_dir = Path(args.output_dir)

    if args.tensor_output:
        if args.progressive_outputs:
            for step, batch in enumerate(model.generate_images_stream(**generation_kwargs, progressive_outputs=True), start=1):
                save_tensor_batch(batch, output_dir, args.image_name, step=step)
        else:
            batch = model.generate_images(**generation_kwargs)
            save_tensor_batch(batch, output_dir, args.image_name)
    else:
        if args.progressive_outputs:
            for step, image in enumerate(model.generate_image_stream(**generation_kwargs, progressive_outputs=True), start=1):
                save_pil(image, output_dir / f"{args.image_name}_step_{step:03d}.png")
        else:
            image = model.generate_image(**generation_kwargs)
            save_pil(image, output_dir / f"{args.image_name}.png")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    normalize_args(args)
    print(json.dumps(plan_dict(args), indent=2, sort_keys=True))
    if not args.run:
        print("dry run only; add --run to construct MinDalle and generate images")
        return 0
    run_generation(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
