#!/usr/bin/env python3
"""Print a safe Diffusers pipeline invocation skeleton without downloading by default."""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path


PIPELINE_IMPORTS = {
    "auto-text2image": ("AutoPipelineForText2Image", "prompt"),
    "auto-img2img": ("AutoPipelineForImage2Image", "prompt, image=init_image, strength=args.strength"),
    "auto-inpaint": ("AutoPipelineForInpainting", "prompt, image=init_image, mask_image=mask_image"),
    "generic": ("DiffusionPipeline", "prompt"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate pipeline invocation options and print a safe from_pretrained/call skeleton. "
            "The generated skeleton uses local_files_only=True unless --allow-download is set."
        )
    )
    parser.add_argument("--model", required=True, help="Model id or local model directory placeholder for from_pretrained.")
    parser.add_argument(
        "--pipeline",
        choices=sorted(PIPELINE_IMPORTS),
        default="auto-text2image",
        help="Pipeline skeleton family to print.",
    )
    parser.add_argument("--prompt", default="a precise prompt", help="Prompt text to include in the skeleton.")
    parser.add_argument("--negative-prompt", default="", help="Optional negative prompt to include.")
    parser.add_argument("--seed", type=int, default=0, help="Seed for a fresh CPU torch.Generator.")
    parser.add_argument("--steps", type=int, default=25, help="num_inference_steps value; must be positive.")
    parser.add_argument("--strength", type=float, default=0.75, help="Img2img strength; must be between 0 and 1.")
    parser.add_argument("--height", type=int, help="Optional output height; must be positive if set.")
    parser.add_argument("--width", type=int, help="Optional output width; must be positive if set.")
    parser.add_argument("--allow-download", action="store_true", help="Allow generated skeleton to download from model hubs.")
    parser.add_argument(
        "--device-policy",
        choices=["auto", "cpu", "cuda"],
        default="auto",
        help="Device selection policy for the skeleton.",
    )
    parser.add_argument(
        "--with-callback",
        action="store_true",
        help="Include a callback_on_step_end skeleton guarded by the concrete pipeline signature.",
    )
    args = parser.parse_args()

    if args.steps <= 0:
        parser.error("--steps must be positive")
    if not 0.0 <= args.strength <= 1.0:
        parser.error("--strength must be between 0 and 1")
    if args.height is not None and args.height <= 0:
        parser.error("--height must be positive")
    if args.width is not None and args.width <= 0:
        parser.error("--width must be positive")
    if args.seed < 0:
        parser.error("--seed must be nonnegative")

    model_path = Path(args.model)
    looks_local = model_path.exists() or args.model.startswith(('.', '/', '~'))
    if not args.allow_download and not looks_local:
        parser.error("--model must be an existing/local-looking path unless --allow-download is set")

    return args


def quote(value: str) -> str:
    return repr(value)


def main() -> int:
    args = parse_args()
    class_name, call_inputs = PIPELINE_IMPORTS[args.pipeline]
    local_files_only = "False" if args.allow_download else "True"
    negative_prompt_line = f"    negative_prompt={quote(args.negative_prompt)},\n" if args.negative_prompt else ""
    size_lines = ""
    if args.height is not None:
        size_lines += f"    height={args.height},\n"
    if args.width is not None:
        size_lines += f"    width={args.width},\n"

    callback_def = ""
    callback_args = ""
    if args.with_callback:
        callback_def = '''

def on_step_end(pipe, step_index, timestep, callback_kwargs):
    # Keep this callback lightweight; return callback_kwargs after any edits.
    return callback_kwargs
'''
        callback_args = '''
if "callback_on_step_end" in inspect.signature(pipe.__call__).parameters:
    call_kwargs["callback_on_step_end"] = on_step_end
    if "callback_on_step_end_tensor_inputs" in inspect.signature(pipe.__call__).parameters:
        call_kwargs["callback_on_step_end_tensor_inputs"] = ["latents"]
'''

    image_setup = ""
    if args.pipeline in {"auto-img2img", "auto-inpaint"}:
        image_setup += '''
# Provide real local images before running this skeleton.
init_image = Image.open("/path/to/input.png").convert("RGB")
'''
    if args.pipeline == "auto-inpaint":
        image_setup += '''mask_image = Image.open("/path/to/mask.png").convert("RGB")
if init_image.size != mask_image.size:
    raise ValueError(f"image and mask_image must match, got {init_image.size} and {mask_image.size}")
'''

    pil_import = "from PIL import Image\n" if args.pipeline in {"auto-img2img", "auto-inpaint"} else ""
    force_device = "None" if args.device_policy == "auto" else quote(args.device_policy)

    skeleton = f'''\
import inspect
import torch
{pil_import}from diffusers import {class_name}

model_id_or_path = {quote(args.model)}
prompt = {quote(args.prompt)}
forced_device = {force_device}
if forced_device is None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
else:
    if forced_device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")
    device = forced_device
dtype = torch.float16 if device == "cuda" else torch.float32

pipe = {class_name}.from_pretrained(
    model_id_or_path,
    torch_dtype=dtype,
    local_files_only={local_files_only},
)
pipe = pipe.to(device)
{image_setup}{callback_def}
generator = torch.Generator(device="cpu").manual_seed({args.seed})
call_kwargs = dict(
    num_inference_steps={args.steps},
    generator=generator,
{negative_prompt_line}{size_lines})
{callback_args}
result = pipe({call_inputs}, **call_kwargs)
image = result.images[0]
# image.save("output.png")
'''

    print(textwrap.dedent(skeleton).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
