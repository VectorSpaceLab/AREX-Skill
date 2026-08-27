#!/usr/bin/env python3
"""Build a safe torchtune `tune run` command without executing it.

The script is intentionally side-effect free: it validates command shape against a
small bundled recipe capability table and prints the command to run after human
approval. It does not import torchtune, touch GPUs, read configs, or launch jobs.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class RecipeInfo:
    supports_distributed: bool
    note: str


RECIPE_REGISTRY: dict[str, RecipeInfo] = {
    "dev/grpo_full_finetune_distributed": RecipeInfo(True, "experimental distributed GRPO"),
    "dev/async_grpo_full_finetune_distributed": RecipeInfo(False, "experimental async GRPO; may require async RL extras"),
    "full_finetune_single_device": RecipeInfo(False, "single-device full finetune"),
    "full_finetune_distributed": RecipeInfo(True, "distributed full finetune"),
    "lora_finetune_single_device": RecipeInfo(False, "single-device LoRA/QLoRA/DoRA finetune"),
    "lora_dpo_single_device": RecipeInfo(False, "single-device LoRA DPO"),
    "lora_dpo_distributed": RecipeInfo(True, "distributed LoRA DPO"),
    "full_dpo_distributed": RecipeInfo(True, "distributed full DPO"),
    "ppo_full_finetune_single_device": RecipeInfo(False, "single-device PPO RLHF"),
    "lora_finetune_distributed": RecipeInfo(True, "distributed LoRA/QLoRA/DoRA finetune"),
    "dev/lora_finetune_distributed_multi_dataset": RecipeInfo(True, "experimental multi-dataset LoRA"),
    "dev/early_exit_finetune_distributed": RecipeInfo(True, "experimental early-exit finetune"),
    "qat_single_device": RecipeInfo(False, "single-device QAT"),
    "qat_distributed": RecipeInfo(True, "distributed QAT"),
    "qat_lora_finetune_distributed": RecipeInfo(True, "distributed QAT LoRA finetune"),
    "knowledge_distillation_single_device": RecipeInfo(False, "single-device KD"),
    "knowledge_distillation_distributed": RecipeInfo(True, "distributed KD"),
}


_WARNINGS: tuple[tuple[str, str], ...] = (
    ("bitsandbytes", "uses optional bitsandbytes; confirm package/backend before executing"),
    ("wandb", "uses optional W&B logging; confirm wandb install/login before executing"),
    ("comet", "uses optional Comet logging; confirm comet_ml install/login before executing"),
    ("quantize_base=True", "uses QLoRA/QDoRA base quantization; confirm torchao/NF4 runtime support"),
    ("Int8DynActInt4WeightQATQuantizer", "uses QAT quantizer; follow QAT flow and later quantize conversion separately"),
    ("async_grpo", "uses experimental async GRPO; confirm async RL extras before executing"),
)


def _add_torchrun_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--nnodes", help="torchrun node count, placed before the recipe")
    parser.add_argument("--nproc-per-node", "--nproc_per_node", dest="nproc_per_node", help="torchrun workers per node")
    parser.add_argument("--rdzv-id", "--rdzv_id", dest="rdzv_id", help="torchrun rendezvous id")
    parser.add_argument("--rdzv-backend", "--rdzv_backend", dest="rdzv_backend", help="torchrun rendezvous backend")
    parser.add_argument("--rdzv-endpoint", "--rdzv_endpoint", dest="rdzv_endpoint", help="torchrun rendezvous endpoint host:port")
    parser.add_argument("--standalone", action="store_true", help="pass torchrun standalone mode")
    parser.add_argument("--max-restarts", "--max_restarts", dest="max_restarts", help="torchrun max restarts")
    parser.add_argument("--monitor-interval", "--monitor_interval", dest="monitor_interval", help="torchrun monitor interval")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a safe torchtune `tune run` command without executing it.",
        epilog=(
            "Example: build_tune_command.py lora_finetune_distributed llama3_2/3B_lora "
            "--nnodes 2 --nproc-per-node 8 --rdzv-endpoint head:29500 "
            "--override output_dir=./runs/lora"
        ),
    )
    parser.add_argument("recipe", help="Registry recipe name, e.g. lora_finetune_distributed")
    parser.add_argument("config", help="Registry config name or local YAML path")
    _add_torchrun_arguments(parser)
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Recipe/config override appended after --config; repeatable. Deletions such as '~optimizer.foreach' are allowed.",
    )
    parser.add_argument(
        "--allow-unknown-recipe",
        action="store_true",
        help="Allow custom recipe names/paths that are not in the bundled registry table.",
    )
    parser.add_argument(
        "--print-notes",
        action="store_true",
        help="Print safety notes and warnings after the command.",
    )
    return parser.parse_args(argv)


def torchrun_flags(args: argparse.Namespace) -> list[str]:
    mapping = [
        ("nnodes", "--nnodes"),
        ("nproc_per_node", "--nproc_per_node"),
        ("rdzv_id", "--rdzv_id"),
        ("rdzv_backend", "--rdzv_backend"),
        ("rdzv_endpoint", "--rdzv_endpoint"),
        ("max_restarts", "--max_restarts"),
        ("monitor_interval", "--monitor_interval"),
    ]
    flags: list[str] = []
    for attr, flag in mapping:
        value = getattr(args, attr)
        if value is not None:
            flags.extend([flag, value])
    if args.standalone:
        flags.append("--standalone")
    return flags


def validate(args: argparse.Namespace, launcher_flags: list[str]) -> list[str]:
    warnings: list[str] = []
    info = RECIPE_REGISTRY.get(args.recipe)
    if info is None and not args.allow_unknown_recipe:
        known = ", ".join(sorted(RECIPE_REGISTRY))
        raise SystemExit(
            f"Unknown bundled recipe {args.recipe!r}. Use --allow-unknown-recipe for a custom recipe.\n"
            f"Known training recipes: {known}"
        )
    if info is not None and launcher_flags and not info.supports_distributed:
        raise SystemExit(
            f"Recipe {args.recipe!r} is registry-marked non-distributed ({info.note}). "
            "Remove torchrun flags or choose a distributed recipe/config."
        )
    for override in args.override:
        if not override.startswith("~") and "=" not in override:
            raise SystemExit(
                f"Override {override!r} is not KEY=VALUE or ~KEY deletion syntax."
            )
    text = " ".join([args.recipe, args.config, *args.override])
    for needle, warning in _WARNINGS:
        if needle in text:
            warnings.append(warning)
    if args.recipe.startswith("dev/"):
        warnings.append("dev recipe selected; treat as experimental and verify current dependencies")
    if launcher_flags:
        warnings.append("torchrun flags are placed before the recipe; keep config overrides after --config")
    return warnings


def quote_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    launcher_flags = torchrun_flags(args)
    warnings = validate(args, launcher_flags)
    command = ["tune", "run", *launcher_flags, args.recipe, "--config", args.config, *args.override]
    print(quote_command(command))
    if args.print_notes:
        print("\nSafety notes:")
        print("- This script only prints a command; it never executes training.")
        print("- Confirm GPUs/cluster, credentials, checkpoints, dataset, optional packages, and output_dir before running.")
        for warning in warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
