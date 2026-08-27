#!/usr/bin/env python3
"""Parameterized Nunchaku Qwen-Image / Qwen-Image-Edit template.

This script assumes `nunchaku`, `torch`, `diffusers`, and required model assets are
available in the active Python environment. It does not embed credentials, cache
paths, or checkout-local paths.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from importlib import metadata
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


SUPPORTED_TRANSFORMER_SUFFIXES = (".safetensors", ".sft")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Nunchaku-backed Qwen-Image text-to-image or edit workflow.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--mode", choices=("txt2img", "edit"), required=True, help="Workflow mode.")
    parser.add_argument(
        "--transformer",
        required=True,
        help="Nunchaku Qwen transformer checkpoint file or HF file path ending in .safetensors/.sft.",
    )
    parser.add_argument("--base-model", required=True, help="Diffusers base model id/path, e.g. Qwen/Qwen-Image.")
    parser.add_argument("--prompt", required=True, help="Prompt or edit instruction.")
    parser.add_argument(
        "--image",
        action="append",
        default=[],
        help="Edit input image path/URL. Repeat for 2509 multi-image edit, or pass comma-separated values.",
    )
    parser.add_argument("--output", required=True, help="Output image path.")
    parser.add_argument("--device", default="cuda", help="Torch device for non-offload execution, e.g. cuda or cuda:0.")
    parser.add_argument(
        "--dtype",
        default="auto",
        choices=("auto", "bf16", "bfloat16", "fp16", "float16", "fp32", "float32"),
        help="Torch dtype for transformer and pipeline construction.",
    )
    parser.add_argument(
        "--offload",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Use Nunchaku transformer offload plus Diffusers sequential CPU offload.",
    )
    parser.add_argument("--negative-prompt", default=None, help="Optional negative prompt. A single space is common.")
    parser.add_argument("--width", type=int, default=1024, help="Text-to-image output width.")
    parser.add_argument("--height", type=int, default=1024, help="Text-to-image output height.")
    parser.add_argument("--steps", type=int, default=None, help="Inference steps; inferred from Lightning names if omitted.")
    parser.add_argument("--true-cfg-scale", type=float, default=None, help="Qwen true_cfg_scale; inferred if omitted.")
    parser.add_argument("--seed", type=int, default=None, help="Optional CPU generator seed.")
    parser.add_argument("--num-blocks-on-gpu", type=int, default=1, help="Nunchaku offload blocks kept on GPU.")
    parser.add_argument(
        "--pin-memory",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Pin CPU memory for Nunchaku offload.",
    )
    args = parser.parse_args()
    validate_args(parser, args)
    return args


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    suffix = Path(args.transformer).name.lower()
    if not suffix.endswith(SUPPORTED_TRANSFORMER_SUFFIXES):
        parser.error("--transformer must name a .safetensors or .sft checkpoint file, not a model directory")

    local_transformer = Path(args.transformer).expanduser()
    if local_transformer.exists() and not local_transformer.is_file():
        parser.error("--transformer points to a local path that is not a file")

    flattened_images = list(flatten_image_args(args.image))
    args.image = flattened_images

    if args.mode == "txt2img" and args.image:
        parser.error("--image is only valid with --mode edit")
    if args.mode == "edit" and not args.image:
        parser.error("--mode edit requires at least one --image input")

    for image in args.image:
        if looks_like_url(image):
            continue
        if not Path(image).expanduser().is_file():
            parser.error(f"edit input image does not exist or is not a file: {image}")

    plus = is_2509(args)
    if args.mode == "edit" and len(args.image) > 1 and not plus:
        parser.error("multiple --image inputs require a 2509/QwenImageEditPlus workflow")

    if args.width <= 0 or args.height <= 0:
        parser.error("--width and --height must be positive")
    if args.steps is not None and args.steps <= 0:
        parser.error("--steps must be positive")
    if args.num_blocks_on_gpu <= 0:
        parser.error("--num-blocks-on-gpu must be positive")


def flatten_image_args(values: Iterable[str]) -> Iterable[str]:
    for value in values:
        for item in value.split(","):
            item = item.strip()
            if item:
                yield item


def looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"}


def is_lightning(args: argparse.Namespace) -> bool:
    return "lightning" in args.transformer.lower()


def is_2509(args: argparse.Namespace) -> bool:
    text = f"{args.base_model} {args.transformer}".lower()
    return "2509" in text


def infer_steps(args: argparse.Namespace) -> int:
    if args.steps is not None:
        return args.steps
    match = re.search(r"(\d+)\s*steps", args.transformer.lower())
    if match:
        return int(match.group(1))
    if is_lightning(args):
        return 4
    if args.mode == "edit" and is_2509(args):
        return 40
    return 50


def infer_true_cfg_scale(args: argparse.Namespace) -> float:
    if args.true_cfg_scale is not None:
        return args.true_cfg_scale
    return 1.0 if is_lightning(args) else 4.0


def version_tuple(version: str) -> tuple[int, int, int]:
    parts = [int(part) for part in re.findall(r"\d+", version)[:3]]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def require_diffusers_at_least(min_version: str, reason: str) -> None:
    try:
        installed = metadata.version("diffusers")
    except metadata.PackageNotFoundError as exc:
        raise RuntimeError("diffusers is not installed") from exc
    if version_tuple(installed) < version_tuple(min_version):
        raise RuntimeError(f"{reason} requires diffusers>={min_version}; installed version is {installed}")


def lightning_scheduler():
    from diffusers import FlowMatchEulerDiscreteScheduler

    scheduler_config = {
        "base_image_seq_len": 256,
        "base_shift": math.log(3),
        "invert_sigmas": False,
        "max_image_seq_len": 8192,
        "max_shift": math.log(3),
        "num_train_timesteps": 1000,
        "shift": 1.0,
        "shift_terminal": None,
        "stochastic_sampling": False,
        "time_shift_type": "exponential",
        "use_beta_sigmas": False,
        "use_dynamic_shifting": True,
        "use_exponential_sigmas": False,
        "use_karras_sigmas": False,
    }
    return FlowMatchEulerDiscreteScheduler.from_config(scheduler_config)


def resolve_dtype(dtype_name: str):
    import torch

    if dtype_name in {"bf16", "bfloat16"}:
        return torch.bfloat16
    if dtype_name in {"fp16", "float16"}:
        return torch.float16
    if dtype_name in {"fp32", "float32"}:
        return torch.float32
    if dtype_name == "auto":
        try:
            from nunchaku.utils import is_turing

            return torch.float16 if is_turing() else torch.bfloat16
        except Exception:
            return torch.bfloat16
    raise ValueError(f"unsupported dtype: {dtype_name}")


def cuda_device_index(device: str) -> int | None:
    if device == "cuda":
        return None
    if device.startswith("cuda:"):
        suffix = device.split(":", 1)[1]
        if suffix.isdigit():
            return int(suffix)
    return None


def load_edit_images(paths: list[str]):
    from diffusers.utils import load_image

    images = [load_image(path).convert("RGB") for path in paths]
    return images[0] if len(images) == 1 else images


def main() -> int:
    args = parse_args()

    import torch
    from nunchaku import NunchakuQwenImageTransformer2DModel

    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError(f"requested device {args.device!r}, but torch.cuda.is_available() is false")
    if args.offload and not args.device.startswith("cuda"):
        raise RuntimeError("--offload requires a CUDA device because it offloads between CPU and GPU")

    if is_2509(args):
        require_diffusers_at_least("0.36.0", "Qwen-Image-Edit-2509")

    if args.mode == "txt2img":
        from diffusers import QwenImagePipeline

        pipe_cls = QwenImagePipeline
    elif is_2509(args):
        from diffusers import QwenImageEditPlusPipeline

        pipe_cls = QwenImageEditPlusPipeline
    else:
        from diffusers import QwenImageEditPipeline

        pipe_cls = QwenImageEditPipeline

    torch_dtype = resolve_dtype(args.dtype)
    transformer = NunchakuQwenImageTransformer2DModel.from_pretrained(
        args.transformer,
        torch_dtype=torch_dtype,
    )

    pipe_kwargs = {"transformer": transformer, "torch_dtype": torch_dtype}
    if is_lightning(args):
        pipe_kwargs["scheduler"] = lightning_scheduler()

    pipe = pipe_cls.from_pretrained(args.base_model, **pipe_kwargs)

    if args.offload:
        transformer.set_offload(True, use_pin_memory=args.pin_memory, num_blocks_on_gpu=args.num_blocks_on_gpu)
        excludes = getattr(pipe, "_exclude_from_cpu_offload", None)
        if excludes is None:
            pipe._exclude_from_cpu_offload = []
            excludes = pipe._exclude_from_cpu_offload
        if "transformer" not in excludes:
            excludes.append("transformer")
        gpu_id = cuda_device_index(args.device)
        if gpu_id is None:
            pipe.enable_sequential_cpu_offload()
        else:
            pipe.enable_sequential_cpu_offload(gpu_id=gpu_id)
    else:
        pipe.to(args.device)

    call_kwargs = {
        "prompt": args.prompt,
        "num_inference_steps": infer_steps(args),
        "true_cfg_scale": infer_true_cfg_scale(args),
    }
    if args.negative_prompt is not None:
        call_kwargs["negative_prompt"] = args.negative_prompt
    if args.seed is not None:
        call_kwargs["generator"] = torch.Generator(device="cpu").manual_seed(args.seed)

    if args.mode == "txt2img":
        call_kwargs.update({"width": args.width, "height": args.height})
    else:
        call_kwargs["image"] = load_edit_images(args.image)

    image = pipe(**call_kwargs).images[0]
    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    print(f"Saved {output_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
