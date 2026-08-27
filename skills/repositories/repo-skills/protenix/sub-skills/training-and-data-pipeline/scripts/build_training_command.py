#!/usr/bin/env python3
"""Build Protenix training commands without launching training.

This helper intentionally uses only the Python standard library. It does not
import Protenix, inspect CUDA, download data, initialize W&B, or execute the
generated command.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any

TRIANGLE_ATTENTION = ("triattention", "cuequivariance", "deepspeed", "torch")
TRIANGLE_MULTIPLICATIVE = ("cuequivariance", "torch")
DATASET_2024 = "weightedPDB_before2109_wopb_nometalc_0925"
TESTSETS_DEFAULT = "recentPDB_1536_sample384_0925,posebusters_0925"


def str_to_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected true/false, got {value!r}")


def add_bool_argument(parser: argparse.ArgumentParser, name: str, default: bool, help_text: str) -> None:
    parser.add_argument(
        f"--{name}",
        type=str_to_bool,
        default=default,
        metavar="true|false",
        help=help_text,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a Protenix runner.train command without importing Protenix, "
            "checking CUDA, downloading data, initializing W&B, or launching training."
        )
    )
    parser.add_argument("--mode", choices=("train", "finetune"), default="train", help="Command pattern to build.")
    parser.add_argument(
        "--data-root",
        default=os.environ.get("PROTENIX_ROOT_DIR"),
        help="Value to use for PROTENIX_ROOT_DIR in the printed command. Defaults to current environment value.",
    )
    parser.add_argument("--base-dir", default="./output", help="Training output base directory.")
    parser.add_argument("--project", default="protenix", help="Training project name.")
    parser.add_argument("--run-name", default=None, help="Run name. Defaults by --mode.")
    parser.add_argument("--model-name", default="protenix_base_default_v1.0.0", help="Training model config/checkpoint name.")
    parser.add_argument("--seed", type=int, default=42, help="Training seed.")
    parser.add_argument("--dtype", choices=("bf16", "fp32", "fp16"), default="bf16", help="Training dtype.")
    parser.add_argument("--train-sets", default=DATASET_2024, help="Comma-separated data.train_sets value.")
    parser.add_argument("--test-sets", default=TESTSETS_DEFAULT, help="Comma-separated data.test_sets value.")
    parser.add_argument("--diffusion-batch-size", type=int, default=48, help="Training diffusion batch size.")
    parser.add_argument("--train-crop-size", type=int, default=384, help="Training crop size.")
    parser.add_argument("--max-steps", type=int, default=100000, help="Maximum optimizer steps.")
    parser.add_argument("--eval-interval", type=int, default=400, help="Evaluation interval in optimizer steps; use 0 to disable periodic evaluation.")
    parser.add_argument("--log-interval", type=int, default=50, help="Logging interval in optimizer steps.")
    parser.add_argument("--checkpoint-interval", type=int, default=400, help="Checkpoint interval in optimizer steps; use -1 to disable periodic checkpoints.")
    parser.add_argument("--ema-decay", default="0.999", help="EMA decay value. Use -1 to disable EMA.")
    parser.add_argument("--warmup-steps", type=int, default=2000, help="Learning-rate warmup steps.")
    parser.add_argument("--lr", default="0.001", help="Base learning rate.")
    parser.add_argument("--model-cycle", type=int, default=4, help="Value for --model.N_cycle.")
    parser.add_argument("--diffusion-steps", type=int, default=20, help="Value for --sample_diffusion.N_step during training evaluation.")
    parser.add_argument("--triangle-attention", choices=TRIANGLE_ATTENTION, default="cuequivariance", help="Triangle attention kernel.")
    parser.add_argument("--triangle-multiplicative", choices=TRIANGLE_MULTIPLICATIVE, default="cuequivariance", help="Triangle multiplicative kernel.")
    add_bool_argument(parser, "wandb", False, "Enable Weights & Biases by printing --use_wandb true.")
    parser.add_argument("--checkpoint", default=None, help="Fine-tune/load checkpoint path for --load_checkpoint_path.")
    parser.add_argument("--ema-checkpoint", default=None, help="EMA checkpoint path for --load_ema_checkpoint_path. Defaults to --checkpoint in finetune mode.")
    parser.add_argument("--subset-list", default=None, help="PDB subset text file for fine-tuning released data.")
    parser.add_argument("--subset-dataset", default=DATASET_2024, help="Dataset name whose base_info.pdb_list should be overridden.")
    add_bool_argument(parser, "load-strict", True, "Value for --load_strict.")
    add_bool_argument(parser, "load-params-only", True, "Value for --load_params_only.")
    add_bool_argument(parser, "skip-load-optimizer", False, "Value for --skip_load_optimizer.")
    add_bool_argument(parser, "skip-load-scheduler", False, "Value for --skip_load_scheduler.")
    add_bool_argument(parser, "skip-load-step", False, "Value for --skip_load_step.")
    add_bool_argument(parser, "load-step-for-scheduler", False, "Value for --load_step_for_scheduler.")
    parser.add_argument("--index", default=None, help="Override selected training dataset base_info.indices_fpath.")
    parser.add_argument("--bioassembly-dir", default=None, help="Override selected training dataset base_info.bioassembly_dict_dir.")
    parser.add_argument("--mmcif-dir", default=None, help="Override selected training dataset base_info.mmcif_dir.")
    parser.add_argument("--max-n-token", type=int, default=None, help="Override selected training dataset base_info.max_n_token.")
    parser.add_argument("--num-dl-workers", type=int, default=None, help="Override data.num_dl_workers.")
    parser.add_argument("--torchrun", action="store_true", help="Print a torchrun launcher instead of plain python.")
    parser.add_argument("--nproc-per-node", type=int, default=8, help="torchrun process count per node.")
    parser.add_argument("--nnodes", type=int, default=None, help="Optional torchrun --nnodes value.")
    parser.add_argument("--node-rank", type=int, default=None, help="Optional torchrun --node_rank value.")
    parser.add_argument("--master-addr", default=None, help="Optional torchrun --master_addr value.")
    parser.add_argument("--master-port", default=None, help="Optional torchrun --master_port value.")
    parser.add_argument("--python", default="python", help="Python executable name to print. Defaults to python.")
    parser.add_argument("--override", action="append", default=[], metavar="KEY=VALUE", help="Additional runner.train config override. May be repeated.")
    parser.add_argument("--env", action="append", default=[], metavar="KEY=VALUE", help="Additional environment assignment to print before the command. May be repeated.")
    parser.add_argument("--torch-fallback", action="store_true", help="Use portable torch kernels and fp32 unless explicitly overridden later.")
    parser.add_argument("--format", choices=("shell", "argv", "json"), default="shell", help="Output format.")
    parser.add_argument("--no-validate-paths", action="store_true", help="Do not warn about missing local paths.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when validation warnings are produced.")
    return parser


def bool_value(value: bool) -> str:
    return "true" if value else "false"


def shell_join(argv: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in argv)


def parse_key_value(raw: str, label: str) -> tuple[str, str]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError(f"{label} must be KEY=VALUE, got {raw!r}")
    key, value = raw.split("=", 1)
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError(f"{label} key is empty in {raw!r}")
    return key, value


def parse_override(raw: str) -> tuple[str, str]:
    key, value = parse_key_value(raw, "override")
    if key.startswith("--"):
        key = key[2:]
    return key, value


def parse_env(raw: str) -> tuple[str, str]:
    key, value = parse_key_value(raw, "environment assignment")
    if any(char.isspace() for char in key):
        raise argparse.ArgumentTypeError(f"environment key contains whitespace in {raw!r}")
    return key, value


def normalize_args(args: argparse.Namespace) -> None:
    if args.run_name is None:
        args.run_name = "protenix_finetune" if args.mode == "finetune" else "protenix_train"
    if args.mode == "finetune" and args.ema_checkpoint is None:
        args.ema_checkpoint = args.checkpoint
    if args.torch_fallback:
        if args.triangle_attention == "cuequivariance":
            args.triangle_attention = "torch"
        if args.triangle_multiplicative == "cuequivariance":
            args.triangle_multiplicative = "torch"
        if args.dtype == "bf16":
            args.dtype = "fp32"


def path_exists(value: str | None) -> bool:
    return bool(value) and Path(value).exists()


def validate_args(args: argparse.Namespace) -> list[str]:
    warnings: list[str] = []
    if not args.data_root:
        warnings.append("no data root was supplied and PROTENIX_ROOT_DIR is not set; printed command will omit the export.")
    if not args.no_validate_paths:
        for label, value in [
            ("data root", args.data_root),
            ("checkpoint", args.checkpoint),
            ("EMA checkpoint", args.ema_checkpoint),
            ("subset list", args.subset_list),
            ("index", args.index),
            ("bioassembly directory", args.bioassembly_dir),
            ("mmcif directory", args.mmcif_dir),
        ]:
            if value and not path_exists(value):
                warnings.append(f"{label} does not exist on this machine: {value}")
    if args.mode == "finetune" and not args.checkpoint:
        warnings.append("finetune mode usually needs --checkpoint and often --ema-checkpoint.")
    if args.mode == "finetune" and not args.subset_list:
        warnings.append("finetune mode usually restricts released data with --subset-list.")
    if args.triangle_attention == "deepspeed":
        warnings.append("--triangle_attention deepspeed requires CUTLASS_PATH and a compatible CUDA/deepspeed/pydantic runtime.")
    if args.wandb:
        warnings.append("W&B is enabled; confirm credentials, network policy, project naming, and non-interactive behavior.")
    if args.max_steps < 1:
        warnings.append("--max-steps should be at least 1.")
    if args.eval_interval < 0:
        warnings.append("--eval-interval should be non-negative; use 0 to disable periodic evaluation.")
    if args.log_interval < 1:
        warnings.append("--log-interval should be at least 1.")
    if args.diffusion_batch_size < 1:
        warnings.append("--diffusion-batch-size should be at least 1.")
    if args.train_crop_size < 1:
        warnings.append("--train-crop-size should be at least 1.")
    if args.torchrun and args.nproc_per_node < 1:
        warnings.append("--nproc-per-node should be at least 1.")
    if args.load_step_for_scheduler and args.skip_load_step:
        warnings.append("--load-step-for-scheduler true conflicts with --skip-load-step true.")
    for raw in args.override:
        try:
            parse_override(raw)
        except argparse.ArgumentTypeError as exc:
            warnings.append(str(exc))
    for raw in args.env:
        try:
            parse_env(raw)
        except argparse.ArgumentTypeError as exc:
            warnings.append(str(exc))
    return warnings


def base_training_overrides(args: argparse.Namespace) -> list[tuple[str, str]]:
    overrides = [
        ("run_name", args.run_name),
        ("model_name", args.model_name),
        ("seed", str(args.seed)),
        ("base_dir", args.base_dir),
        ("dtype", args.dtype),
        ("project", args.project),
        ("use_wandb", bool_value(args.wandb)),
        ("diffusion_batch_size", str(args.diffusion_batch_size)),
        ("eval_interval", str(args.eval_interval)),
        ("log_interval", str(args.log_interval)),
        ("checkpoint_interval", str(args.checkpoint_interval)),
        ("ema_decay", str(args.ema_decay)),
        ("train_crop_size", str(args.train_crop_size)),
        ("max_steps", str(args.max_steps)),
        ("warmup_steps", str(args.warmup_steps)),
        ("lr", str(args.lr)),
        ("model.N_cycle", str(args.model_cycle)),
        ("sample_diffusion.N_step", str(args.diffusion_steps)),
        ("triangle_attention", args.triangle_attention),
        ("triangle_multiplicative", args.triangle_multiplicative),
        ("data.train_sets", args.train_sets),
        ("data.test_sets", args.test_sets),
    ]
    if args.num_dl_workers is not None:
        overrides.append(("data.num_dl_workers", str(args.num_dl_workers)))
    return overrides


def dataset_overrides(args: argparse.Namespace) -> list[tuple[str, str]]:
    dataset = args.subset_dataset
    overrides: list[tuple[str, str]] = []
    if args.subset_list:
        overrides.append((f"data.{dataset}.base_info.pdb_list", args.subset_list))
    if args.index:
        overrides.append((f"data.{dataset}.base_info.indices_fpath", args.index))
    if args.bioassembly_dir:
        overrides.append((f"data.{dataset}.base_info.bioassembly_dict_dir", args.bioassembly_dir))
    if args.mmcif_dir:
        overrides.append((f"data.{dataset}.base_info.mmcif_dir", args.mmcif_dir))
    if args.max_n_token is not None:
        overrides.append((f"data.{dataset}.base_info.max_n_token", str(args.max_n_token)))
    return overrides


def finetune_overrides(args: argparse.Namespace) -> list[tuple[str, str]]:
    overrides: list[tuple[str, str]] = []
    if args.checkpoint:
        overrides.append(("load_checkpoint_path", args.checkpoint))
    if args.ema_checkpoint:
        overrides.append(("load_ema_checkpoint_path", args.ema_checkpoint))
    overrides.extend(
        [
            ("load_strict", bool_value(args.load_strict)),
            ("load_params_only", bool_value(args.load_params_only)),
            ("skip_load_optimizer", bool_value(args.skip_load_optimizer)),
            ("skip_load_scheduler", bool_value(args.skip_load_scheduler)),
            ("skip_load_step", bool_value(args.skip_load_step)),
            ("load_step_for_scheduler", bool_value(args.load_step_for_scheduler)),
        ]
    )
    return overrides


def build_runner_argv(args: argparse.Namespace) -> list[str]:
    command = ["-m", "runner.train"]
    all_overrides = base_training_overrides(args) + dataset_overrides(args)
    if args.mode == "finetune":
        all_overrides.extend(finetune_overrides(args))
    for raw in args.override:
        key, value = parse_override(raw)
        all_overrides.append((key, value))
    for key, value in all_overrides:
        command.extend([f"--{key}", value])
    return command


def build_command(args: argparse.Namespace) -> tuple[list[tuple[str, str]], list[str]]:
    env: list[tuple[str, str]] = []
    if args.data_root:
        env.append(("PROTENIX_ROOT_DIR", args.data_root))
    for raw in args.env:
        env.append(parse_env(raw))

    runner_argv = build_runner_argv(args)
    if args.torchrun:
        command = ["torchrun", "--nproc_per_node", str(args.nproc_per_node)]
        if args.nnodes is not None:
            command.extend(["--nnodes", str(args.nnodes)])
        if args.node_rank is not None:
            command.extend(["--node_rank", str(args.node_rank)])
        if args.master_addr:
            command.extend(["--master_addr", args.master_addr])
        if args.master_port:
            command.extend(["--master_port", args.master_port])
        command.extend(runner_argv)
    else:
        command = [args.python] + runner_argv
    return env, command


def render_shell(env: list[tuple[str, str]], command: list[str]) -> str:
    lines = [f"export {key}={shlex.quote(value)}" for key, value in env]
    lines.append(shell_join(command))
    return "\n".join(lines)


def render_argv(env: list[tuple[str, str]], command: list[str]) -> str:
    env_prefix = [f"{key}={value}" for key, value in env]
    return "\n".join(env_prefix + command)


def render_json(env: list[tuple[str, str]], command: list[str], warnings: list[str]) -> str:
    payload: dict[str, Any] = {
        "env": dict(env),
        "argv": command,
        "warnings": warnings,
        "side_effects": "none; command is printed only",
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def main() -> int:
    args = build_parser().parse_args()
    normalize_args(args)
    warnings = validate_args(args)
    try:
        env, command = build_command(args)
    except argparse.ArgumentTypeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(render_json(env, command, warnings))
    elif args.format == "argv":
        print(render_argv(env, command))
    else:
        print("# Protenix training command plan; not executed by this helper.")
        if warnings:
            for warning in warnings:
                print(f"# WARN: {warning}")
        print(render_shell(env, command))

    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
