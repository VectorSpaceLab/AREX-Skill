#!/usr/bin/env python3
"""Print canonical pix2pixHD training commands without launching training."""

from __future__ import annotations

import argparse
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class RecipeSpec:
    key: str
    summary: str
    args: tuple[str, ...]
    source_script: str
    notes: tuple[str, ...] = ()
    needs_feature_helpers: bool = False
    needs_apex: bool = False
    expected_gpu_count: int = 1
    expected_vram_gb: int | None = None


RECIPE_SPECS: dict[str, RecipeSpec] = {
    "512p": RecipeSpec(
        key="512p",
        summary="Baseline 512p label-only training",
        args=("python", "train.py", "--name", "label2city_512p"),
        source_script="scripts/train_512p.sh",
        notes=("Matches the README quick-start recipe.",),
        expected_vram_gb=11,
    ),
    "512p_feat": RecipeSpec(
        key="512p_feat",
        summary="512p feature-conditioned training",
        args=("python", "train.py", "--name", "label2city_512p_feat", "--instance_feat"),
        source_script="scripts/train_512p_feat.sh",
        notes=(
            "This recipe trains the encoder on the fly and does not require --load_features.",
            "If you also need cached maps, follow the separate instance-features workflow.",
        ),
        expected_vram_gb=11,
    ),
    "1024p_12G": RecipeSpec(
        key="1024p_12G",
        summary="1024p cropped training for limited VRAM",
        args=(
            "python",
            "train.py",
            "--name",
            "label2city_1024p",
            "--netG",
            "local",
            "--ngf",
            "32",
            "--num_D",
            "3",
            "--load_pretrain",
            "checkpoints/label2city_512p/",
            "--niter_fix_global",
            "20",
            "--resize_or_crop",
            "crop",
            "--fineSize",
            "1024",
        ),
        source_script="scripts/train_1024p_12G.sh",
        notes=("Cropping reduces memory at the cost of some fidelity.",),
        expected_vram_gb=12,
    ),
    "1024p_24G": RecipeSpec(
        key="1024p_24G",
        summary="1024p full-resolution training",
        args=(
            "python",
            "train.py",
            "--name",
            "label2city_1024p",
            "--netG",
            "local",
            "--ngf",
            "32",
            "--num_D",
            "3",
            "--load_pretrain",
            "checkpoints/label2city_512p/",
            "--niter",
            "50",
            "--niter_decay",
            "50",
            "--niter_fix_global",
            "10",
            "--resize_or_crop",
            "none",
        ),
        source_script="scripts/train_1024p_24G.sh",
        notes=("Uses the full image resolution and needs much more VRAM.",),
        expected_vram_gb=24,
    ),
    "1024p_feat_12G": RecipeSpec(
        key="1024p_feat_12G",
        summary="1024p cropped feature-conditioned training",
        args=(
            "python",
            "train.py",
            "--name",
            "label2city_1024p_feat",
            "--netG",
            "local",
            "--ngf",
            "32",
            "--num_D",
            "3",
            "--load_pretrain",
            "checkpoints/label2city_512p_feat/",
            "--niter_fix_global",
            "20",
            "--resize_or_crop",
            "crop",
            "--fineSize",
            "896",
            "--instance_feat",
            "--load_features",
        ),
        source_script="scripts/train_1024p_feat_12G.sh",
        notes=(
            "The feature-cache preparation step is handled by the instance-features workflow.",
            "This command only covers the training half of the recipe.",
        ),
        needs_feature_helpers=True,
        expected_vram_gb=12,
    ),
    "1024p_feat_24G": RecipeSpec(
        key="1024p_feat_24G",
        summary="1024p full-resolution feature-conditioned training",
        args=(
            "python",
            "train.py",
            "--name",
            "label2city_1024p_feat",
            "--netG",
            "local",
            "--ngf",
            "32",
            "--num_D",
            "3",
            "--load_pretrain",
            "checkpoints/label2city_512p_feat/",
            "--niter",
            "50",
            "--niter_decay",
            "50",
            "--niter_fix_global",
            "10",
            "--resize_or_crop",
            "none",
            "--instance_feat",
            "--load_features",
        ),
        source_script="scripts/train_1024p_feat_24G.sh",
        notes=(
            "The feature-cache preparation step is handled by the instance-features workflow.",
            "This command only covers the training half of the recipe.",
        ),
        needs_feature_helpers=True,
        expected_vram_gb=24,
    ),
    "512p_multigpu": RecipeSpec(
        key="512p_multigpu",
        summary="512p multi-GPU training",
        args=("python", "train.py", "--name", "label2city_512p", "--batchSize", "8", "--gpu_ids", "0,1,2,3,4,5,6,7"),
        source_script="scripts/train_512p_multigpu.sh",
        notes=("The training code uses DataParallel, not DDP.", "README says multi-GPU was not fully tested."),
        expected_gpu_count=8,
        expected_vram_gb=11,
    ),
    "512p_fp16": RecipeSpec(
        key="512p_fp16",
        summary="512p FP16 training",
        args=("python", "-m", "torch.distributed.launch", "train.py", "--name", "label2city_512p", "--fp16"),
        source_script="scripts/train_512p_fp16.sh",
        notes=("Legacy launcher style.", "Requires NVIDIA Apex."),
        needs_apex=True,
        expected_vram_gb=11,
    ),
    "512p_fp16_multigpu": RecipeSpec(
        key="512p_fp16_multigpu",
        summary="512p FP16 multi-GPU training",
        args=(
            "python",
            "-m",
            "torch.distributed.launch",
            "train.py",
            "--name",
            "label2city_512p",
            "--batchSize",
            "8",
            "--gpu_ids",
            "0,1,2,3,4,5,6,7",
            "--fp16",
        ),
        source_script="scripts/train_512p_fp16_multigpu.sh",
        notes=("Legacy launcher style.", "Requires NVIDIA Apex.", "The repo still relies on DataParallel under the hood."),
        needs_apex=True,
        expected_gpu_count=8,
        expected_vram_gb=11,
    ),
}


def list_recipes() -> list[RecipeSpec]:
    return [RECIPE_SPECS[key] for key in sorted(RECIPE_SPECS)]


def replace_flag(argv: Iterable[str], flag: str, value: str) -> list[str]:
    out: list[str] = []
    argv = list(argv)
    i = 0
    replaced = False
    while i < len(argv):
        if argv[i] == flag and i + 1 < len(argv):
            out.extend([flag, value])
            replaced = True
            i += 2
        else:
            out.append(argv[i])
            i += 1
    if not replaced:
        out.extend([flag, value])
    return out


def build_command(repo_root: Path, recipe_key: str, *, name_override: str | None = None, debug_smoke: bool = False) -> tuple[str, RecipeSpec]:
    if recipe_key not in RECIPE_SPECS:
        raise KeyError(f"Unknown recipe: {recipe_key}")
    spec = RECIPE_SPECS[recipe_key]
    args = list(spec.args)
    if name_override:
        args = replace_flag(args, "--name", name_override)
    if debug_smoke:
        args.extend(["--debug", "--no_vgg_loss", "--save_latest_freq", "1", "--save_epoch_freq", "1"])
    command = f"cd {shlex.quote(str(repo_root))} && {' '.join(shlex.quote(part) for part in args)}"
    return command, spec


def validate_repo_root(repo_root: Path, spec: RecipeSpec) -> list[str]:
    required = ["train.py", "models", "options", "scripts"]
    if spec.needs_feature_helpers:
        required.extend(["encode_features.py", "precompute_feature_maps.py"])
    missing = [name for name in required if not (repo_root / name).exists()]
    return missing


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print canonical pix2pixHD training commands without launching training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", default=".", help="Path to the pix2pixHD repository root.")
    parser.add_argument("--recipe", choices=sorted(RECIPE_SPECS), required=False, help="Canonical recipe to print.")
    parser.add_argument("--name", help="Override the --name argument for the selected recipe.")
    parser.add_argument("--debug-smoke", action="store_true", help="Append a bounded debug/checkpoint-smoke overlay.")
    parser.add_argument("--validate", action="store_true", help="Check that the repository root contains the expected source files.")
    parser.add_argument("--list-recipes", action="store_true", help="List available recipes and exit.")
    parser.add_argument("--with-notes", action="store_true", help="Print source and trade-off notes before the command.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list_recipes:
        for spec in list_recipes():
            print(f"{spec.key}: {spec.summary} ({spec.source_script})")
        return 0

    if not args.recipe:
        print("--recipe is required unless --list-recipes is used.", file=sys.stderr)
        return 2

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"Repository root does not exist: {repo_root}", file=sys.stderr)
        return 2

    command, spec = build_command(repo_root, args.recipe, name_override=args.name, debug_smoke=args.debug_smoke)

    if args.validate:
        missing = validate_repo_root(repo_root, spec)
        if missing:
            print("Missing expected files for this recipe:", file=sys.stderr)
            for item in missing:
                print(f"- {repo_root / item}", file=sys.stderr)
            return 2

    if args.with_notes:
        print(f"# recipe: {spec.key} — {spec.summary}")
        print(f"# source: {spec.source_script}")
        for note in spec.notes:
            print(f"# note: {note}")
        if spec.needs_feature_helpers:
            print("# feature workflow: see ../instance-features/SKILL.md for cache preparation")
        if spec.needs_apex:
            print("# fp16 workflow: requires NVIDIA Apex")
    print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
