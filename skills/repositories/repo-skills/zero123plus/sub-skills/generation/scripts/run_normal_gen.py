#!/usr/bin/env python3
"""Zero123Plus v1.2 normal generator.

Purpose
    Run the v1.2 Zero123Plus base model, then the v1.2 normal ControlNet, and
    optionally postprocess the paired outputs with the bundled matting helper.

Prerequisites
    - torch
    - torchvision
    - diffusers==0.20.2
    - transformers==4.29.2
    - pillow
    - numpy, pymatting, scipy (only if postprocess is enabled)

Example
    python ./scripts/run_normal_gen.py \
      --input-image ./input.png \
      --color-output ./outputs/colors.png \
      --normal-output ./outputs/normals.png \
      --steps 75 \
      --guidance-scale 4.0
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import sys
from pathlib import Path

DEFAULT_MODEL_ID = "sudo-ai/zero123plus-v1.2"
DEFAULT_CONTROLNET_ID = "sudo-ai/controlnet-zp12-normal-gen-v1"
DEFAULT_CUSTOM_PIPELINE = str(Path(__file__).resolve().parents[6] / "diffusers-support")
DEFAULT_STEPS = 75
DEFAULT_GUIDANCE_SCALE = 4.0
DEFAULT_CONDITIONING_SCALE = 1.0
DEFAULT_NUM_IMAGES_PER_PROMPT = 1
MAX_INPUT_SIDE = 1280
OUTPUT_WIDTH = 640
OUTPUT_HEIGHT = 960
ALPHA_OUTPUT_SUFFIXES = {".png", ".webp", ".tif", ".tiff"}
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _require_module(module_name: str, install_hint: str) -> None:
    if not _module_available(module_name):
        raise ImportError(f"Missing required dependency '{module_name}'. Install it with: {install_hint}")


def _warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def _load_pil():
    _require_module("PIL", "pip install pillow")
    from PIL import Image, ImageOps

    return Image, ImageOps


def _load_generation_stack():
    _require_module("torch", "pip install torch torchvision")
    _require_module("torchvision", "pip install torch torchvision")
    _require_module("diffusers", "pip install diffusers==0.20.2 transformers==4.29.2")
    _require_module("transformers", "pip install diffusers==0.20.2 transformers==4.29.2")
    import torch
    from diffusers import ControlNetModel, DiffusionPipeline, EulerAncestralDiscreteScheduler

    return torch, ControlNetModel, DiffusionPipeline, EulerAncestralDiscreteScheduler


def _resolve_device(requested_device: str, torch):
    choice = requested_device.strip().lower()
    if choice == "auto":
        if torch.cuda.is_available():
            return "cuda:0", torch.float16
        _warn("CUDA is not available; running on CPU float32 for inspection only. This is not a full substitute for real generation.")
        return "cpu", torch.float32
    if choice == "cpu":
        _warn("CPU float32 was selected; generation will be much slower and is only a debug fallback.")
        return "cpu", torch.float32
    if choice.startswith("cuda"):
        if not torch.cuda.is_available():
            raise RuntimeError(f"CUDA was requested via --device {requested_device!r}, but no CUDA device is available in this runtime.")
        return ("cuda:0" if choice == "cuda" else requested_device), torch.float16
    raise ValueError(f"Unsupported --device value {requested_device!r}. Use auto, cpu, or cuda[:index].")


def _resample_filter(Image):
    resampling = getattr(Image, "Resampling", None)
    return resampling.LANCZOS if resampling is not None else Image.LANCZOS


def _pad_to_square(image, background=(127, 127, 127)):
    from PIL import Image

    if image.width == image.height:
        return image
    side = max(image.width, image.height)
    canvas = Image.new("RGB", (side, side), background)
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    return canvas


def _prepare_input_image(path: Path):
    Image, ImageOps = _load_pil()
    if not path.exists():
        raise FileNotFoundError(f"Input image not found: {path}")
    with Image.open(path) as img:
        image = ImageOps.exif_transpose(img)
        if image.mode == "RGBA":
            background = Image.new("RGBA", image.size, (127, 127, 127, 255))
            background.paste(image, mask=image.getchannel("A"))
            image = background.convert("RGB")
        else:
            image = image.convert("RGB")
    if max(image.size) > MAX_INPUT_SIDE:
        scale = MAX_INPUT_SIDE / float(max(image.size))
        image = image.resize((round(image.width * scale), round(image.height * scale)), _resample_filter(Image))
    return _pad_to_square(image)


def _load_base_pipeline(model_id: str, allow_download: bool, dtype):
    _, _, DiffusionPipeline, EulerAncestralDiscreteScheduler = _load_generation_stack()
    try:
        pipeline = DiffusionPipeline.from_pretrained(
            model_id,
            custom_pipeline=DEFAULT_CUSTOM_PIPELINE,
            torch_dtype=dtype,
            local_files_only=not allow_download,
        )
    except Exception as exc:
        if not allow_download:
            raise RuntimeError(
                f"Could not load model {model_id!r} with custom pipeline {DEFAULT_CUSTOM_PIPELINE!r} from the local cache. Downloads are disabled by default; pre-populate the Hugging Face cache or rerun with --allow-download after approval."
            ) from exc
        raise RuntimeError(
            f"Failed to load the Zero123Plus base model {model_id!r}. Check the model id, custom pipeline, and network access."
        ) from exc

    try:
        pipeline.scheduler = EulerAncestralDiscreteScheduler.from_config(pipeline.scheduler.config, timestep_spacing="trailing")
    except TypeError:
        pipeline.scheduler = EulerAncestralDiscreteScheduler.from_config(pipeline.scheduler.config)
    return pipeline


def _load_controlnet(controlnet_id: str, allow_download: bool, dtype, ControlNetModel):
    try:
        return ControlNetModel.from_pretrained(
            controlnet_id,
            torch_dtype=dtype,
            local_files_only=not allow_download,
        )
    except Exception as exc:
        if not allow_download:
            raise RuntimeError(
                f"Could not load ControlNet {controlnet_id!r} from the local cache. Downloads are disabled by default; pre-populate the cache or rerun with --allow-download after approval."
            ) from exc
        raise RuntimeError(
            f"Failed to load the normal ControlNet {controlnet_id!r}. Check the model id, custom cache, and network access."
        ) from exc


def _load_postprocess():
    try:
        from matting_postprocess import postprocess
    except ImportError as exc:
        raise ImportError(
            "Could not import the bundled matting_postprocess helper. Install numpy/pillow if needed, or rerun with --skip-postprocess."
        ) from exc
    return postprocess


def _ensure_alpha_output(image, output_path: Path) -> None:
    if image.mode in {"RGBA", "LA"} and output_path.suffix.lower() not in ALPHA_OUTPUT_SUFFIXES:
        raise ValueError(f"The output path {str(output_path)!r} does not support alpha storage. Use a PNG, WEBP, TIF, or TIFF path when saving the postprocessed color image.")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the Zero123Plus v1.2 normal generator and optional matting helper.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input-image", type=Path, required=True, help="Path to the conditioning image.")
    parser.add_argument("--color-output", type=Path, required=True, help="Path where the color output should be saved.")
    parser.add_argument("--normal-output", type=Path, required=True, help="Path where the normal output should be saved.")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID, help="Diffusers model id or local directory. Default: sudo-ai/zero123plus-v1.2")
    parser.add_argument("--controlnet-id", default=DEFAULT_CONTROLNET_ID, help="Normal ControlNet id or local directory. Default: sudo-ai/controlnet-zp12-normal-gen-v1")
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS, help="Number of diffusion steps.")
    parser.add_argument("--guidance-scale", type=float, default=DEFAULT_GUIDANCE_SCALE, help="Classifier-free guidance scale.")
    parser.add_argument("--device", default="auto", help="Device selection: auto, cpu, or cuda[:index]. Default: auto.")
    parser.add_argument("--allow-download", action="store_true", help="Allow Hugging Face checkpoint downloads instead of local-only loading.")
    parser.add_argument("--skip-postprocess", action="store_true", help="Save the raw color and normal grids without calling the bundled matting helper.")
    parser.add_argument("--dry-run", action="store_true", help="Print the planned configuration and exit without loading models or saving outputs.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.dry_run:
        print("Zero123Plus normal dry run")
        print(f"- input image: {args.input_image}")
        print(f"- color output: {args.color_output}")
        print(f"- normal output: {args.normal_output}")
        print(f"- base model: {args.model_id}")
        print(f"- controlnet: {args.controlnet_id}")
        print(f"- custom pipeline: {DEFAULT_CUSTOM_PIPELINE}")
        print(f"- steps: {args.steps}")
        print(f"- guidance scale: {args.guidance_scale}")
        print(f"- device: {args.device} (auto prefers CUDA when available)")
        print(f"- allow downloads: {args.allow_download}")
        print(f"- skip postprocess: {args.skip_postprocess}")
        return 0

    Image, _ = _load_pil()
    torch, ControlNetModel, _, _ = _load_generation_stack()
    device, dtype = _resolve_device(args.device, torch)

    base_pipeline = _load_base_pipeline(args.model_id, args.allow_download, dtype)
    normal_pipeline = copy.copy(base_pipeline)
    controlnet = _load_controlnet(args.controlnet_id, args.allow_download, dtype, ControlNetModel)
    normal_pipeline.add_controlnet(controlnet, conditioning_scale=DEFAULT_CONDITIONING_SCALE)
    base_pipeline.to(device, dtype)
    normal_pipeline.to(device, dtype)

    conditioned = _prepare_input_image(args.input_image)
    color_grid = base_pipeline(
        image=conditioned,
        prompt="",
        num_images_per_prompt=DEFAULT_NUM_IMAGES_PER_PROMPT,
        guidance_scale=args.guidance_scale,
        output_type="pil",
        width=OUTPUT_WIDTH,
        height=OUTPUT_HEIGHT,
        num_inference_steps=args.steps,
    ).images[0]
    normal_grid = normal_pipeline(
        image=conditioned,
        prompt="",
        depth_image=color_grid,
        num_images_per_prompt=DEFAULT_NUM_IMAGES_PER_PROMPT,
        guidance_scale=args.guidance_scale,
        output_type="pil",
        width=OUTPUT_WIDTH,
        height=OUTPUT_HEIGHT,
        num_inference_steps=args.steps,
    ).images[0]

    if args.skip_postprocess:
        color_output, normal_output = color_grid, normal_grid
    else:
        postprocess = _load_postprocess()
        try:
            color_output, normal_output = postprocess(color_grid, normal_grid)
        except ImportError as exc:
            raise ImportError(f"{exc}\nInstall pymatting and scipy, or rerun with --skip-postprocess to keep the raw grids.") from exc

    _ensure_alpha_output(color_output, args.color_output)
    args.color_output.parent.mkdir(parents=True, exist_ok=True)
    args.normal_output.parent.mkdir(parents=True, exist_ok=True)
    color_output.save(args.color_output)
    normal_output.save(args.normal_output)
    if args.skip_postprocess:
        print(f"Saved raw color grid to {args.color_output}")
        print(f"Saved raw normal grid to {args.normal_output}")
    else:
        print(f"Saved postprocessed color cutout to {args.color_output}")
        print(f"Saved postprocessed normal image to {args.normal_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
