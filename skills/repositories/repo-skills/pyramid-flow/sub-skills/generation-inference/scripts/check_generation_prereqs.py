#!/usr/bin/env python3
"""Validate Pyramid-Flow generation prerequisites before launch.

This checker keeps the runtime skill self-contained and avoids importing the
side-effectful demo apps during inspection.
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, List, Optional

TASKS = {"t2v", "i2v", "txt2img"}
MODEL_NAMES = {"pyramid_flux", "pyramid_mmdit"}
MODEL_REPO_HINTS = {
    "pyramid_flux": "rain1011/pyramid-flow-miniflux",
    "pyramid_mmdit": "rain1011/pyramid-flow-sd3",
}
RESOLUTION_TO_VARIANT = {
    "384p": "diffusion_transformer_384p",
    "768p": "diffusion_transformer_768p",
}
RESOLUTION_TO_SIZE = {
    "384p": (640, 384),
    "768p": (1280, 768),
}
RATIO_TO_SIZE = {
    "1:1": (1024, 1024),
    "5:3": (1280, 768),
    "3:5": (768, 1280),
}
IMAGE_VARIANT = "diffusion_transformer_image"


class GenerationPrereqError(ValueError):
    """Raised when a launch request is not safe to execute."""


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def _existing_file(value: str) -> str:
    path = Path(value).expanduser()
    if not path.exists():
        raise argparse.ArgumentTypeError(f"file does not exist: {value}")
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"not a file: {value}")
    return str(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Pyramid-Flow generation prerequisites.",
    )
    parser.add_argument("--task", choices=sorted(TASKS), required=True)
    parser.add_argument("--model-name", choices=sorted(MODEL_NAMES))
    parser.add_argument("--model-path", help="Path to the downloaded checkpoint directory")
    parser.add_argument("--variant", help="Checkpoint variant directory name")
    parser.add_argument("--resolution", choices=sorted(RESOLUTION_TO_VARIANT))
    parser.add_argument("--ratio", choices=sorted(RATIO_TO_SIZE))
    parser.add_argument("--prompt", help="Prompt text")
    parser.add_argument("--image-path", type=_existing_file, help="Input image for image-to-video")
    parser.add_argument("--output-path", help="Output file path")
    parser.add_argument("--gpus", type=_positive_int, default=1)
    parser.add_argument("--sp-group-size", type=_positive_int)
    parser.add_argument("--sp-proc-num", type=int, default=-1)
    parser.add_argument("--model-dtype", choices=("bf16", "fp16", "fp32"), default="bf16")
    parser.add_argument("--temp", type=_positive_int, default=16)
    parser.add_argument("--guidance-scale", type=float, default=7.0)
    parser.add_argument("--video-guidance-scale", type=float, default=5.0)
    parser.add_argument("--cpu-offloading", action="store_true", help="Enable per-call CPU offloading in the single-GPU path")
    parser.add_argument("--sequential-cpu-offload", action="store_true", help="Enable sequential CPU offload in the single-GPU path")
    parser.add_argument("--save-memory", dest="save_memory", action="store_true", help="Prefer the lower-memory generation path")
    parser.add_argument("--no-save-memory", dest="save_memory", action="store_false", help="Disable the lower-memory generation path")
    parser.set_defaults(save_memory=True)
    parser.add_argument("--json", action="store_true", help="Emit a JSON summary")
    return parser


def _probe_runtime() -> Dict[str, Any]:
    runtime: Dict[str, Any] = {}
    try:
        runtime["gradio_version"] = metadata.version("gradio")
    except metadata.PackageNotFoundError:
        runtime["gradio_version"] = None
    try:
        runtime["huggingface_hub_version"] = metadata.version("huggingface_hub")
    except metadata.PackageNotFoundError:
        runtime["huggingface_hub_version"] = None

    try:
        import torch
    except Exception as exc:  # pragma: no cover - exercised in failure mode
        runtime["torch_error"] = str(exc)
        runtime["cuda_available"] = False
        runtime["cuda_device_count"] = 0
        runtime["distributed_available"] = False
        runtime["mps_available"] = False
        return runtime

    runtime["torch_version"] = torch.__version__
    runtime["cuda_available"] = torch.cuda.is_available()
    runtime["cuda_device_count"] = torch.cuda.device_count() if torch.cuda.is_available() else 0
    runtime["distributed_available"] = torch.distributed.is_available()
    runtime["mps_available"] = bool(getattr(torch.backends, "mps", None)) and torch.backends.mps.is_available()
    return runtime


def _default_model_name(task: str, resolution: Optional[str], model_name: Optional[str]) -> str:
    if model_name:
        return model_name
    if task == "txt2img":
        return "pyramid_flux"
    if resolution == "768p":
        return "pyramid_mmdit"
    return "pyramid_flux"


def _default_variant(task: str, resolution: Optional[str], variant: Optional[str]) -> str:
    if variant:
        return variant
    if task == "txt2img":
        return IMAGE_VARIANT
    if resolution is None:
        return RESOLUTION_TO_VARIANT["384p"]
    return RESOLUTION_TO_VARIANT[resolution]


def _default_output_path(task: str, output_path: Optional[str]) -> str:
    if output_path:
        return output_path
    if task == "t2v":
        return "text_to_video_sample.mp4"
    if task == "i2v":
        return "image_to_video_sample.mp4"
    return "text_to_image_sample.png"


def _resolve_sp_group_size(gpus: int, sp_group_size: Optional[int]) -> int:
    if sp_group_size is not None:
        return sp_group_size
    return gpus if gpus > 1 else 1


def _check_model_path(model_path: Optional[str], variant: str) -> List[str]:
    errors: List[str] = []
    if not model_path:
        errors.append("model-path is required for direct generation tasks")
        return errors

    root = Path(model_path).expanduser()
    if not root.exists():
        errors.append(f"model path does not exist: {root}")
        return errors

    variant_dir = root / variant
    root_config = root / "config.json"
    variant_config = variant_dir / "config.json"

    if variant_config.exists():
        return errors
    if root_config.exists():
        return errors

    errors.append(
        f"expected config.json under '{variant_dir}' or at the model root, but neither was found"
    )
    return errors


def validate_generation_prereqs(args: argparse.Namespace) -> Dict[str, Any]:
    runtime = _probe_runtime()
    warnings: List[str] = []
    errors: List[str] = []

    task = args.task
    resolution = args.resolution
    ratio = args.ratio
    model_name = _default_model_name(task, resolution, args.model_name)
    variant = _default_variant(task, resolution, args.variant)
    output_path = _default_output_path(task, args.output_path)
    sp_group_size = _resolve_sp_group_size(args.gpus, args.sp_group_size)

    if runtime.get("torch_error"):
        errors.append(f"torch import failed: {runtime['torch_error']}")

    if runtime.get("gradio_version") is None:
        warnings.append("gradio is not installed in the active environment")
    if runtime.get("huggingface_hub_version") is None:
        warnings.append("huggingface_hub is not installed in the active environment")

    if task in {"t2v", "i2v"} and resolution is None:
        resolution = "384p"

    if not args.prompt:
        errors.append("prompt is required for generation tasks")

    if task == "txt2img":
        if ratio is None:
            ratio = "1:1"
        if variant != IMAGE_VARIANT:
            errors.append("text-to-image must use the image variant")
        if args.temp != 1:
            errors.append("text-to-image uses temp=1 in the notebook recipe")
        if args.gpus != 1:
            errors.append("text-to-image is single-process in the bundled recipe")

    if task == "i2v" and not args.image_path:
        errors.append("image-path is required for image-to-video")

    if task in {"t2v", "i2v"}:
        if args.temp < 1:
            errors.append("temp must be at least 1")
        if resolution == "384p" and args.temp > 16:
            errors.append("384p paths cap temp at 16 in the bundled recipe")
        if resolution == "768p" and args.temp > 31:
            errors.append("768p paths cap temp at 31 in the bundled recipe")

    if task == "txt2img":
        if ratio not in RATIO_TO_SIZE:
            errors.append(f"unsupported text-to-image ratio: {ratio}")

    if task in {"t2v", "i2v"} and resolution not in RESOLUTION_TO_VARIANT:
        errors.append("resolution must be 384p or 768p for video generation")

    if task in {"t2v", "i2v"} and resolution is not None and RESOLUTION_TO_VARIANT[resolution] != variant:
        errors.append("the requested resolution and variant do not match")

    if task in {"t2v", "i2v"} and model_name == "pyramid_flux" and variant == "diffusion_transformer_768p":
        errors.append(
            "pyramid_flux + 768p is intentionally rejected by the bundled launcher; use pyramid_mmdit for 768p"
        )

    if task in {"t2v", "i2v"} and args.guidance_scale <= 0:
        errors.append("guidance-scale must be positive")
    if task in {"t2v", "i2v"} and args.video_guidance_scale <= 0:
        errors.append("video-guidance-scale must be positive")

    if args.gpus < 1:
        errors.append("gpus must be at least 1")
    if sp_group_size < 1:
        errors.append("sp-group-size must be at least 1")
    if args.gpus > 1 and sp_group_size != args.gpus:
        errors.append("the sequence-parallel group size must match the launched world size")
    if args.sp_proc_num != -1 and sp_group_size > 0 and args.sp_proc_num % sp_group_size != 0:
        errors.append("sp-proc-num must be evenly divisible by sp-group-size")

    if args.gpus > 1 and (args.cpu_offloading or args.sequential_cpu_offload):
        errors.append("CPU offload is only supported in the single-GPU path")
    if task == "txt2img" and (args.cpu_offloading or args.sequential_cpu_offload):
        warnings.append("CPU offload flags are ignored by the text-to-image notebook recipe")

    if task in {"t2v", "i2v", "txt2img"} and not runtime.get("cuda_available"):
        errors.append("the bundled generation wrapper is CUDA-first; MPS is documented separately but not implemented here")

    if args.gpus > 1:
        if not runtime.get("cuda_available"):
            errors.append("multi-GPU generation requires CUDA availability")
        elif runtime.get("cuda_device_count", 0) < args.gpus:
            errors.append(
                f"requested {args.gpus} GPUs but only {runtime.get('cuda_device_count', 0)} CUDA devices are visible"
            )
        if not runtime.get("distributed_available"):
            errors.append("multi-GPU generation requires torch.distributed")

    if task == "txt2img" and args.gpus > 1:
        errors.append("the text-to-image recipe is single-GPU in this repo")

    errors.extend(_check_model_path(args.model_path, variant) if task in {"t2v", "i2v", "txt2img"} else [])

    if task == "txt2img":
        width, height = RATIO_TO_SIZE[ratio]
    else:
        width, height = RESOLUTION_TO_SIZE[resolution]

    if task in {"t2v", "i2v"}:
        if args.sequential_cpu_offload:
            cpu_offload_note = "sequential CPU offload is enabled for the single-GPU path"
        elif args.cpu_offloading:
            cpu_offload_note = "per-call CPU offload is enabled for the single-GPU path"
        else:
            cpu_offload_note = "single-GPU CPU offload is available; multi-GPU uses sequence parallel instead"
    else:
        cpu_offload_note = "text-to-image follows the single-process notebook recipe"

    if runtime.get("mps_available"):
        warnings.append("MPS is visible, but the bundled launchers are CUDA-first and not MPS-native")

    if errors:
        raise GenerationPrereqError("\n".join(errors))

    plan: Dict[str, Any] = {
        "task": task,
        "model_name": model_name,
        "model_dtype": args.model_dtype,
        "variant": variant,
        "resolution": resolution,
        "ratio": ratio,
        "width": width,
        "height": height,
        "model_path": args.model_path,
        "output_path": output_path,
        "prompt": args.prompt,
        "image_path": args.image_path,
        "gpus": args.gpus,
        "sp_group_size": sp_group_size,
        "sp_proc_num": args.sp_proc_num,
        "temp": args.temp,
        "guidance_scale": args.guidance_scale,
        "video_guidance_scale": args.video_guidance_scale,
        "save_memory": args.save_memory,
        "cpu_offloading": args.cpu_offloading,
        "sequential_cpu_offload": args.sequential_cpu_offload,
        "runtime": runtime,
        "warnings": warnings,
        "cpu_offload_note": cpu_offload_note,
        "model_repo_hint": MODEL_REPO_HINTS[model_name],
    }
    return plan


def format_plan(plan: Dict[str, Any]) -> str:
    pieces = [
        f"task={plan['task']}",
        f"model_name={plan['model_name']}",
        f"variant={plan['variant']}",
        f"gpus={plan['gpus']}",
        f"sp_group_size={plan['sp_group_size']}",
        f"output_path={plan['output_path']}",
    ]
    if plan.get("resolution"):
        pieces.append(f"resolution={plan['resolution']}")
    if plan.get("ratio"):
        pieces.append(f"ratio={plan['ratio']}")
    pieces.append(f"size={plan['width']}x{plan['height']}")
    return "ready: " + ", ".join(pieces)


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        plan = validate_generation_prereqs(args)
    except GenerationPrereqError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for warning in plan["warnings"]:
        print(f"warning: {warning}", file=sys.stderr)

    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True, default=str))
    else:
        print(format_plan(plan))
        print(f"repo_hint: {plan['model_repo_hint']}")
        print(f"cpu_offload_note: {plan['cpu_offload_note']}")
        print(f"gradio_version: {plan['runtime'].get('gradio_version')}")
        print(f"huggingface_hub_version: {plan['runtime'].get('huggingface_hub_version')}")
        print(f"cuda_available: {plan['runtime'].get('cuda_available')}")
        print(f"cuda_device_count: {plan['runtime'].get('cuda_device_count')}")
        print(f"distributed_available: {plan['runtime'].get('distributed_available')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
