#!/usr/bin/env python3
"""Plan Neuralangelo data-preparation commands without executing them.

The planner is intentionally safe and standalone. It prints shell command
templates and checklist notes for ffmpeg/COLMAP/data validation, but never runs
external tools, downloads datasets, imports Neuralangelo code, or launches
training.
"""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any


def q(value: str | Path) -> str:
    return shlex.quote(str(value))


def gpu_bool(value: str) -> str:
    normalized = value.lower()
    if normalized in {"true", "1", "yes", "y", "gpu", "cuda"}:
        return "true"
    if normalized in {"false", "0", "no", "n", "cpu"}:
        return "false"
    raise argparse.ArgumentTypeError("expected true/false")


def helper(prefix: str, name: str) -> str:
    return str(Path(prefix) / name)


def add_step(steps: list[dict[str, Any]], title: str, commands: list[str] | None = None, notes: list[str] | None = None) -> None:
    steps.append({"title": title, "commands": commands or [], "notes": notes or []})


def colmap_commands(data_dir: str, matcher: str, use_gpu: str, camera_model: str, num_threads: int, max_image_size: int | None) -> list[str]:
    database = f"{data_dir}/database.db"
    images_raw = f"{data_dir}/images_raw"
    sparse = f"{data_dir}/sparse"
    commands = [
        " ".join([
            "colmap feature_extractor",
            f"--database_path={q(database)}",
            f"--image_path={q(images_raw)}",
            f"--ImageReader.camera_model={shlex.quote(camera_model)}",
            "--ImageReader.single_camera=true",
            f"--SiftExtraction.use_gpu={use_gpu}",
            f"--SiftExtraction.num_threads={int(num_threads)}",
        ]),
        " ".join([
            f"colmap {matcher}_matcher",
            f"--database_path={q(database)}",
            f"--SiftMatching.use_gpu={use_gpu}",
        ]),
        f"mkdir -p {q(sparse)}",
        " ".join([
            "colmap mapper",
            f"--database_path={q(database)}",
            f"--image_path={q(images_raw)}",
            f"--output_path={q(sparse)}",
        ]),
        f"if [ -d {q(sparse + '/0')} ]; then cp {q(sparse + '/0')}/*.bin {q(sparse)}/; fi",
        "# If COLMAP produced sparse/1, sparse/2, ... inspect the trajectory before merging; broken models are better repaired than blindly trained.",
    ]
    undistort = [
        "colmap image_undistorter",
        f"--image_path={q(images_raw)}",
        f"--input_path={q(sparse)}",
        f"--output_path={q(data_dir)}",
        "--output_type=COLMAP",
    ]
    if max_image_size:
        undistort.append(f"--max_image_size={int(max_image_size)}")
    commands.append(" ".join(undistort))
    return commands


def plan_video(args: argparse.Namespace) -> list[dict[str, Any]]:
    data_dir = args.data_dir or f"datasets/{args.sequence_name}_ds{args.downsample_rate}"
    video = args.video or "<PATH_TO_VIDEO>"
    steps: list[dict[str, Any]] = []
    add_step(
        steps,
        "Select source and scene settings",
        notes=[
            f"sequence_name={args.sequence_name}",
            f"data_dir={data_dir}",
            f"scene_type={args.scene_type}",
            "Use object for object-centric captures, outdoor for building-scale scenes, indoor for room-scale scenes.",
        ],
    )
    add_step(
        steps,
        "Extract frames with ffmpeg",
        commands=[
            f"mkdir -p {q(data_dir + '/images_raw')}",
            f"ffmpeg -i {q(video)} -vf {q('select=not(mod(n\\,' + str(args.downsample_rate) + '))')} -vsync vfr -q:v 2 {q(data_dir + '/images_raw/%06d.jpg')}",
        ],
        notes=["Lower --downsample-rate if COLMAP registers too few frames."],
    )
    add_step(
        steps,
        "Run COLMAP and undistort images",
        commands=colmap_commands(data_dir, args.matcher, args.use_gpu, args.camera_model, args.num_threads, args.max_image_size),
        notes=["The Neuralangelo image set should end up under images/ after undistortion."],
    )
    add_transform_and_config_steps(steps, args, data_dir)
    return steps


def plan_colmap(args: argparse.Namespace) -> list[dict[str, Any]]:
    data_dir = args.data_dir or "<DATASET_WITH_COLMAP_OUTPUT>"
    steps: list[dict[str, Any]] = []
    add_step(
        steps,
        "Check existing COLMAP layout",
        commands=[
            f"test -d {q(data_dir + '/images')} || echo 'missing undistorted images/'",
            f"test -d {q(data_dir + '/sparse')} || echo 'missing sparse/'",
            f"find {q(data_dir + '/sparse')} -maxdepth 2 -type f \\( -name 'cameras.*' -o -name 'images.*' -o -name 'points3D.*' \\) -print",
        ],
        notes=[
            "Use the active sparse model that matches the image set.",
            "If only images_raw/ exists, run an undistortion step before using Neuralangelo data loading.",
        ],
    )
    add_transform_and_config_steps(steps, args, data_dir)
    return steps


def plan_dtu(args: argparse.Namespace) -> list[dict[str, Any]]:
    root = args.data_dir or "<DTU_ROOT>"
    steps: list[dict[str, Any]] = []
    add_step(
        steps,
        "Check DTU scan layout",
        commands=[
            f"find {q(root)} -maxdepth 2 -type f -name 'cameras_sphere.npz' -print",
            f"find {q(root)} -maxdepth 3 -type d -name image -print",
        ],
        notes=[
            "Validate dataset license and usage permissions before download or redistribution.",
            "Each scan should be converted and validated independently.",
            "DTU transforms often use sphere_center [0,0,0] and sphere_radius 1; aabb_range may be absent.",
        ],
    )
    add_step(
        steps,
        "For each converted scan, validate metadata",
        commands=[
            f"python {q(helper(args.helper_prefix, 'validate_transforms_json.py'))} --transforms {q(root + '/scanXX/transforms.json')} --data-dir {q(root + '/scanXX')} --allow-missing-images",
            f"python {q(helper(args.helper_prefix, 'generate_config_from_images.py'))} --data-dir {q(root + '/scanXX')} --images-subdir image --sequence-name scanXX --scene-type object --output {q(root + '/scanXX.yaml')}",
        ],
        notes=["Remove --allow-missing-images once the scan images are present in the target environment."],
    )
    return steps


def plan_tnt(args: argparse.Namespace) -> list[dict[str, Any]]:
    root = args.data_dir or "<TANKS_AND_TEMPLES_ROOT>"
    scene = args.sequence_name or "<Scene>"
    scene_dir = f"{root}/{scene}"
    steps: list[dict[str, Any]] = []
    add_step(
        steps,
        "Check Tanks-and-Temples scene layout",
        commands=[
            f"test -d {q(scene_dir + '/images_raw')} || echo 'missing images_raw/'",
            f"test -f {q(scene_dir + '/' + scene + '_COLMAP_SfM.log')} || echo 'missing pose log'",
            f"test -f {q(scene_dir + '/' + scene + '_trans.txt')} || echo 'missing alignment transform'",
            f"test -f {q(scene_dir + '/' + scene + '.ply')} || echo 'missing point cloud for bounds'",
        ],
        notes=[
            "The pose log, alignment transform, point cloud, crop file, and images must belong to the same scene.",
            "Large outdoor scenes usually use scene_type outdoor; room-like scenes may need indoor overrides.",
        ],
    )
    add_step(
        steps,
        "Run COLMAP feature/match/refinement if the scene needs it",
        commands=colmap_commands(scene_dir, args.matcher, args.use_gpu, "RADIAL", args.num_threads, args.max_image_size or 1500),
        notes=["TNT preparation often uses known poses plus bundle adjustment/undistortion before metadata export."],
    )
    add_transform_and_config_steps(steps, args, scene_dir)
    return steps


def add_transform_and_config_steps(steps: list[dict[str, Any]], args: argparse.Namespace, data_dir: str) -> None:
    transforms = f"{data_dir}/transforms.json"
    config_out = args.config_output or f"{data_dir}/{args.sequence_name}.yaml"
    config_cmd = [
        "python", q(helper(args.helper_prefix, "generate_config_from_images.py")),
        "--data-dir", q(data_dir),
        "--sequence-name", q(args.sequence_name),
        "--scene-type", q(args.scene_type),
        "--output", q(config_out),
    ]
    if args.auto_exposure_wb:
        config_cmd.append("--auto-exposure-wb")
    add_step(
        steps,
        "Create or collect transforms.json",
        notes=[
            "The final metadata must follow the Neuralangelo/Instant-NGP schema in references/data-formats.md.",
            "For COLMAP-derived data, ensure poses are converted from COLMAP/OpenCV convention to camera-to-world OpenGL/Instant-NGP convention.",
            "For DTU/TNT data, preserve dataset-specific normalization/alignment evidence in the handoff.",
        ],
    )
    add_step(
        steps,
        "Validate metadata and export camera centers for inspection",
        commands=[
            f"python {q(helper(args.helper_prefix, 'validate_transforms_json.py'))} --transforms {q(transforms)} --data-dir {q(data_dir)} --camera-centers-csv {q(data_dir + '/camera_centers.csv')}",
        ],
        notes=["Inspect the CSV with a plotting tool if poses or bounds are suspect."],
    )
    add_step(
        steps,
        "Generate Neuralangelo data config patch",
        commands=[" ".join(config_cmd)],
        notes=[
            "Review data.readjust.center and data.readjust.scale after inspecting bounds.",
            "Training launch and optimization settings are handled by training-and-configs.",
        ],
    )


def render_text(steps: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for index, step in enumerate(steps, 1):
        lines.append(f"## {index}. {step['title']}")
        for note in step.get("notes", []):
            lines.append(f"# {note}")
        for command in step.get("commands", []):
            lines.append(command)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_shell(steps: list[dict[str, Any]]) -> str:
    lines = ["#!/usr/bin/env bash", "set -euo pipefail", "", "# Planned commands. Review before running."]
    for index, step in enumerate(steps, 1):
        lines.append("")
        lines.append(f"# {index}. {step['title']}")
        for note in step.get("notes", []):
            lines.append(f"# - {note}")
        for command in step.get("commands", []):
            lines.append(command)
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print a safe Neuralangelo preprocessing command plan.")
    parser.add_argument("--mode", choices=["video", "colmap", "dtu", "tnt"], required=True)
    parser.add_argument("--sequence-name", default="scene", help="Sequence or scene name.")
    parser.add_argument("--video", default=None, help="Input video path for --mode video.")
    parser.add_argument("--downsample-rate", type=int, default=2, help="Temporal downsample rate for video frame extraction.")
    parser.add_argument("--data-dir", default=None, help="Dataset root, DTU root, or TNT root depending on mode.")
    parser.add_argument("--scene-type", choices=["outdoor", "indoor", "object"], default="outdoor")
    parser.add_argument("--matcher", choices=["sequential", "exhaustive"], default="sequential")
    parser.add_argument("--use-gpu", type=gpu_bool, default="true", help="true/false for COLMAP SIFT GPU flags.")
    parser.add_argument("--camera-model", default="SIMPLE_RADIAL", help="COLMAP camera model for self-captured video.")
    parser.add_argument("--num-threads", type=int, default=32, help="COLMAP SIFT extraction thread count.")
    parser.add_argument("--max-image-size", type=int, default=None, help="Optional COLMAP undistortion max image size.")
    parser.add_argument("--auto-exposure-wb", action="store_true", help="Include --auto-exposure-wb in generated config command.")
    parser.add_argument("--config-output", default=None, help="Output path for generated YAML config in the plan.")
    parser.add_argument("--helper-prefix", default="scripts", help="Prefix used for bundled helper script paths in printed commands.")
    parser.add_argument("--format", choices=["text", "shell", "json"], default="text")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.downsample_rate <= 0:
        raise SystemExit("--downsample-rate must be positive")
    if args.num_threads <= 0:
        raise SystemExit("--num-threads must be positive")
    if args.max_image_size is not None and args.max_image_size <= 0:
        raise SystemExit("--max-image-size must be positive")

    if args.mode == "video":
        steps = plan_video(args)
    elif args.mode == "colmap":
        steps = plan_colmap(args)
    elif args.mode == "dtu":
        steps = plan_dtu(args)
    elif args.mode == "tnt":
        steps = plan_tnt(args)
    else:  # argparse prevents this.
        raise SystemExit(f"unknown mode: {args.mode}")

    if args.format == "json":
        print(json.dumps({"mode": args.mode, "steps": steps}, indent=2))
    elif args.format == "shell":
        print(render_shell(steps), end="")
    else:
        print(render_text(steps), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
