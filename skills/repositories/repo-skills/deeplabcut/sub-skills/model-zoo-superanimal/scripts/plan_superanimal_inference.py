#!/usr/bin/env python3
"""No-download planner for deeplabcut.video_inference_superanimal arguments.

The script is intentionally standalone: it does not import DeepLabCut, dlclibrary,
torch, TensorFlow, or FMPose3D, and it never downloads model weights. It validates
common argument combinations and prints a planned call plus a preflight checklist.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SUPERANIMAL_CHOICES = (
    "superanimal_quadruped",
    "superanimal_topviewmouse",
    "superanimal_humanbody",
    "superanimal_bird",
)

MODEL_CHOICES = (
    "dlcrnet",
    "hrnet_w32",
    "resnet_50",
    "rtmpose_s",
    "rtmpose_x",
    "fmpose3d_animals",
    "fmpose3d_humans",
)

DETECTOR_CHOICES = (
    "fasterrcnn_resnet50_fpn_v2",
    "fasterrcnn_mobilenet_v3_large_fpn",
    "fasterrcnn_resnet50_fpn",
    "ssdlite",
)

DOCUMENTED_MODELS = {
    "superanimal_quadruped": {"hrnet_w32", "dlcrnet", "fmpose3d_animals"},
    "superanimal_topviewmouse": {"hrnet_w32", "dlcrnet"},
    "superanimal_humanbody": {"rtmpose_x", "fmpose3d_humans"},
    "superanimal_bird": set(),
}


def parse_csv_ints(raw: str | None, *, field: str) -> list[int] | None:
    if raw is None or raw == "":
        return None
    value = raw.strip()
    if value.lower() in {"none", "null", "[]"}:
        return None
    if value.startswith("range:"):
        parts = value.split(":")
        if len(parts) != 4:
            raise argparse.ArgumentTypeError(
                f"{field} range syntax must be range:START:STOP:STEP"
            )
        try:
            start, stop, step = (int(p) for p in parts[1:])
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"{field} range values must be integers") from exc
        if step == 0:
            raise argparse.ArgumentTypeError(f"{field} range step cannot be 0")
        values = list(range(start, stop, step))
        if not values:
            raise argparse.ArgumentTypeError(f"{field} range produced no values")
        return values
    try:
        values = [int(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{field} must contain integers") from exc
    if not values:
        raise argparse.ArgumentTypeError(f"{field} produced no values")
    return values


def parse_cropping(raw: str | None) -> list[int] | None:
    values = parse_csv_ints(raw, field="cropping")
    if values is None:
        return None
    if len(values) != 4:
        raise argparse.ArgumentTypeError("cropping must be x1,x2,y1,y2")
    x1, x2, y1, y2 = values
    if not (x1 < x2 and y1 < y2):
        raise argparse.ArgumentTypeError("cropping must satisfy x1 < x2 and y1 < y2")
    return values


def parse_scale_list(raw: str | None) -> list[int] | None:
    values = parse_csv_ints(raw, field="scale-list")
    if values is None:
        return None
    if any(v <= 0 for v in values):
        raise argparse.ArgumentTypeError("scale-list values must be positive")
    return values


def add_bool_arg(parser: argparse.ArgumentParser, name: str, *, default: bool, help_text: str) -> None:
    parser.add_argument(
        f"--{name}",
        action=argparse.BooleanOptionalAction,
        default=default,
        help=help_text,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and print a planned deeplabcut.video_inference_superanimal call "
            "without importing DeepLabCut or downloading weights."
        )
    )
    parser.add_argument("--video", action="append", default=[], help="Video path; repeat for multiple videos.")
    parser.add_argument("--videos", nargs="+", default=[], help="One or more video paths.")
    parser.add_argument("--superanimal-name", required=True, choices=SUPERANIMAL_CHOICES)
    parser.add_argument("--model-name", required=True, choices=MODEL_CHOICES)
    parser.add_argument("--detector-name", choices=DETECTOR_CHOICES)
    parser.add_argument("--scale-list", type=parse_scale_list, help="Comma list such as 200,300,400 or range:200:600:50.")
    parser.add_argument("--video-extensions", help="Extension filter used when a video input is a directory, e.g. .mp4.")
    parser.add_argument("--dest-folder", help="Destination folder for predictions and labeled videos.")
    parser.add_argument("--cropping", type=parse_cropping, help="Crop as x1,x2,y1,y2 applied to all videos in this call.")
    parser.add_argument("--video-adapt", action="store_true", help="Plan self-supervised video adaptation.")
    parser.add_argument("--plot-trajectories", action="store_true", help="Plan trajectory plotting where supported.")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--detector-batch-size", type=int, default=1)
    parser.add_argument("--pcutoff", type=float, default=0.1)
    parser.add_argument("--adapt-iterations", type=int, default=1000)
    parser.add_argument("--pseudo-threshold", type=float, default=0.1)
    parser.add_argument("--bbox-threshold", type=float, default=0.9)
    parser.add_argument("--detector-epochs", type=int, default=4)
    parser.add_argument("--pose-epochs", type=int, default=4)
    parser.add_argument("--max-individuals", type=int, default=10)
    parser.add_argument("--video-adapt-batch-size", type=int, default=8)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--customized-pose-checkpoint")
    parser.add_argument("--customized-detector-checkpoint")
    parser.add_argument("--customized-model-config")
    add_bool_arg(parser, "plot-bboxes", default=True, help_text="Draw detector boxes in top-down labeled videos.")
    add_bool_arg(parser, "create-labeled-video", default=True, help_text="Create a labeled video in addition to prediction files.")
    parser.add_argument("--fmpose-return-3d", action="store_true", help="Include df_3d in returned payload for FMPose3D.")
    parser.add_argument("--check-paths", action="store_true", help="Check whether input/custom paths already exist; still no downloads.")
    parser.add_argument("--output", choices=("json", "markdown"), default="json")
    return parser


def validate(args: argparse.Namespace, videos: list[str]) -> tuple[list[str], list[str], str]:
    errors: list[str] = []
    warnings: list[str] = []

    if not videos:
        errors.append("Provide at least one --video or --videos value.")

    for name in ("batch_size", "detector_batch_size", "adapt_iterations", "detector_epochs", "pose_epochs", "max_individuals", "video_adapt_batch_size"):
        if getattr(args, name) <= 0:
            errors.append(f"{name.replace('_', '-')} must be positive.")

    for name in ("pcutoff", "pseudo_threshold", "bbox_threshold"):
        value = getattr(args, name)
        if not (0.0 <= value <= 1.0):
            errors.append(f"{name.replace('_', '-')} must be between 0 and 1.")

    model = args.model_name
    family = args.superanimal_name
    is_fmpose = model.startswith("fmpose3d")
    is_dlcrnet = model == "dlcrnet"
    engine_route = "tensorflow" if is_dlcrnet else "pytorch"
    if is_fmpose:
        engine_route = "pytorch/fmpose3d"

    documented = DOCUMENTED_MODELS[family]
    if documented and model not in documented:
        warnings.append(
            f"{model!r} is a local model-config name but not one of the most directly documented choices for {family!r}; confirm weight availability before execution."
        )
    if not documented:
        warnings.append(
            f"{family!r} has evidenced project configuration, but this planner has no verified pretrained video-inference weight pair for it."
        )

    if is_fmpose:
        expected_family = {
            "fmpose3d_animals": "superanimal_quadruped",
            "fmpose3d_humans": "superanimal_humanbody",
        }[model]
        if family != expected_family:
            warnings.append(
                f"FMPose3D model {model!r} is normally paired with superanimal_name={expected_family!r}; model_name drives this branch."
            )
        if args.detector_name:
            warnings.append("FMPose3D video inference ignores detector_name.")
        if args.scale_list:
            warnings.append("FMPose3D video inference ignores scale_list.")
        if args.video_adapt:
            warnings.append("FMPose3D video inference does not run SuperAnimal video adaptation.")
        if args.customized_pose_checkpoint or args.customized_detector_checkpoint or args.customized_model_config:
            warnings.append(
                "The public video_inference_superanimal FMPose3D branch does not use the SuperAnimal customized_* checkpoint/config arguments."
            )
        if args.max_individuals != 1:
            warnings.append("FMPose3D video lifting is single-individual in this workflow; max_individuals will effectively be clamped to 1.")
    elif is_dlcrnet:
        if args.detector_name:
            warnings.append("dlcrnet uses the TensorFlow bottom-up branch; detector_name is not used.")
        if args.detector_batch_size != 1:
            warnings.append("detector_batch_size is a PyTorch detector setting and is not used by dlcrnet.")
        if args.customized_pose_checkpoint or args.customized_detector_checkpoint or args.customized_model_config:
            warnings.append("customized_* checkpoint/config arguments are PyTorch-only; dlcrnet will not use them.")
    else:
        if family != "superanimal_humanbody" and args.detector_name is None:
            errors.append("PyTorch top-down animal SuperAnimal inference requires --detector-name.")
        if family == "superanimal_humanbody":
            if args.detector_name is None:
                warnings.append("superanimal_humanbody will use the default filtered torchvision person detector.")
            if args.customized_detector_checkpoint:
                warnings.append("A custom detector checkpoint is not the normal human-body path; the human-body branch uses a filtered torchvision person detector.")
        if args.scale_list:
            warnings.append("scale_list is mainly useful for bottom-up dlcrnet; PyTorch top-down inference relies on detector/cropping choices.")

    if family == "superanimal_humanbody" and model not in {"rtmpose_x", "fmpose3d_humans"}:
        warnings.append("superanimal_humanbody is directly documented for rtmpose_x and fmpose3d_humans; verify other model choices before execution.")

    if args.check_paths:
        for video in videos:
            if not Path(video).exists():
                warnings.append(f"Video path does not currently exist: {video}")
        for label, value in (
            ("customized_pose_checkpoint", args.customized_pose_checkpoint),
            ("customized_detector_checkpoint", args.customized_detector_checkpoint),
            ("customized_model_config", args.customized_model_config),
        ):
            if value and not Path(value).exists():
                warnings.append(f"{label} does not currently exist: {value}")
        if args.dest_folder:
            parent = Path(args.dest_folder).expanduser().parent
            if parent and not parent.exists():
                warnings.append(f"Destination parent does not currently exist: {parent}")

    return errors, warnings, engine_route


def build_kwargs(args: argparse.Namespace, videos: list[str]) -> dict[str, Any]:
    return {
        "videos": videos,
        "superanimal_name": args.superanimal_name,
        "model_name": args.model_name,
        "detector_name": args.detector_name,
        "scale_list": args.scale_list,
        "video_extensions": args.video_extensions,
        "dest_folder": args.dest_folder,
        "cropping": args.cropping,
        "video_adapt": args.video_adapt,
        "plot_trajectories": args.plot_trajectories,
        "batch_size": args.batch_size,
        "detector_batch_size": args.detector_batch_size,
        "pcutoff": args.pcutoff,
        "adapt_iterations": args.adapt_iterations,
        "pseudo_threshold": args.pseudo_threshold,
        "bbox_threshold": args.bbox_threshold,
        "detector_epochs": args.detector_epochs,
        "pose_epochs": args.pose_epochs,
        "max_individuals": args.max_individuals,
        "video_adapt_batch_size": args.video_adapt_batch_size,
        "device": args.device,
        "customized_pose_checkpoint": args.customized_pose_checkpoint,
        "customized_detector_checkpoint": args.customized_detector_checkpoint,
        "customized_model_config": args.customized_model_config,
        "plot_bboxes": args.plot_bboxes,
        "create_labeled_video": args.create_labeled_video,
        "fmpose_return_3d": args.fmpose_return_3d,
    }


def render_call(kwargs: dict[str, Any]) -> str:
    lines = ["deeplabcut.video_inference_superanimal("]
    for key, value in kwargs.items():
        lines.append(f"    {key}={value!r},")
    lines.append(")")
    return "\n".join(lines)


def build_checklist(args: argparse.Namespace, engine_route: str, errors: list[str]) -> list[str]:
    checklist = [
        "Confirm the task really needs pretrained Model Zoo inference rather than a trained project snapshot.",
        "Confirm downloads/cache are allowed, or provide compatible custom checkpoints before execution.",
        "Confirm the selected SuperAnimal family matches the species/view and expected bodypart set.",
        "Use a short representative video first and inspect outputs before batch processing many videos.",
        "Set dest_folder intentionally so HDF5, JSON, and labeled-video outputs are easy to find.",
    ]
    if engine_route == "tensorflow":
        checklist.append("For dlcrnet, choose scale_list based on apparent animal size and TensorFlow availability.")
    elif engine_route == "pytorch":
        checklist.append("For PyTorch top-down animal models, confirm detector_name and detector weights are available.")
        checklist.append("Tune batch_size and detector_batch_size for available memory; reduce them before changing model choices.")
    else:
        checklist.append("For FMPose3D, confirm optional FMPose3D support is installed and treat the workflow as single-individual video lifting.")
    if args.video_adapt:
        checklist.append("For video_adapt, put the most representative video first and budget extra time for pseudo-label training.")
    if args.cropping:
        checklist.append("Verify cropping=[x1,x2,y1,y2] is valid for every video in the call; split calls when crops differ.")
    if args.scale_list:
        checklist.append("Verify scale_list values are appropriate for object size, not just full-frame resolution.")
    if not args.create_labeled_video:
        checklist.append("create_labeled_video=False means no labeled MP4 should be expected from this call.")
    if errors:
        checklist.append("Resolve listed errors before executing DeepLabCut.")
    return checklist


def print_markdown(payload: dict[str, Any]) -> None:
    print(f"# SuperAnimal inference plan: {payload['status']}")
    print(f"\nEngine route: `{payload['engine_route']}`")
    if payload["errors"]:
        print("\n## Errors")
        for item in payload["errors"]:
            print(f"- {item}")
    if payload["warnings"]:
        print("\n## Warnings")
        for item in payload["warnings"]:
            print(f"- {item}")
    print("\n## Planned call")
    print("```python")
    print("import deeplabcut")
    print(payload["python_call"])
    print("```")
    print("\n## Checklist")
    for item in payload["checklist"]:
        print(f"- {item}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    videos = list(args.video) + list(args.videos)
    errors, warnings, engine_route = validate(args, videos)
    kwargs = build_kwargs(args, videos)
    payload = {
        "status": "error" if errors else "ok",
        "engine_route": engine_route,
        "planned_kwargs": kwargs,
        "python_call": render_call(kwargs),
        "errors": errors,
        "warnings": warnings,
        "checklist": build_checklist(args, engine_route, errors),
        "no_download": True,
        "imports_deeplabcut": False,
    }
    if args.output == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_markdown(payload)
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
