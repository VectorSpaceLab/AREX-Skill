#!/usr/bin/env python3
"""Bundled ICEdit inference helper for normal and MoE CLI flows.

This script merges the normal and MoE CLI behavior into one mode-flagged entry point.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROMPT_PREFIX = (
    "A diptych with two side-by-side images of the same scene. On the right, the scene is exactly the same as on the left but "
)
DEFAULT_FLUX_PATH = "black-forest-labs/flux.1-fill-dev"
DEFAULT_NORMAL_LORA = "RiverZ/normal-lora"
DEFAULT_MOE_LORA = "sanaka87/ICEdit-MoE-LoRA"
VENDORED_PACKAGE_NAME = "icedit"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run ICEdit single-image editing from the CLI."
    )
    parser.add_argument(
        "--mode",
        choices=("normal", "moe"),
        default="normal",
        help="Select the standard LoRA path or the MoE variant.",
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Path to the source image to edit.",
    )
    parser.add_argument(
        "--instruction",
        required=True,
        help="Edit instruction. The helper prepends the fixed diptych prompt template automatically.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used for the torch generator.",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory where the edited image is written.",
    )
    parser.add_argument(
        "--output-name",
        default=None,
        help="Optional output filename inside output-dir. Defaults to the input basename.",
    )
    parser.add_argument(
        "--flux-path",
        default=DEFAULT_FLUX_PATH,
        help="Flux.1-fill-dev model id or local directory.",
    )
    parser.add_argument(
        "--lora-path",
        default=None,
        help="LoRA model id or local directory. If omitted, a mode-specific default is used.",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Checkout root that contains the vendored icedit/ package for MoE mode.",
    )
    parser.add_argument(
        "--enable-model-cpu-offload",
        action="store_true",
        help="Use accelerate CPU offload instead of moving the full pipeline to cuda.",
    )
    parser.add_argument(
        "--guidance-scale",
        type=float,
        default=50.0,
        help="Guidance scale passed to FluxFillPipeline.",
    )
    parser.add_argument(
        "--num-inference-steps",
        type=int,
        default=28,
        help="Number of denoising steps.",
    )
    return parser


def resolve_vendored_root(repo_root_arg: str | None) -> Path | None:
    candidates = []
    if repo_root_arg:
        candidates.append(Path(repo_root_arg))
    env_root = os.environ.get("ICEDIT_REPO_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.append(Path.cwd())

    for candidate in candidates:
        expanded = candidate.expanduser()
        if not expanded.is_dir():
            continue
        if expanded.name == VENDORED_PACKAGE_NAME and (expanded / "diffusers").is_dir():
            return expanded
        nested = expanded / VENDORED_PACKAGE_NAME
        if nested.is_dir() and (nested / "diffusers").is_dir():
            return nested
    return None


def install_vendored_package(mode: str, repo_root_arg: str | None) -> Path | None:
    if mode != "moe":
        return None

    vendor_root = resolve_vendored_root(repo_root_arg)
    if vendor_root is None:
        raise SystemExit(
            "MoE mode requires a checkout root that contains the vendored icedit/ package. "
            "Pass --repo-root /path/to/ICEdit-checkout, export ICEDIT_REPO_ROOT, or switch to --mode normal."
        )

    vendor_root_str = str(vendor_root)
    if vendor_root_str not in sys.path:
        sys.path.insert(0, vendor_root_str)
    return vendor_root


def choose_lora_path(mode: str, lora_path_arg: str | None) -> str:
    if lora_path_arg:
        return lora_path_arg
    return DEFAULT_MOE_LORA if mode == "moe" else DEFAULT_NORMAL_LORA


def resample_filter(image_module):
    try:
        return image_module.Resampling.LANCZOS
    except AttributeError:
        return image_module.LANCZOS


def normalize_width(image_module, image):
    if image.width == 512:
        return image

    scale = 512 / image.width
    new_height = int(image.height * scale)
    new_height = max(8, (new_height // 8) * 8)
    print(
        f"[ICEdit] Input width {image.width} is not 512; resizing to 512 x {new_height}. "
        "The helper always normalizes width automatically."
    )
    return image.resize((512, new_height), resample=resample_filter(image_module))


def make_diptych(np_module, image_module, image):
    width, height = image.size
    combined = image_module.new("RGB", (width * 2, height))
    combined.paste(image, (0, 0))
    combined.paste(image, (width, 0))
    mask_array = np_module.zeros((height, width * 2), dtype=np_module.uint8)
    mask_array[:, width:] = 255
    mask = image_module.fromarray(mask_array)
    return combined, mask, width, height


def main() -> None:
    args = build_parser().parse_args()
    vendor_root = install_vendored_package(args.mode, args.repo_root)

    try:
        import torch
    except ImportError as exc:
        raise SystemExit(
            "PyTorch is not installed. Install the ICEdit requirements first."
        ) from exc

    if not torch.cuda.is_available():
        raise SystemExit(
            "CUDA is not available. ICEdit inference expects a CUDA-enabled torch wheel and an NVIDIA GPU. "
            "Install a CUDA build such as torch==2.7.0+cu126 and rerun on a GPU host."
        )

    if vendor_root is not None:
        print(f"[ICEdit] Using vendored diffusers from {vendor_root}")

    try:
        from diffusers import FluxFillPipeline
    except ImportError as exc:
        raise SystemExit(
            "diffusers is not installed or could not be imported. Install the ICEdit requirements first."
        ) from exc

    import numpy as np
    from PIL import Image

    lora_path = choose_lora_path(args.mode, args.lora_path)
    print(f"[ICEdit] Mode: {args.mode}")
    print(f"[ICEdit] Flux path: {args.flux_path}")
    print(f"[ICEdit] LoRA path: {lora_path}")

    with Image.open(args.image) as src_image:
        image = src_image.convert("RGB")

    image = normalize_width(Image, image)

    instruction = args.instruction.strip()
    prompt = PROMPT_PREFIX + instruction
    print(f"[ICEdit] Instruction: {instruction}")
    print("[ICEdit] Prompt template prepended automatically.")

    combined_image, mask_image, width, height = make_diptych(np, Image, image)

    pipe = FluxFillPipeline.from_pretrained(args.flux_path, torch_dtype=torch.bfloat16)
    pipe.load_lora_weights(lora_path)

    if args.enable_model_cpu_offload:
        print(
            "[ICEdit] CPU offload enabled; expect slower inference and use this on lower-VRAM CUDA machines."
        )
        pipe.enable_model_cpu_offload()
    else:
        pipe = pipe.to("cuda")

    result_image = pipe(
        prompt=prompt,
        image=combined_image,
        mask_image=mask_image,
        height=height,
        width=width * 2,
        guidance_scale=args.guidance_scale,
        num_inference_steps=args.num_inference_steps,
        generator=torch.Generator(device="cpu").manual_seed(args.seed)
        if args.seed is not None
        else None,
    ).images[0]

    result_image = result_image.crop((width, 0, width * 2, height))

    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    output_name = Path(args.output_name).name if args.output_name else Path(args.image).name
    output_path = output_dir / output_name
    if output_path.suffix == "":
        output_path = output_path.with_suffix(Path(args.image).suffix)

    result_image.save(output_path)
    print(f"[ICEdit] Result saved as {output_path.resolve()}")


if __name__ == "__main__":
    main()
