#!/usr/bin/env python3
"""Plan or execute the LatentSync data-preparation pipeline.

This helper is an adapted wrapper around LatentSync's repo-maintained
`data_processing_pipeline.sh`, `preprocess/data_processing_pipeline.py`, and
individual `preprocess/*` stage modules. It keeps the original stage functions
as the execution backend while adding:

- explicit --repo-root support because the repo has no package metadata,
- dry-run planning by default,
- --start-at/--stop-after stage slicing for recovery and fixtures,
- prerequisite checks before GPU worker pools start,
- a destructive-input opt-in for the broken-video prune stage.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

DEFAULT_AUX_CHECKPOINTS = {
    "syncnet": Path("checkpoints/auxiliary/syncnet_v2.model"),
    "s3fd_face_detector": Path("checkpoints/auxiliary/sfd_face.pth"),
    "hyperiqa_koniq": Path("checkpoints/auxiliary/koniq_pretrained.pkl"),
}

REQUIRED_REPO_FILES = [
    Path("preprocess/data_processing_pipeline.py"),
    Path("data_processing_pipeline.sh"),
    Path("preprocess/remove_broken_videos.py"),
    Path("preprocess/resample_fps_hz.py"),
    Path("preprocess/detect_shot.py"),
    Path("preprocess/segment_videos.py"),
    Path("preprocess/affine_transform.py"),
    Path("preprocess/remove_incorrect_affined.py"),
    Path("preprocess/sync_av.py"),
    Path("preprocess/filter_high_resolution.py"),
    Path("preprocess/filter_visual_quality.py"),
    Path("latentsync/utils/av_reader.py"),
    Path("latentsync/utils/image_processor.py"),
    Path("latentsync/utils/face_detector.py"),
    Path("latentsync/utils/util.py"),
    Path("eval/syncnet_detect.py"),
    Path("eval/hyper_iqa.py"),
    Path("eval/syncnet/syncnet_eval.py"),
]

GPU_STAGE_KEYS = {"affine_transform", "sync_av", "filter_visual_quality"}


@dataclass(frozen=True)
class StageSpec:
    key: str
    label: str
    kind: str
    input_dir: str
    output_dir: str
    workers: str
    note: str
    optional: bool = False
    destructive: bool = False
    requires_gpu: bool = False


@dataclass(frozen=True)
class PipelinePlan:
    repo_root: str
    input_dir: str
    workspace_root: str
    temp_dir: str
    resolution: int
    sync_conf_threshold: int
    total_num_workers: int
    per_gpu_num_workers: int
    include_high_resolution: bool
    include_remove_incorrect_affined: bool
    start_at: str | None
    stop_after: str | None
    stages: list[StageSpec]


def resolve_relative(path_str: str, base: Path) -> Path:
    path = Path(path_str).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def stage_output_path(workspace_root: Path, stage_name: str, sync_conf_threshold: int) -> Path:
    if stage_name == "av_synced":
        return workspace_root / f"av_synced_{sync_conf_threshold}"
    return workspace_root / stage_name


def build_stage_specs(
    workspace_root: Path,
    input_dir: Path,
    resolution: int,
    sync_conf_threshold: int,
    total_num_workers: int,
    per_gpu_num_workers: int,
    include_high_resolution: bool,
    include_remove_incorrect_affined: bool,
) -> list[StageSpec]:
    resampled_dir = stage_output_path(workspace_root, "resampled", sync_conf_threshold)
    shot_dir = stage_output_path(workspace_root, "shot", sync_conf_threshold)
    segmented_dir = stage_output_path(workspace_root, "segmented", sync_conf_threshold)
    high_resolution_dir = stage_output_path(workspace_root, "high_resolution", sync_conf_threshold)
    affine_dir = stage_output_path(workspace_root, "affine_transformed", sync_conf_threshold)
    av_synced_dir = stage_output_path(workspace_root, "av_synced", sync_conf_threshold)
    high_visual_quality_dir = stage_output_path(workspace_root, "high_visual_quality", sync_conf_threshold)

    alignment_source = high_resolution_dir if include_high_resolution else segmented_dir
    align_workers = max(1, per_gpu_num_workers // 2)

    stages: list[StageSpec] = [
        StageSpec(
            key="remove_broken_videos",
            label="Remove broken videos",
            kind="cpu",
            input_dir=str(input_dir),
            output_dir=str(input_dir),
            workers=f"total_num_workers={total_num_workers}",
            note="Destructive in-place prune using AVReader; run only on a disposable raw tree.",
            destructive=True,
        ),
        StageSpec(
            key="resample_fps_hz",
            label="Resample FPS and audio rate",
            kind="cpu",
            input_dir=str(input_dir),
            output_dir=str(resampled_dir),
            workers=f"total_num_workers={total_num_workers}",
            note="Writes 25 FPS video and 16 kHz audio under the resampled sibling tree.",
        ),
        StageSpec(
            key="detect_shot",
            label="Detect shots",
            kind="cpu",
            input_dir=str(resampled_dir),
            output_dir=str(shot_dir),
            workers=f"total_num_workers={total_num_workers}",
            note="Uses the scenedetect CLI with adaptive threshold 2.",
        ),
        StageSpec(
            key="segment_videos",
            label="Segment videos",
            kind="cpu",
            input_dir=str(shot_dir),
            output_dir=str(segmented_dir),
            workers=f"total_num_workers={total_num_workers}",
            note="Splits shot clips into about 5-second segments.",
        ),
    ]

    if include_high_resolution:
        stages.append(
            StageSpec(
                key="filter_high_resolution",
                label="Filter high-resolution face clips",
                kind="cpu",
                input_dir=str(segmented_dir),
                output_dir=str(high_resolution_dir),
                workers=f"total_num_workers={total_num_workers}",
                note=f"Keeps clips whose detected face box is at least {resolution}x{resolution}.",
                optional=True,
            )
        )

    stages.append(
        StageSpec(
            key="affine_transform",
            label="Affine-transform faces",
            kind="gpu",
            input_dir=str(alignment_source),
            output_dir=str(affine_dir),
            workers=f"per_gpu_num_workers_for_alignment={align_workers}",
            note="CUDA/InsightFace alignment; skipped clips usually mean face detection failed.",
            requires_gpu=True,
        )
    )

    if include_remove_incorrect_affined:
        stages.append(
            StageSpec(
                key="remove_incorrect_affined",
                label="Remove incorrect affine outputs",
                kind="cpu",
                input_dir=str(affine_dir),
                output_dir=str(affine_dir),
                workers=f"total_num_workers={total_num_workers}",
                note="Optional destructive cleanup that requires one MediaPipe face in every aligned frame.",
                optional=True,
                destructive=True,
            )
        )

    stages.extend(
        [
            StageSpec(
                key="sync_av",
                label="Sync audio and video",
                kind="gpu",
                input_dir=str(affine_dir),
                output_dir=str(av_synced_dir),
                workers=f"per_gpu_num_workers={per_gpu_num_workers}",
                note=f"Keeps clips with SyncNet confidence >= {sync_conf_threshold} and |offset| <= 6.",
                requires_gpu=True,
            ),
            StageSpec(
                key="filter_visual_quality",
                label="Filter visual quality",
                kind="gpu",
                input_dir=str(av_synced_dir),
                output_dir=str(high_visual_quality_dir),
                workers=f"per_gpu_num_workers={per_gpu_num_workers}",
                note="Keeps clips with HyperIQA score >= 40.",
                requires_gpu=True,
            ),
        ]
    )

    return stages


def build_plan(args: argparse.Namespace) -> PipelinePlan:
    repo_root = resolve_relative(args.repo_root, Path.cwd())
    input_dir = resolve_relative(args.input_dir, repo_root)
    workspace_root = input_dir.parent.resolve()
    temp_dir = resolve_relative(args.temp_dir, repo_root)

    stages = build_stage_specs(
        workspace_root=workspace_root,
        input_dir=input_dir,
        resolution=args.resolution,
        sync_conf_threshold=args.sync_conf_threshold,
        total_num_workers=args.total_num_workers,
        per_gpu_num_workers=args.per_gpu_num_workers,
        include_high_resolution=args.include_high_resolution,
        include_remove_incorrect_affined=args.include_remove_incorrect_affined,
    )

    return PipelinePlan(
        repo_root=str(repo_root),
        input_dir=str(input_dir),
        workspace_root=str(workspace_root),
        temp_dir=str(temp_dir),
        resolution=args.resolution,
        sync_conf_threshold=args.sync_conf_threshold,
        total_num_workers=args.total_num_workers,
        per_gpu_num_workers=args.per_gpu_num_workers,
        include_high_resolution=args.include_high_resolution,
        include_remove_incorrect_affined=args.include_remove_incorrect_affined,
        start_at=args.start_at,
        stop_after=args.stop_after,
        stages=stages,
    )


def stage_key_index(stages: list[StageSpec], key: str) -> int:
    for index, stage in enumerate(stages):
        if stage.key == key:
            return index
    available = ", ".join(stage.key for stage in stages)
    raise SystemExit(f"Unknown stage '{key}'. Available stages: {available}")


def slice_stages(plan: PipelinePlan) -> list[StageSpec]:
    start_index = stage_key_index(plan.stages, plan.start_at) if plan.start_at else 0
    end_index = stage_key_index(plan.stages, plan.stop_after) if plan.stop_after else len(plan.stages) - 1
    if start_index > end_index:
        raise SystemExit(f"--start-at stage '{plan.start_at}' comes after --stop-after stage '{plan.stop_after}'.")
    return plan.stages[start_index : end_index + 1]


def plan_payload(plan: PipelinePlan) -> dict[str, Any]:
    selected = slice_stages(plan)
    return {
        "repo_root": plan.repo_root,
        "input_dir": plan.input_dir,
        "workspace_root": plan.workspace_root,
        "temp_dir": plan.temp_dir,
        "resolution": plan.resolution,
        "sync_conf_threshold": plan.sync_conf_threshold,
        "total_num_workers": plan.total_num_workers,
        "per_gpu_num_workers": plan.per_gpu_num_workers,
        "include_high_resolution": plan.include_high_resolution,
        "include_remove_incorrect_affined": plan.include_remove_incorrect_affined,
        "start_at": plan.start_at,
        "stop_after": plan.stop_after,
        "stages": [asdict(stage) for stage in selected],
    }


def print_plan(plan: PipelinePlan, json_output: bool = False) -> None:
    payload = plan_payload(plan)
    if json_output:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    print(f"Repo root: {payload['repo_root']}")
    print(f"Input dir: {payload['input_dir']}")
    print(f"Workspace root: {payload['workspace_root']}")
    print(f"Temp dir: {payload['temp_dir']}")
    print(f"Resolution: {payload['resolution']}")
    print(f"Sync threshold: {payload['sync_conf_threshold']}")
    print(f"CPU workers: {payload['total_num_workers']}")
    print(f"GPU workers per device: {payload['per_gpu_num_workers']}")
    print()
    for index, stage_payload in enumerate(payload["stages"], start=1):
        flags = [stage_payload["kind"]]
        if stage_payload["optional"]:
            flags.append("optional")
        if stage_payload["destructive"]:
            flags.append("destructive")
        if stage_payload["requires_gpu"]:
            flags.append("requires-gpu")
        print(f"{index}. {stage_payload['key']} [{', '.join(flags)}]")
        print(f"   {stage_payload['label']}")
        print(f"   input : {stage_payload['input_dir']}")
        print(f"   output: {stage_payload['output_dir']}")
        print(f"   work  : {stage_payload['workers']}")
        print(f"   note  : {stage_payload['note']}")


def ensure_repo_files(repo_root: Path) -> None:
    missing = [str(path) for path in REQUIRED_REPO_FILES if not (repo_root / path).exists()]
    if missing:
        raise SystemExit("Missing source anchors in repo root: " + ", ".join(missing))


def selected_requires_gpu(stages: list[StageSpec]) -> bool:
    return any(stage.requires_gpu or stage.key in GPU_STAGE_KEYS for stage in stages)


def missing_checkpoints(repo_root: Path) -> list[Path]:
    return [path for path in DEFAULT_AUX_CHECKPOINTS.values() if not (repo_root / path).exists()]


def download_missing_checkpoints(repo_root: Path, paths: list[Path], model_id: str) -> None:
    cli = shutil.which("huggingface-cli")
    if cli is None:
        raise SystemExit("Missing huggingface-cli; cannot download checkpoints. Install it or place checkpoints manually.")

    for rel_path in paths:
        # The source util downloads Path(*ckpt_path.parts[1:]) into local-dir checkpoints.
        remote_path = str(Path(*rel_path.parts[1:]))
        print(f"Downloading {remote_path} from {model_id} into {repo_root / 'checkpoints'}")
        result = subprocess.run(
            [cli, "download", model_id, remote_path, "--local-dir", str(repo_root / "checkpoints")],
            cwd=str(repo_root),
            check=False,
        )
        if result.returncode != 0:
            raise SystemExit(f"Checkpoint download failed for {remote_path} with exit code {result.returncode}.")

    still_missing = missing_checkpoints(repo_root)
    if still_missing:
        raise SystemExit("Checkpoint download completed but files are still missing: " + ", ".join(map(str, still_missing)))


def validate_prerequisites(repo_root: Path, stages: list[StageSpec], allow_downloads: bool, checkpoint_model_id: str) -> None:
    ensure_repo_files(repo_root)

    for stage in stages:
        if not Path(stage.input_dir).exists():
            raise SystemExit(
                f"Input directory for stage '{stage.key}' does not exist: {stage.input_dir}. "
                "If you are resuming, choose a --start-at stage whose upstream output tree is complete."
            )

    if not selected_requires_gpu(stages):
        return

    missing = missing_checkpoints(repo_root)
    if missing:
        if not allow_downloads:
            raise SystemExit(
                "Missing prerequisite checkpoints: "
                + ", ".join(str(path) for path in missing)
                + "\nPlace them under checkpoints/auxiliary/ or re-run with --allow-downloads if network fetches are acceptable."
            )
        download_missing_checkpoints(repo_root, missing, checkpoint_model_id)

    try:
        import torch  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on prepared env
        raise SystemExit(f"torch import failed before GPU stages: {exc}") from exc

    if torch.cuda.device_count() == 0:
        raise SystemExit("No CUDA devices are visible; selected stages require GPU support.")
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available to torch; selected stages require GPU support.")


def import_stage_functions(repo_root: Path, stages: list[StageSpec]) -> dict[str, Callable[..., object]]:
    module_map: dict[str, tuple[str, str]] = {
        "remove_broken_videos": ("preprocess.remove_broken_videos", "remove_broken_videos_multiprocessing"),
        "resample_fps_hz": ("preprocess.resample_fps_hz", "resample_fps_hz_multiprocessing"),
        "detect_shot": ("preprocess.detect_shot", "detect_shot_multiprocessing"),
        "segment_videos": ("preprocess.segment_videos", "segment_videos_multiprocessing"),
        "filter_high_resolution": ("preprocess.filter_high_resolution", "filter_high_resolution_multiprocessing"),
        "affine_transform": ("preprocess.affine_transform", "affine_transform_multi_gpus"),
        "remove_incorrect_affined": ("preprocess.remove_incorrect_affined", "remove_incorrect_affined_multiprocessing"),
        "sync_av": ("preprocess.sync_av", "sync_av_multi_gpus"),
        "filter_visual_quality": ("preprocess.filter_visual_quality", "filter_visual_quality_multi_gpus"),
    }

    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)

    funcs: dict[str, Callable[..., object]] = {}
    try:
        for stage in stages:
            module_name, attr_name = module_map[stage.key]
            module = importlib.import_module(module_name)
            funcs[stage.key] = getattr(module, attr_name)
    except Exception as exc:  # pragma: no cover - depends on prepared env
        raise SystemExit(
            "Failed to import selected pipeline modules from --repo-root. "
            "Make sure repo dependencies are installed and the checkout root is correct."
        ) from exc
    return funcs


def execute_stage(stage: StageSpec, plan: PipelinePlan, func: Callable[..., object]) -> None:
    if stage.key == "remove_broken_videos":
        func(stage.input_dir, plan.total_num_workers)
    elif stage.key == "resample_fps_hz":
        func(stage.input_dir, stage.output_dir, plan.total_num_workers)
    elif stage.key == "detect_shot":
        func(stage.input_dir, stage.output_dir, plan.total_num_workers)
    elif stage.key == "segment_videos":
        func(stage.input_dir, stage.output_dir, plan.total_num_workers)
    elif stage.key == "filter_high_resolution":
        func(stage.input_dir, stage.output_dir, plan.resolution, plan.total_num_workers)
    elif stage.key == "affine_transform":
        func(stage.input_dir, stage.output_dir, plan.temp_dir, plan.resolution, max(1, plan.per_gpu_num_workers // 2))
    elif stage.key == "remove_incorrect_affined":
        func(stage.input_dir, plan.total_num_workers)
    elif stage.key == "sync_av":
        func(stage.input_dir, stage.output_dir, plan.temp_dir, plan.per_gpu_num_workers, plan.sync_conf_threshold)
    elif stage.key == "filter_visual_quality":
        func(stage.input_dir, stage.output_dir, plan.per_gpu_num_workers)
    else:  # pragma: no cover - guarded by stage construction
        raise SystemExit(f"Unknown stage key: {stage.key}")


def execute_plan(plan: PipelinePlan, args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(plan.repo_root)
    selected = slice_stages(plan)

    if any(stage.destructive for stage in selected) and not args.allow_destructive_inputs:
        destructive_keys = ", ".join(stage.key for stage in selected if stage.destructive)
        raise SystemExit(
            "Refusing to execute destructive stage(s): "
            + destructive_keys
            + ". Re-run with --allow-destructive-inputs only after the affected tree is safely duplicated."
        )

    validate_prerequisites(repo_root, selected, args.allow_downloads, args.checkpoint_model_id)
    funcs = import_stage_functions(repo_root, selected)

    previous_cwd = Path.cwd()
    executed: list[str] = []
    os.chdir(repo_root)
    try:
        for index, stage in enumerate(selected, start=1):
            print(f"[{index}/{len(selected)}] {stage.key}: {stage.label}", flush=True)
            execute_stage(stage, plan, funcs[stage.key])
            executed.append(stage.key)
    finally:
        os.chdir(previous_cwd)

    return {
        "status": "completed",
        "workspace_root": plan.workspace_root,
        "input_dir": plan.input_dir,
        "temp_dir": plan.temp_dir,
        "stages_executed": executed,
        "start_at": plan.start_at,
        "stop_after": plan.stop_after,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan or run the LatentSync data-preparation pipeline.")
    parser.add_argument("--repo-root", type=str, default=".", help="LatentSync checkout to import pipeline modules from.")
    parser.add_argument("--input-dir", type=str, required=True, help="Raw video tree used to compute sibling stage outputs.")
    parser.add_argument("--temp-dir", type=str, default="temp", help="Scratch directory for GPU-backed stages.")
    parser.add_argument("--total-num-workers", type=int, default=96, help="Multiprocessing pool size for CPU stages.")
    parser.add_argument("--per-gpu-num-workers", type=int, default=12, help="Worker processes per visible GPU for GPU stages.")
    parser.add_argument("--resolution", type=int, default=256, help="Target aligned face resolution.")
    parser.add_argument("--sync-conf-threshold", type=int, default=3, help="Minimum SyncNet confidence for AV sync gate.")
    parser.add_argument("--include-high-resolution", action="store_true", help="Insert optional face-size prefilter before alignment.")
    parser.add_argument("--include-remove-incorrect-affined", action="store_true", help="Insert optional destructive affine cleanup.")
    parser.add_argument("--start-at", type=str, default=None, help="First stage key to plan/execute, useful for recovery.")
    parser.add_argument("--stop-after", type=str, default=None, help="Last stage key to plan/execute, useful for fixtures.")
    parser.add_argument("--execute", action="store_true", help="Execute selected stages instead of only printing the plan.")
    parser.add_argument(
        "--allow-destructive-inputs",
        action="store_true",
        help="Allow selected destructive stages to delete broken/raw or rejected files in place.",
    )
    parser.add_argument(
        "--allow-downloads",
        action="store_true",
        help="Allow the wrapper to fetch missing auxiliary checkpoints with huggingface-cli.",
    )
    parser.add_argument(
        "--checkpoint-model-id",
        type=str,
        default="ByteDance/LatentSync-1.5",
        help="Hugging Face model id for auxiliary checkpoint downloads when --allow-downloads is set.",
    )
    parser.add_argument("--json", action="store_true", help="Emit plan or final execution summary as JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_plan(args)

    if not args.execute:
        print_plan(plan, json_output=args.json)
        return 0

    result = execute_plan(plan, args)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Completed LatentSync data-preparation stages: {', '.join(result['stages_executed'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
