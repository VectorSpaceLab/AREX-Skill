#!/usr/bin/env python3
"""Build a safe OpenFold training command without launching training."""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable, List, Optional


def str_to_bool(value: str) -> str:
    lowered = value.lower()
    if lowered in {"true", "t", "yes", "y", "1"}:
        return "true"
    if lowered in {"false", "f", "no", "n", "0"}:
        return "false"
    raise argparse.ArgumentTypeError(f"expected a boolean string, got {value!r}")


def add_optional(command: List[str], flag: str, value: Optional[object]) -> None:
    if value is not None and value != "":
        command.extend([flag, str(value)])


def add_bool_flag(command: List[str], flag: str, enabled: bool) -> None:
    if enabled:
        command.append(flag)


def split_extra_args(values: Optional[Iterable[str]]) -> List[str]:
    result: List[str] = []
    for value in values or []:
        result.extend(shlex.split(value))
    return result


def build_command(args: argparse.Namespace) -> List[str]:
    if (args.gpus is not None and args.gpus > 1 or args.num_nodes is not None and args.num_nodes > 1) and args.seed is None:
        raise ValueError("OpenFold distributed training requires --seed when --gpus > 1 or --num_nodes > 1")

    if args.deepspeed_config_path and str(args.precision) == "16":
        raise ValueError("OpenFold rejects DeepSpeed with Lightning precision 16; use BF16 or remove DeepSpeed")

    if args.resume_from_ckpt and args.resume_from_jax_params:
        raise ValueError("Choose either --resume_from_ckpt or --resume_from_jax_params, not both")

    if args.alignment_index_path and not args.train_alignment_dir:
        raise ValueError("--alignment_index_path requires the training alignment DB directory positional")

    command = [
        args.python_executable,
        args.train_script,
        args.train_data_dir,
        args.train_alignment_dir,
        args.template_mmcif_dir,
        args.output_dir,
        args.max_template_date,
    ]

    add_optional(command, "--config_preset", args.config_preset)
    add_optional(command, "--seed", args.seed)
    add_optional(command, "--gpus", args.gpus)
    add_optional(command, "--num_nodes", args.num_nodes)
    add_optional(command, "--precision", args.precision)
    add_optional(command, "--max_epochs", args.max_epochs)
    add_optional(command, "--train_epoch_len", args.train_epoch_len)
    add_optional(command, "--accumulate_grad_batches", args.accumulate_grad_batches)
    add_optional(command, "--log_every_n_steps", args.log_every_n_steps)
    add_optional(command, "--num_sanity_val_steps", args.num_sanity_val_steps)
    add_optional(command, "--reload_dataloaders_every_n_epochs", args.reload_dataloaders_every_n_epochs)
    add_optional(command, "--train_chain_data_cache_path", args.train_chain_data_cache_path)
    add_optional(command, "--train_mmcif_data_cache_path", args.train_mmcif_data_cache_path)
    add_optional(command, "--template_release_dates_cache_path", args.template_release_dates_cache_path)
    add_optional(command, "--alignment_index_path", args.alignment_index_path)
    add_optional(command, "--obsolete_pdbs_file_path", args.obsolete_pdbs_file_path)
    add_optional(command, "--train_filter_path", args.train_filter_path)
    add_optional(command, "--experiment_config_json", args.experiment_config_json)
    add_optional(command, "--deepspeed_config_path", args.deepspeed_config_path)
    add_optional(command, "--val_data_dir", args.val_data_dir)
    add_optional(command, "--val_alignment_dir", args.val_alignment_dir)
    add_optional(command, "--val_mmcif_data_cache_path", args.val_mmcif_data_cache_path)
    add_optional(command, "--distillation_data_dir", args.distillation_data_dir)
    add_optional(command, "--distillation_alignment_dir", args.distillation_alignment_dir)
    add_optional(command, "--distillation_chain_data_cache_path", args.distillation_chain_data_cache_path)
    add_optional(command, "--distillation_alignment_index_path", args.distillation_alignment_index_path)
    add_optional(command, "--distillation_filter_path", args.distillation_filter_path)
    add_optional(command, "--resume_from_ckpt", args.resume_from_ckpt)
    add_optional(command, "--resume_model_weights_only", args.resume_model_weights_only)
    add_optional(command, "--resume_from_jax_params", args.resume_from_jax_params)
    add_optional(command, "--early_stopping", args.early_stopping)
    add_optional(command, "--min_delta", args.min_delta)
    add_optional(command, "--patience", args.patience)
    add_optional(command, "--log_performance", args.log_performance)
    add_optional(command, "--experiment_name", args.experiment_name)
    add_optional(command, "--wandb_id", args.wandb_id)
    add_optional(command, "--wandb_project", args.wandb_project)
    add_optional(command, "--wandb_entity", args.wandb_entity)
    add_optional(command, "--script_modules", args.script_modules)
    add_optional(command, "--use_single_seq_mode", args.use_single_seq_mode)
    add_optional(command, "--kalign_binary_path", args.kalign_binary_path)

    add_bool_flag(command, "--checkpoint_every_epoch", args.checkpoint_every_epoch)
    add_bool_flag(command, "--log_lr", args.log_lr)
    add_bool_flag(command, "--wandb", args.wandb)
    add_bool_flag(command, "--mpi_plugin", args.mpi_plugin)

    command.extend(split_extra_args(args.extra_arg))
    return command


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a shell-quoted OpenFold train_openfold.py command without running it."
    )
    parser.add_argument("--python-executable", default="python", help="Python executable to place at the front of the command")
    parser.add_argument("--train-script", default="train_openfold.py", help="Path to train_openfold.py in the user's OpenFold checkout")
    parser.add_argument("--train-data-dir", required=True, help="Training mmCIF directory")
    parser.add_argument("--train-alignment-dir", required=True, help="Training alignment directory or alignment DB shard directory")
    parser.add_argument("--template-mmcif-dir", required=True, help="Template mmCIF directory")
    parser.add_argument("--output-dir", required=True, help="Training output directory")
    parser.add_argument("--max-template-date", required=True, help="Template cutoff date positional, e.g. 2021-10-10")

    parser.add_argument("--config-preset", default="initial_training")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--gpus", type=int, default=1)
    parser.add_argument("--num-nodes", type=int, default=1)
    parser.add_argument("--precision", default="bf16")
    parser.add_argument("--max-epochs", type=int)
    parser.add_argument("--train-epoch-len", type=int)
    parser.add_argument("--accumulate-grad-batches", type=int)
    parser.add_argument("--log-every-n-steps", type=int)
    parser.add_argument("--num-sanity-val-steps", type=int)
    parser.add_argument("--reload-dataloaders-every-n-epochs", type=int)

    parser.add_argument("--train-chain-data-cache-path")
    parser.add_argument("--train-mmcif-data-cache-path")
    parser.add_argument("--template-release-dates-cache-path")
    parser.add_argument("--alignment-index-path")
    parser.add_argument("--obsolete-pdbs-file-path")
    parser.add_argument("--train-filter-path")
    parser.add_argument("--experiment-config-json")
    parser.add_argument("--deepspeed-config-path")

    parser.add_argument("--val-data-dir")
    parser.add_argument("--val-alignment-dir")
    parser.add_argument("--val-mmcif-data-cache-path")
    parser.add_argument("--distillation-data-dir")
    parser.add_argument("--distillation-alignment-dir")
    parser.add_argument("--distillation-chain-data-cache-path")
    parser.add_argument("--distillation-alignment-index-path")
    parser.add_argument("--distillation-filter-path")

    parser.add_argument("--resume-from-ckpt")
    parser.add_argument("--resume-model-weights-only", type=str_to_bool)
    parser.add_argument("--resume-from-jax-params")

    parser.add_argument("--checkpoint-every-epoch", action="store_true")
    parser.add_argument("--early-stopping", type=str_to_bool)
    parser.add_argument("--min-delta", type=float)
    parser.add_argument("--patience", type=int)
    parser.add_argument("--log-performance", type=str_to_bool)
    parser.add_argument("--log-lr", action="store_true")

    parser.add_argument("--wandb", action="store_true")
    parser.add_argument("--experiment-name")
    parser.add_argument("--wandb-id")
    parser.add_argument("--wandb-project")
    parser.add_argument("--wandb-entity")

    parser.add_argument("--script-modules", type=str_to_bool)
    parser.add_argument("--use-single-seq-mode", type=str_to_bool)
    parser.add_argument("--kalign-binary-path")
    parser.add_argument("--mpi-plugin", action="store_true")
    parser.add_argument("--extra-arg", action="append", help="Additional raw train_openfold.py arguments, shell-split; may be repeated")
    return parser


def main() -> int:
    args = parser().parse_args()
    try:
        command = build_command(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(shlex.join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
