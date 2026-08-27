#!/usr/bin/env python3
"""Plan Sana conversion/export commands without executing conversion jobs."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from textwrap import indent


@dataclass(frozen=True)
class ConversionPlan:
    family: str
    script: str
    notes: tuple[str, ...]
    warnings: tuple[str, ...]


def choose_family(args: argparse.Namespace) -> ConversionPlan:
    family = args.family.lower()
    mapping = {
        "sana-image": ConversionPlan(
            family="sana-image",
            script="tools/convert_scripts/convert_sana_to_diffusers.py",
            notes=("Converts image-family `.pth` checkpoints to a diffusers directory.", "Supports full-pipeline export or transformer-only export."),
            warnings=("Check model_type, image_size, and dtype before planning.",),
        ),
        "sana-video": ConversionPlan(
            family="sana-video",
            script="tools/convert_scripts/convert_sana_video_to_diffusers.py",
            notes=("Converts Sana video checkpoints to a diffusers video pipeline.", "Supports t2v and i2v tasks."),
            warnings=("Confirm scheduler and video size before planning.",),
        ),
        "svdquant": ConversionPlan(
            family="svdquant",
            script="tools/convert_scripts/convert_sana_to_svdquant.py",
            notes=("Prepares a quantization-friendly image pipeline.", "Use only when an SVDQuant/Nunchaku path is intended."),
            warnings=("Confirm the model family is supported by the quantization path.",),
        ),
    }
    plan = mapping.get(family)
    if plan is None:
        raise SystemExit(f"Unsupported conversion family: {args.family}")
    return plan


def looks_remote(value: str | None) -> bool:
    if not value:
        return False
    return value.startswith(("hf://", "http://", "https://")) or value.count("/") == 1 and not value.endswith(".pth")


def supported_warnings(args: argparse.Namespace, plan: ConversionPlan) -> list[str]:
    warnings = list(plan.warnings)
    if args.orig_ckpt_path and not looks_remote(args.orig_ckpt_path) and not Path(args.orig_ckpt_path).exists():
        warnings.append("Source checkpoint path is not present locally; verify it before executing conversion.")
    image_types = {
        "SanaMS_1600M_P1_D20",
        "SanaMS_600M_P1_D28",
        "SanaMS1.5_1600M_P1_D20",
        "SanaMS1.5_4800M_P1_D60",
        "SanaSprint_1600M_P1_D20",
        "SanaSprint_600M_P1_D28",
        "SanaSprint_1600M_1024px_teacher",
        "SanaSprint_600M_1024px_teacher",
    }
    svd_types = image_types - {"SanaSprint_1600M_1024px_teacher", "SanaSprint_600M_1024px_teacher"}
    if plan.family == "sana-image" and args.model_type and args.model_type not in image_types:
        warnings.append("Model type is not in the image converter support list.")
    if plan.family == "svdquant" and args.model_type and args.model_type not in svd_types:
        warnings.append("Model type is not in the SVDQuant converter support list.")
    if plan.family == "sana-video" and args.model_type and args.model_type != "SanaVideo":
        warnings.append("Video conversion expects model_type SanaVideo.")
    if args.dtype and args.dtype not in {"fp32", "fp16", "bf16"}:
        warnings.append("Unsupported dtype; choose fp32, fp16, or bf16.")
    if args.image_size and args.image_size not in {512, 1024, 2048, 4096}:
        warnings.append("Unsupported image size for Sana image conversion.")
    if args.video_size and args.video_size not in {480, 720}:
        warnings.append("Unsupported video size for Sana video conversion.")
    if plan.family == "sana-video" and args.task == "i2v" and args.scheduler_type not in {None, "flow-euler"}:
        warnings.append("i2v video conversion requires the flow-euler scheduler path.")
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan a Sana conversion command without executing it.")
    parser.add_argument("--family", required=True, help="Conversion family: sana-image, sana-video, svdquant")
    parser.add_argument("--orig-ckpt-path", default=None)
    parser.add_argument("--model-type", default=None)
    parser.add_argument("--dtype", default=None)
    parser.add_argument("--dump-path", required=True)
    parser.add_argument("--image-size", type=int, default=None)
    parser.add_argument("--video-size", type=int, default=None)
    parser.add_argument("--scheduler-type", default=None)
    parser.add_argument("--task", default=None)
    parser.add_argument("--save-full-pipeline", action="store_true")
    parser.add_argument("--json-out", action="store_true")
    args = parser.parse_args()

    plan = choose_family(args)
    dump_path = Path(args.dump_path)

    command = ["python", plan.script]
    if args.orig_ckpt_path is not None:
        command.append(f"--orig_ckpt_path={args.orig_ckpt_path}")
    if args.model_type is not None:
        command.append(f"--model_type={args.model_type}")
    if args.dtype is not None:
        command.append(f"--dtype={args.dtype}")
    if args.image_size is not None:
        command.append(f"--image_size={args.image_size}")
    if args.video_size is not None:
        command.append(f"--video_size={args.video_size}")
    if args.scheduler_type is not None:
        command.append(f"--scheduler_type={args.scheduler_type}")
    if args.task is not None:
        command.append(f"--task={args.task}")
    if args.save_full_pipeline:
        command.append("--save_full_pipeline")
    command.append(f"--dump_path={dump_path}")

    warnings = supported_warnings(args, plan)
    if not dump_path.parent.exists():
        warnings.append("Parent directory does not exist yet; create or confirm it before executing the conversion.")
    if args.model_type is None:
        warnings.append("Model type is required for a reliable conversion plan.")
    if args.dtype is None:
        warnings.append("Precision should be made explicit in the plan.")

    payload = {
        "family": plan.family,
        "script": plan.script,
        "command": command,
        "notes": list(plan.notes),
        "warnings": warnings,
        "safe_only": True,
    }

    if args.json_out:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Family: {payload['family']}")
        print(f"Script: {payload['script']}")
        print("Command:")
        print(indent(" ".join(command), "  "))
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
