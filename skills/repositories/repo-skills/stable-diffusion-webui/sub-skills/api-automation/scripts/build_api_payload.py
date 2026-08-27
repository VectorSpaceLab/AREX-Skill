#!/usr/bin/env python3
"""Build starter JSON payloads for Stable Diffusion WebUI API calls."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
from pathlib import Path
from typing import Any

PLACEHOLDER_PNG = "data:image/png;base64,REPLACE_WITH_BASE64_IMAGE_BYTES"
PLACEHOLDER_MASK = "data:image/png;base64,REPLACE_WITH_BASE64_MASK_BYTES"


def data_url(path: str | None, placeholder: str) -> str:
    if not path:
        return placeholder
    file_path = Path(path)
    raw = file_path.read_bytes()
    mime_type = mimetypes.guess_type(file_path.name)[0] or "image/png"
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def bool_arg(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected a boolean value, got {value!r}")


def generation_common(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "prompt": args.prompt,
        "negative_prompt": args.negative_prompt,
        "styles": [],
        "seed": args.seed,
        "subseed": -1,
        "subseed_strength": 0,
        "seed_resize_from_h": -1,
        "seed_resize_from_w": -1,
        "sampler_index": args.sampler,
        "batch_size": 1,
        "n_iter": 1,
        "steps": args.steps,
        "cfg_scale": args.cfg_scale,
        "width": args.width,
        "height": args.height,
        "restore_faces": False,
        "tiling": False,
        "send_images": args.send_images,
        "save_images": False,
    }


def build_txt2img(args: argparse.Namespace) -> dict[str, Any]:
    payload = generation_common(args)
    if args.scheduler:
        payload["scheduler"] = args.scheduler
    if args.force_task_id:
        payload["force_task_id"] = args.force_task_id
    return payload


def build_img2img_inpaint(args: argparse.Namespace) -> dict[str, Any]:
    payload = generation_common(args)
    payload.update(
        {
            "init_images": [data_url(args.image_path, PLACEHOLDER_PNG)],
            "denoising_strength": args.denoising_strength,
            "resize_mode": args.resize_mode,
            "mask": data_url(args.mask_path, PLACEHOLDER_MASK),
            "mask_blur": args.mask_blur,
            "inpainting_fill": args.inpainting_fill,
            "inpaint_full_res": args.inpaint_full_res,
            "inpaint_full_res_padding": args.inpaint_full_res_padding,
            "inpainting_mask_invert": args.inpainting_mask_invert,
            "include_init_images": False,
            "override_settings": {},
        }
    )
    if args.scheduler:
        payload["scheduler"] = args.scheduler
    if args.force_task_id:
        payload["force_task_id"] = args.force_task_id
    return payload


def extras_fields(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "resize_mode": args.resize_mode,
        "show_extras_results": True,
        "gfpgan_visibility": 0,
        "codeformer_visibility": 0,
        "codeformer_weight": 0,
        "upscaling_resize": args.upscaling_resize,
        "upscaling_resize_w": args.upscaling_resize_w,
        "upscaling_resize_h": args.upscaling_resize_h,
        "upscaling_crop": True,
        "upscaler_1": args.upscaler_1,
        "upscaler_2": args.upscaler_2,
        "extras_upscaler_2_visibility": 0,
        "upscale_first": False,
    }


def build_extras_single(args: argparse.Namespace) -> dict[str, Any]:
    payload = extras_fields(args)
    payload["image"] = data_url(args.image_path, PLACEHOLDER_PNG)
    return payload


def build_png_info(args: argparse.Namespace) -> dict[str, Any]:
    return {"image": data_url(args.image_path, PLACEHOLDER_PNG)}


def build_progress(args: argparse.Namespace) -> dict[str, Any]:
    return {"skip_current_image": args.skip_current_image}


def build_options_set(args: argparse.Namespace) -> dict[str, Any]:
    if args.option_json:
        value = json.loads(args.option_json)
        if not isinstance(value, dict):
            raise SystemExit("--option-json must decode to a JSON object")
        return value
    return {args.option_key: json.loads(args.option_value)}


def add_generation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--prompt", default="example prompt")
    parser.add_argument("--negative-prompt", default="")
    parser.add_argument("--sampler", default="Euler a")
    parser.add_argument("--scheduler", default=None)
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--cfg-scale", type=float, default=7)
    parser.add_argument("--width", type=int, default=64)
    parser.add_argument("--height", type=int, default=64)
    parser.add_argument("--seed", type=int, default=-1)
    parser.add_argument("--send-images", type=bool_arg, default=True)
    parser.add_argument("--force-task-id", default=None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit starter JSON payloads for Stable Diffusion WebUI API endpoints")
    subparsers = parser.add_subparsers(dest="kind", required=True)

    txt2img = subparsers.add_parser("txt2img", help="Payload for POST /sdapi/v1/txt2img")
    add_generation_args(txt2img)
    txt2img.set_defaults(builder=build_txt2img)

    img2img = subparsers.add_parser("img2img-inpaint", help="Payload for POST /sdapi/v1/img2img with inpaint fields")
    add_generation_args(img2img)
    img2img.add_argument("--image-path", default=None, help="Local init image to encode as a data URL")
    img2img.add_argument("--mask-path", default=None, help="Local mask image to encode as a data URL")
    img2img.add_argument("--denoising-strength", type=float, default=0.75)
    img2img.add_argument("--resize-mode", type=int, default=0)
    img2img.add_argument("--mask-blur", type=int, default=4)
    img2img.add_argument("--inpainting-fill", type=int, default=0)
    img2img.add_argument("--inpaint-full-res", type=bool_arg, default=False)
    img2img.add_argument("--inpaint-full-res-padding", type=int, default=0)
    img2img.add_argument("--inpainting-mask-invert", type=bool_arg, default=False)
    img2img.set_defaults(builder=build_img2img_inpaint)

    extras = subparsers.add_parser("extras-single", help="Payload for POST /sdapi/v1/extra-single-image")
    extras.add_argument("--image-path", default=None, help="Local image to encode as a data URL")
    extras.add_argument("--resize-mode", type=int, default=0)
    extras.add_argument("--upscaling-resize", type=float, default=2)
    extras.add_argument("--upscaling-resize-w", type=int, default=128)
    extras.add_argument("--upscaling-resize-h", type=int, default=128)
    extras.add_argument("--upscaler-1", default="Lanczos")
    extras.add_argument("--upscaler-2", default="None")
    extras.set_defaults(builder=build_extras_single)

    png_info = subparsers.add_parser("png-info", help="Payload for POST /sdapi/v1/png-info")
    png_info.add_argument("--image-path", default=None, help="Local PNG/image to encode as a data URL")
    png_info.set_defaults(builder=build_png_info)

    progress = subparsers.add_parser("progress", help="Query-equivalent object for GET /sdapi/v1/progress")
    progress.add_argument("--skip-current-image", type=bool_arg, default=True)
    progress.set_defaults(builder=build_progress)

    options = subparsers.add_parser("options-set", help="Payload for POST /sdapi/v1/options")
    options.add_argument("--option-json", default=None, help="Full JSON object to emit")
    options.add_argument("--option-key", default="send_seed", help="Single option key when --option-json is omitted")
    options.add_argument("--option-value", default="false", help="JSON value for --option-key, for example false, true, 7, or \"name\"")
    options.set_defaults(builder=build_options_set)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    payload = args.builder(args)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
