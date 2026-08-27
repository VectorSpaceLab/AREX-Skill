#!/usr/bin/env python3
"""Dry-run KAIR image test command builder.

The helper prints KAIR commands for common argparse image-test entry points. It
never imports KAIR, never downloads checkpoints, and never runs inference.
"""
from __future__ import annotations

import argparse
import shlex
from dataclasses import dataclass
from typing import Dict, List, Optional


def q(value: object) -> str:
    return shlex.quote(str(value))


DN_MODEL_GROUP = {"dncnn_15", "dncnn_25", "dncnn_50", "dncnn_gray_blind", "dncnn_color_blind", "dncnn3"}


@dataclass(frozen=True)
class SwinIRPreset:
    task: str
    model_path: str
    needs_lq: bool
    needs_gt: bool
    window: int
    notes: str


def swinir_model_path(task: str, scale: int, noise: int, jpeg: int, training_patch_size: int, large_model: bool) -> SwinIRPreset:
    if task == "classical_sr":
        patch = 64 if training_patch_size == 64 else 48
        dataset = "DF2K" if patch == 64 else "DIV2K"
        return SwinIRPreset(task, f"model_zoo/swinir/001_classicalSR_{dataset}_s{patch}w8_SwinIR-M_x{scale}.pth", True, True, 8, "paired LR/GT folders; training_patch_size selects checkpoint family")
    if task == "lightweight_sr":
        return SwinIRPreset(task, f"model_zoo/swinir/002_lightweightSR_DIV2K_s64w8_SwinIR-S_x{scale}.pth", True, True, 8, "paired LR/GT folders")
    if task == "real_sr":
        name = "003_realSR_BSRGAN_DFOWMFC_s64w8_SwinIR-L_x4_GAN.pth" if large_model else "003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x4_GAN.pth"
        return SwinIRPreset(task, f"model_zoo/swinir/{name}", True, False, 8, "LQ-only real-world SR; add --large_model only with the large checkpoint")
    if task == "gray_dn":
        return SwinIRPreset(task, f"model_zoo/swinir/004_grayDN_DFWB_s128w8_SwinIR-M_noise{noise}.pth", False, True, 8, "clean GT folder; script generates grayscale noise")
    if task == "color_dn":
        return SwinIRPreset(task, f"model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise{noise}.pth", False, True, 8, "clean GT folder; script generates color noise")
    if task == "jpeg_car":
        return SwinIRPreset(task, f"model_zoo/swinir/006_CAR_DFWB_s126w7_SwinIR-M_jpeg{jpeg}.pth", False, True, 7, "clean GT folder; script generates JPEG artifacts and reports PSNR-B")
    raise SystemExit(f"Unsupported SwinIR task: {task}")


def build_dncnn(args: argparse.Namespace) -> int:
    if args.model_name not in DN_MODEL_GROUP:
        print(f"WARN: {args.model_name!r} is not one of the documented DnCNN names: {sorted(DN_MODEL_GROUP)}")
    cmd: List[str] = [
        "python", "main_test_dncnn.py",
        "--model_name", args.model_name,
        "--testset_name", args.testset_name,
        "--noise_level_img", str(args.noise_level),
        "--model_pool", args.model_pool,
        "--testsets", args.testsets,
        "--results", args.results,
    ]
    if args.no_degradation:
        cmd += ["--need_degradation", "False"]
    if args.x8:
        cmd += ["--x8", "True"]
    print(" ".join(q(part) for part in cmd))
    print("NOTE: This is a dry-run command. Full inference requires a local checkpoint and images.")
    return 0


def build_swinir(args: argparse.Namespace) -> int:
    preset = swinir_model_path(args.task, args.scale, args.noise, args.jpeg, args.training_patch_size, args.large_model)
    cmd: List[str] = [
        "python", "main_test_swinir.py",
        "--task", args.task,
        "--scale", str(args.scale),
        "--model_path", args.model_path or preset.model_path,
    ]
    if args.task in {"gray_dn", "color_dn"}:
        cmd += ["--noise", str(args.noise)]
    if args.task == "jpeg_car":
        cmd += ["--jpeg", str(args.jpeg)]
    if args.task == "classical_sr":
        cmd += ["--training_patch_size", str(args.training_patch_size)]
    if args.large_model:
        cmd.append("--large_model")
    if preset.needs_lq:
        if not args.folder_lq:
            print("ERROR: this SwinIR task needs --folder-lq")
            return 2
        cmd += ["--folder_lq", args.folder_lq]
    if preset.needs_gt:
        if not args.folder_gt:
            print("ERROR: this SwinIR task needs --folder-gt")
            return 2
        cmd += ["--folder_gt", args.folder_gt]
    if args.tile is not None:
        if args.tile % preset.window != 0:
            print(f"WARN: tile {args.tile} is not a multiple of SwinIR window size {preset.window} for task {args.task}.")
        cmd += ["--tile", str(args.tile)]
    if args.tile_overlap is not None:
        cmd += ["--tile_overlap", str(args.tile_overlap)]
    print(" ".join(q(part) for part in cmd))
    print(f"NOTE: {preset.notes}")
    print("NOTE: If the model path is missing, the original KAIR script may attempt a network download.")
    return 0


HARDCODED: Dict[str, str] = {
    "fdncnn": "main_test_fdncnn.py; patch model_name/testset_name/noise constants inside a working copy.",
    "ffdnet": "main_test_ffdnet.py; patch model_name/testset_name/noise constants inside a working copy.",
    "ircnn": "main_test_ircnn_denoiser.py; patch model_name and noise_level_img.",
    "dncnn3-deblocking": "main_test_dncnn3_deblocking.py; patch testset/model/channel constants.",
    "srmd": "main_test_srmd.py; patch model_name and testset_name; scale is inferred from checkpoint name.",
    "dpsr": "main_test_dpsr.py; patch model_name/testset/noise constants.",
    "msrresnet": "main_test_msrresnet.py; patch model_name and testset_name.",
    "rrdb": "main_test_rrdb.py; patch model_name and verify RRDB/ESRGAN checkpoint filename compatibility.",
    "imdn": "main_test_imdn.py; patch model_name/testset_name; also used by challenge profiling.",
    "usrnet": "main_test_usrnet.py; patch model_name/testset_name and ensure kernels/*.mat exists.",
    "face": "main_test_face_enhancement.py; requires RetinaFace and GPEN weights plus models/op import path.",
    "challenge": "main_challenge_sr.py; reference-only profiling script requiring CUDA for runtime/memory metrics.",
}


def hardcoded(args: argparse.Namespace) -> int:
    if args.family == "list":
        for key in sorted(HARDCODED):
            print(f"{key}: {HARDCODED[key]}")
        return 0
    if args.family not in HARDCODED:
        print(f"ERROR: unknown hard-coded family {args.family!r}; use --family list")
        return 2
    print(HARDCODED[args.family])
    print("NOTE: This helper does not patch or execute hard-coded scripts. Copy/patch deliberately in the user's KAIR checkout.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Print dry-run commands for KAIR image testing workflows.")
    sub = parser.add_subparsers(dest="mode", required=True)

    p = sub.add_parser("dncnn", help="Build a main_test_dncnn.py command.")
    p.add_argument("--model-name", default="dncnn_25")
    p.add_argument("--testset-name", default="set12")
    p.add_argument("--noise-level", type=int, default=25)
    p.add_argument("--model-pool", default="model_zoo")
    p.add_argument("--testsets", default="testsets")
    p.add_argument("--results", default="results")
    p.add_argument("--no-degradation", action="store_true")
    p.add_argument("--x8", action="store_true")
    p.set_defaults(func=build_dncnn)

    p = sub.add_parser("swinir", help="Build a main_test_swinir.py command.")
    p.add_argument("--task", choices=["classical_sr", "lightweight_sr", "real_sr", "gray_dn", "color_dn", "jpeg_car"], required=True)
    p.add_argument("--scale", type=int, default=4)
    p.add_argument("--noise", type=int, default=25)
    p.add_argument("--jpeg", type=int, default=30)
    p.add_argument("--training-patch-size", type=int, default=64)
    p.add_argument("--large-model", action="store_true")
    p.add_argument("--model-path", default=None)
    p.add_argument("--folder-lq", default=None)
    p.add_argument("--folder-gt", default=None)
    p.add_argument("--tile", type=int, default=None)
    p.add_argument("--tile-overlap", type=int, default=None)
    p.set_defaults(func=build_swinir)

    p = sub.add_parser("hardcoded", help="Explain how to handle hard-coded image test scripts.")
    p.add_argument("--family", default="list", help="Family name or 'list'.")
    p.set_defaults(func=hardcoded)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
