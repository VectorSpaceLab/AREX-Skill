#!/usr/bin/env python3
"""Run Zero123Plus v1.1 depth-ControlNet generation.

Local-only loading is the default. The checked-in diffusers-support custom
pipeline is loaded directly from the repository, and model downloads stay
opt-in via --allow-download.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

DEFAULT_MODEL_ID = "sudo-ai/zero123plus-v1.1"
DEFAULT_CONTROLNET_ID = "sudo-ai/controlnet-zp11-depth-v1"
DEFAULT_CUSTOM_PIPELINE = str(Path(__file__).resolve().parents[6] / "diffusers-support")
DEFAULT_OUTPUT = "output.png"
DEFAULT_NUM_IMAGES_PER_PROMPT = 1
DEFAULT_GUIDANCE_SCALE = 4.0
DEFAULT_NUM_INFERENCE_STEPS = 36
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 960
DEFAULT_CONDITIONING_SCALE = 0.75


def _require_module(module_name: str, install_hint: str):
    try:
        return importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(install_hint) from exc


def _load_pil_image(path: Path):
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("Missing Pillow. Install pillow to read images.") from exc

    if not path.is_file():
        raise FileNotFoundError(f"Input image not found: {path}")
    with Image.open(path) as image:
        loaded = image.copy()
    if loaded.mode not in {"RGB", "RGBA"}:
        loaded = loaded.convert("RGBA" if "A" in loaded.getbands() else "RGB")
    return loaded


def _square_pad(image):
    from PIL import Image

    if image.width == image.height:
        return image, False
    side = max(image.width, image.height)
    fill = (127, 127, 127, 0) if image.mode == "RGBA" else (127, 127, 127)
    canvas = Image.new(image.mode, (side, side), fill)
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    return canvas, True


def _resolve_device(requested: str, torch_mod):
    requested = requested.lower()
    if requested == "auto":
        if torch_mod.cuda.is_available():
            return "cuda:0", torch_mod.float16
        return "cpu", torch_mod.float32
    if requested == "cpu":
        return "cpu", torch_mod.float32
    if requested == "cuda":
        if not torch_mod.cuda.is_available():
            raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false.")
        return "cuda:0", torch_mod.float16
    if requested.startswith("cuda:"):
        if not torch_mod.cuda.is_available():
            raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false.")
        return requested, torch_mod.float16
    raise ValueError("--device must be auto, cpu, cuda, or a cuda:N device string.")


def _load_pipeline(model_id: str, controlnet_id: str, custom_pipeline: str, allow_download: bool, device: str, dtype, conditioning_scale: float):
    _require_module(
        "torch",
        "Missing torch. Install a CUDA-capable PyTorch build for real generation.",
    )
    _require_module("diffusers", "Missing diffusers. Install diffusers==0.20.2.")
    _require_module("transformers", "Missing transformers. Install transformers==4.29.2.")
    from diffusers import ControlNetModel, DiffusionPipeline, EulerAncestralDiscreteScheduler

    try:
        pipeline = DiffusionPipeline.from_pretrained(
            model_id,
            custom_pipeline=custom_pipeline,
            torch_dtype=dtype,
            local_files_only=not allow_download,
        )
    except Exception as exc:
        if allow_download:
            raise RuntimeError(
                f"Failed to load {model_id!r} with custom pipeline {custom_pipeline!r}. "
                "Check network access, cache permissions, and Hugging Face authentication."
            ) from exc
        raise RuntimeError(
            f"Local cache miss for {model_id!r} or custom pipeline {custom_pipeline!r}. Re-run with --allow-download or pre-populate the cache."
        ) from exc

    try:
        controlnet = ControlNetModel.from_pretrained(
            controlnet_id,
            torch_dtype=dtype,
            local_files_only=not allow_download,
        )
    except Exception as exc:
        if allow_download:
            raise RuntimeError(
                f"Failed to load ControlNet weights {controlnet_id!r}. Check network access and cache permissions."
            ) from exc
        raise RuntimeError(
            f"Local cache miss for ControlNet weights {controlnet_id!r}. Re-run with --allow-download or cache the model first."
        ) from exc

    pipeline.add_controlnet(controlnet, conditioning_scale=conditioning_scale)
    pipeline.scheduler = EulerAncestralDiscreteScheduler.from_config(
        pipeline.scheduler.config,
        timestep_spacing="trailing",
    )
    pipeline.to(device)
    return pipeline


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a Zero123Plus multiview atlas with the v1.1 depth ControlNet.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input_image",
        nargs="?",
        type=Path,
        help="Path to the conditioning image.",
    )
    parser.add_argument(
        "--input-image",
        dest="input_image_flag",
        type=Path,
        help="Path to the conditioning image.",
    )
    parser.add_argument("--depth-image", type=Path, required=True, help="Path to the depth control image.")
    parser.add_argument("--output", type=Path, default=Path(DEFAULT_OUTPUT), help="Path for the generated atlas.")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID, help="Diffusers base model id to load.")
    parser.add_argument("--controlnet-id", default=DEFAULT_CONTROLNET_ID, help="Diffusers ControlNet id to load.")
    parser.add_argument(
        "--custom-pipeline",
        default=DEFAULT_CUSTOM_PIPELINE,
        help="Diffusers custom-pipeline id or local pipeline source to use.",
    )
    parser.add_argument(
        "--conditioning-scale",
        type=float,
        default=DEFAULT_CONDITIONING_SCALE,
        help="ControlNet conditioning strength.",
    )
    parser.add_argument("--steps", type=int, default=DEFAULT_NUM_INFERENCE_STEPS, help="Number of diffusion steps to use.")
    parser.add_argument(
        "--guidance-scale",
        type=float,
        default=DEFAULT_GUIDANCE_SCALE,
        help="Classifier-free guidance scale.",
    )
    parser.add_argument(
        "--device",
        default="auto",
        help="Device to use: auto, cpu, cuda, or a specific cuda:N index.",
    )
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="Allow Hugging Face model downloads when the cache is incomplete.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate paths and show the planned configuration without loading the model.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    input_path = args.input_image_flag or args.input_image
    if input_path is None:
        parser.error("an input image is required (pass it positionally or with --input-image)")

    if args.dry_run:
        print("Zero123Plus depth dry run")
        print(f"- input image: {input_path}")
        print(f"- depth image: {args.depth_image}")
        print(f"- output: {args.output}")
        print(f"- base model: {args.model_id}")
        print(f"- controlnet: {args.controlnet_id}")
        print(f"- custom pipeline: {args.custom_pipeline}")
        print(f"- conditioning scale: {args.conditioning_scale}")
        print(f"- steps: {args.steps}")
        print(f"- guidance scale: {args.guidance_scale}")
        print(f"- device: {args.device} (auto prefers CUDA when available)")
        print(f"- allow downloads: {args.allow_download}")
        return 0

    torch_mod = _require_module(
        "torch",
        "Missing torch. Install a CUDA-capable PyTorch build for real generation.",
    )
    device, dtype = _resolve_device(args.device, torch_mod)
    if device == "cpu":
        print(
            "Warning: CPU mode is only a debugging fallback and is not a full substitute for real generation.",
            file=sys.stderr,
        )

    image = _load_pil_image(input_path)
    image, changed = _square_pad(image)
    if changed:
        print(
            f"Center-padded {input_path} to {image.size[0]}x{image.size[1]} so the input is square.",
            file=sys.stderr,
        )
    if min(image.size) < 320:
        print(
            "Warning: the input is smaller than the recommended 320x320 minimum.",
            file=sys.stderr,
        )

    depth = _load_pil_image(args.depth_image)
    depth, depth_changed = _square_pad(depth)
    if depth_changed:
        print(
            f"Center-padded {args.depth_image} to {depth.size[0]}x{depth.size[1]} so the depth map is square.",
            file=sys.stderr,
        )
    if depth.size != image.size:
        raise ValueError(
            f"Depth image must match the conditioning image after square padding, got {depth.size} and {image.size}."
        )

    pipeline = _load_pipeline(
        args.model_id,
        args.controlnet_id,
        args.custom_pipeline,
        args.allow_download,
        device,
        dtype,
        args.conditioning_scale,
    )
    result = pipeline(
        image=image,
        prompt="",
        depth_image=depth,
        num_images_per_prompt=DEFAULT_NUM_IMAGES_PER_PROMPT,
        guidance_scale=args.guidance_scale,
        output_type="pil",
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
        num_inference_steps=args.steps,
    ).images[0]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.save(args.output)
    print(f"Saved depth-conditioned atlas to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
