#!/usr/bin/env python3
"""Plan Sana evaluation launcher commands without executing benchmarks."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from textwrap import indent


@dataclass(frozen=True)
class MetricPlan:
    metric: str
    launcher: str
    inference_script: str
    notes: tuple[str, ...]
    warnings: tuple[str, ...]


PLANS = {
    "fid": MetricPlan(
        metric="fid",
        launcher="scripts/bash_run_inference_metric.sh",
        inference_script="scripts/inference.py",
        notes=("Uses FID and CLIP together by default.", "Expect MJHQ-30K images and cached reference embeddings."),
        warnings=("No separate benchmark env is required for the launcher itself.", "Disable wandb logging if auth is unavailable."),
    ),
    "clip": MetricPlan(
        metric="clip",
        launcher="scripts/bash_run_inference_metric.sh",
        inference_script="scripts/inference.py",
        notes=("Uses the same wrapper as FID.", "CLIP is usually planned together with FID."),
        warnings=("CLIP still depends on generated images and benchmark data.",),
    ),
    "geneval": MetricPlan(
        metric="geneval",
        launcher="scripts/bash_run_inference_metric_geneval.sh",
        inference_script="scripts/inference_geneval.py",
        notes=("Requires a dedicated GenEval environment.", "Uses the detector cache and GenEval prompts."),
        warnings=("The main Sana env is not enough for GenEval.",),
    ),
    "dpg": MetricPlan(
        metric="dpg",
        launcher="scripts/bash_run_inference_metric_dpg.sh",
        inference_script="scripts/inference_dpg.py",
        notes=("Requires a dedicated DPG environment.", "Plan with bs=1."),
        warnings=("Uses accelerator launch and benchmark CSV metadata.",),
    ),
    "image-reward": MetricPlan(
        metric="image-reward",
        launcher="scripts/bash_run_inference_metric_imagereward.sh",
        inference_script="scripts/inference_image_reward.py",
        notes=("Uses the benchmark prompt dictionary.", "Plan with bs=1."),
        warnings=("Wandb logging is optional and should be disabled when unavailable.",),
    ),
}


def load_model_paths(value: str) -> list[str]:
    path = Path(value)
    if not path.exists():
        return [value]
    if path.suffix != ".txt":
        return [value]
    lines = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            lines.append(stripped)
    return lines


def looks_remote(value: str) -> bool:
    return value.startswith(("hf://", "http://", "https://")) or value.count("/") == 1 and not value.endswith(".pth")


def path_warnings(config: str, model_paths_arg: str, model_paths: list[str]) -> list[str]:
    warnings: list[str] = []
    if not Path(config).exists():
        warnings.append("Config path is not present in the current working directory; verify the Sana checkout and config family.")
    model_paths_file = Path(model_paths_arg)
    if model_paths_arg.endswith(".txt") and not model_paths_file.exists():
        warnings.append("Checkpoint list file is missing; create it or pass a direct checkpoint path.")
    missing = [p for p in model_paths if not looks_remote(p) and not Path(p).exists()]
    if missing:
        preview = ", ".join(missing[:3])
        suffix = " ..." if len(missing) > 3 else ""
        warnings.append(f"Some checkpoint/model paths are not present locally: {preview}{suffix}")
    return warnings


def choose_metric(args: argparse.Namespace) -> MetricPlan:
    metric = args.metric.lower()
    if metric == "clipscore":
        metric = "clip"
    plan = PLANS.get(metric)
    if plan is None:
        raise SystemExit(f"Unsupported metric family: {args.metric}")
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan a Sana metric command without executing it.")
    parser.add_argument("--metric", required=True, help="Metric family: fid, clip, geneval, dpg, image-reward")
    parser.add_argument("--config", required=True, help="Sana config file path")
    parser.add_argument("--model-paths", required=True, help="Checkpoint path or .txt list")
    parser.add_argument("--sample-nums", type=int, default=None)
    parser.add_argument("--img-size", type=int, default=None)
    parser.add_argument("--bs", type=int, default=None)
    parser.add_argument("--cfg-scale", type=float, default=None)
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--tracker-project-name", default=None)
    parser.add_argument("--log", action="store_true", help="Request online logging in the plan")
    parser.add_argument("--json-out", action="store_true", help="Emit machine-readable JSON only")
    args = parser.parse_args()

    plan = choose_metric(args)
    model_paths = load_model_paths(args.model_paths)

    warnings = list(plan.warnings)
    warnings.extend(path_warnings(args.config, args.model_paths, model_paths))
    if args.metric.lower() in {"geneval", "dpg"}:
        warnings.append("Confirm the dedicated metric environment exists before running.")
    if args.log:
        warnings.append("Wandb logging requested; ensure credentials are available or disable logging.")

    command = ["bash", plan.launcher, args.config, args.model_paths]
    if args.sample_nums is not None:
        command.append(f"--sample_nums={args.sample_nums}")
    if args.img_size is not None:
        command.append(f"--img_size={args.img_size}")
    if args.bs is not None:
        command.append(f"--bs={args.bs}")
    if args.cfg_scale is not None:
        command.append(f"--cfg_scale={args.cfg_scale}")
    if args.dataset is not None:
        command.append(f"--dataset={args.dataset}")
    if args.tracker_project_name is not None:
        command.append(f"--tracker_project_name={args.tracker_project_name}")
    if args.log:
        log_flag = {
            "fid": "--log_fid=true",
            "clip": "--log_clip_score=true",
            "geneval": "--log_geneval=true",
            "dpg": "--log_dpg=true",
            "image-reward": "--log_image_reward=true",
        }[plan.metric]
        command.append(log_flag)

    payload = {
        "metric": plan.metric,
        "launcher": plan.launcher,
        "inference_script": plan.inference_script,
        "command": command,
        "model_path_count": len(model_paths),
        "notes": list(plan.notes),
        "warnings": warnings,
        "expected_env": "geneval" if plan.metric == "geneval" else "dpg" if plan.metric == "dpg" else "main Sana env",
        "safe_only": True,
    }

    if args.json_out:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Metric: {payload['metric']}")
        print(f"Launcher: {payload['launcher']}")
        print(f"Inference script: {payload['inference_script']}")
        print("Command:")
        print(indent(" ".join(command), "  "))
        print(f"Model paths: {len(model_paths)}")
        if payload["notes"]:
            print("Notes:")
            for note in payload["notes"]:
                print(f"  - {note}")
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
