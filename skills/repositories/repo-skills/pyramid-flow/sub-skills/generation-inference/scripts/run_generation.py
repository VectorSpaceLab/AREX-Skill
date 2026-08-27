#!/usr/bin/env python3
"""Plan or run Pyramid-Flow generation safely.

Default behavior is a dry run: validate arguments and print the command that
would run. Pass --execute only when the checkpoint, CUDA backend, and imports
are ready. Pass --launch to have this wrapper spawn the torch distributed
launcher for multi-GPU runs.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from check_generation_prereqs import (  # noqa: E402
    GenerationPrereqError,
    build_parser as build_prereq_parser,
    format_plan,
    validate_generation_prereqs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = build_prereq_parser()
    parser.description = "Plan or execute Pyramid-Flow generation without importing the Gradio demo apps."
    parser.add_argument("--execute", action="store_true", help="Run generation in the current process")
    parser.add_argument(
        "--launch",
        action="store_true",
        help="Spawn the appropriate Python/torch distributed command and run generation",
    )
    parser.add_argument("--device-id", type=int, default=0, help="CUDA device for single-process execution")
    return parser


def _add_arg(argv: List[str], flag: str, value: Optional[Any]) -> None:
    if value is not None:
        argv.extend([flag, str(value)])


def _execution_args(plan: Dict[str, Any], args: argparse.Namespace) -> List[str]:
    argv: List[str] = ["--execute", "--task", plan["task"]]
    _add_arg(argv, "--model-name", plan["model_name"])
    _add_arg(argv, "--model-path", plan["model_path"])
    _add_arg(argv, "--variant", plan["variant"])
    _add_arg(argv, "--resolution", plan.get("resolution"))
    _add_arg(argv, "--ratio", plan.get("ratio"))
    _add_arg(argv, "--prompt", plan.get("prompt"))
    _add_arg(argv, "--image-path", plan.get("image_path"))
    _add_arg(argv, "--output-path", plan.get("output_path"))
    _add_arg(argv, "--gpus", plan.get("gpus"))
    _add_arg(argv, "--sp-group-size", plan.get("sp_group_size"))
    _add_arg(argv, "--sp-proc-num", plan.get("sp_proc_num"))
    _add_arg(argv, "--model-dtype", plan.get("model_dtype"))
    _add_arg(argv, "--temp", plan.get("temp"))
    _add_arg(argv, "--guidance-scale", plan.get("guidance_scale"))
    _add_arg(argv, "--video-guidance-scale", plan.get("video_guidance_scale"))
    _add_arg(argv, "--device-id", getattr(args, "device_id", 0))
    if plan.get("cpu_offloading"):
        argv.append("--cpu-offloading")
    if plan.get("sequential_cpu_offload"):
        argv.append("--sequential-cpu-offload")
    if plan.get("save_memory"):
        argv.append("--save-memory")
    else:
        argv.append("--no-save-memory")
    return argv


def _launch_command(plan: Dict[str, Any], args: argparse.Namespace) -> List[str]:
    child_args = _execution_args(plan, args)
    script_path = str(Path(__file__).resolve())
    if plan["gpus"] > 1:
        return [
            sys.executable,
            "-m",
            "torch.distributed.run",
            "--nproc_per_node",
            str(plan["gpus"]),
            script_path,
            *child_args,
        ]
    return [sys.executable, script_path, *child_args]


def _print_dry_run(plan: Dict[str, Any], args: argparse.Namespace) -> None:
    print(format_plan(plan))
    print("launch_command:")
    print("  " + shlex.join(_launch_command(plan, args)))
    print("notes:")
    print("  - This is a dry run; no checkpoint is loaded and no video/image is generated.")
    print("  - Use --execute only inside the correct single-process or torchrun context.")
    print("  - Use --launch to let this wrapper spawn the printed command.")


def _resize_crop_image(img: Any, target_width: int, target_height: int) -> Any:
    from PIL import Image

    original_width, original_height = img.width, img.height
    scale = max(target_width / original_width, target_height / original_height)
    resized_width = round(original_width * scale)
    resized_height = round(original_height * scale)
    img = img.resize((resized_width, resized_height), resample=Image.LANCZOS)

    left = (resized_width - target_width) / 2
    top = (resized_height - target_height) / 2
    right = (resized_width + target_width) / 2
    bottom = (resized_height + target_height) / 2
    return img.crop((left, top, right, bottom))


def _torch_dtype(torch: Any, model_dtype: str) -> Any:
    if model_dtype == "bf16":
        return torch.bfloat16
    if model_dtype == "fp16":
        return torch.float16
    return torch.float32


def _prepare_model(plan: Dict[str, Any], args: argparse.Namespace, torch: Any, distributed: bool) -> Any:
    from pyramid_dit import PyramidDiTForVideoGeneration

    model = PyramidDiTForVideoGeneration(
        plan["model_path"],
        model_dtype=plan["model_dtype"],
        model_name=plan["model_name"],
        model_variant=plan["variant"],
    )
    model.vae.enable_tiling()

    if distributed:
        device = torch.device("cuda")
        model.vae.to(device)
        model.dit.to(device)
        model.text_encoder.to(device)
        return model

    torch.cuda.set_device(args.device_id)
    if plan.get("sequential_cpu_offload"):
        model.enable_sequential_cpu_offload()
    elif not plan.get("cpu_offloading"):
        model.vae.to("cuda")
        model.dit.to("cuda")
        model.text_encoder.to("cuda")
    return model


def _ensure_output_parent(output_path: str) -> Path:
    path = Path(output_path).expanduser()
    if path.parent and str(path.parent) != ".":
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _setup_distributed_if_needed(plan: Dict[str, Any], args: argparse.Namespace) -> bool:
    if plan["gpus"] <= 1:
        return False

    from trainer_misc import init_distributed_mode, init_sequence_parallel_group

    init_distributed_mode(args)
    if not getattr(args, "distributed", False):
        raise RuntimeError(
            "multi-GPU generation requested, but this process is not under torchrun; use --launch or the printed command"
        )
    if getattr(args, "world_size", None) != plan["sp_group_size"]:
        raise RuntimeError("world_size must match sp_group_size for sequence-parallel inference")
    init_sequence_parallel_group(args)
    return True


def execute_generation(plan: Dict[str, Any], args: argparse.Namespace) -> int:
    import torch
    from PIL import Image
    from diffusers.utils import export_to_video

    distributed = _setup_distributed_if_needed(plan, args)
    rank = getattr(args, "rank", 0) if distributed else 0
    torch_dtype = _torch_dtype(torch, plan["model_dtype"])
    model = _prepare_model(plan, args, torch, distributed)
    output_path = _ensure_output_parent(plan["output_path"])

    use_amp = plan["model_dtype"] != "fp32"
    cpu_offloading = bool(plan.get("cpu_offloading")) and not distributed

    if plan["task"] == "t2v":
        with torch.no_grad(), torch.cuda.amp.autocast(enabled=use_amp, dtype=torch_dtype):
            frames = model.generate(
                prompt=plan["prompt"],
                num_inference_steps=[20, 20, 20],
                video_num_inference_steps=[10, 10, 10],
                height=plan["height"],
                width=plan["width"],
                temp=plan["temp"],
                guidance_scale=plan["guidance_scale"],
                video_guidance_scale=plan["video_guidance_scale"],
                output_type="pil",
                save_memory=plan["save_memory"],
                cpu_offloading=cpu_offloading,
                inference_multigpu=distributed,
            )
        if rank == 0:
            export_to_video(frames, str(output_path), fps=24)

    elif plan["task"] == "i2v":
        image = Image.open(plan["image_path"]).convert("RGB")
        image = _resize_crop_image(image, plan["width"], plan["height"])
        with torch.no_grad(), torch.cuda.amp.autocast(enabled=use_amp, dtype=torch_dtype):
            frames = model.generate_i2v(
                prompt=plan["prompt"],
                input_image=image,
                num_inference_steps=[10, 10, 10],
                temp=plan["temp"],
                guidance_scale=plan["guidance_scale"],
                video_guidance_scale=plan["video_guidance_scale"],
                output_type="pil",
                save_memory=plan["save_memory"],
                cpu_offloading=cpu_offloading,
                inference_multigpu=distributed,
            )
        if rank == 0:
            export_to_video(frames, str(output_path), fps=24)

    elif plan["task"] == "txt2img":
        with torch.no_grad(), torch.cuda.amp.autocast(enabled=use_amp, dtype=torch_dtype):
            images = model.generate(
                prompt=plan["prompt"],
                num_inference_steps=[20, 20, 20],
                height=plan["height"],
                width=plan["width"],
                temp=1,
                guidance_scale=plan["guidance_scale"],
                output_type="pil",
                save_memory=False,
            )
        if rank == 0:
            images[0].save(str(output_path))

    else:  # pragma: no cover - argparse prevents this
        raise RuntimeError(f"unsupported task: {plan['task']}")

    if distributed and torch.distributed.is_initialized():
        torch.distributed.barrier()
    if rank == 0:
        print(f"wrote {output_path}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        plan = validate_generation_prereqs(args)
    except GenerationPrereqError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for warning in plan["warnings"]:
        print(f"warning: {warning}", file=sys.stderr)

    if args.json and not args.execute and not args.launch:
        print(json.dumps(plan, indent=2, sort_keys=True, default=str))
        return 0

    if not args.execute and not args.launch:
        _print_dry_run(plan, args)
        return 0

    if args.launch:
        command = _launch_command(plan, args)
        print("launching:", shlex.join(command))
        return subprocess.run(command, check=False).returncode

    try:
        return execute_generation(plan, args)
    except Exception as exc:  # pragma: no cover - runtime backend failures are environment-specific
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
