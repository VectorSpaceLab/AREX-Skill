#!/usr/bin/env python3
"""Build safe OpenRLHF SFT/RM/DPO command skeletons.

This helper formats commands for review. It does not import OpenRLHF,
inspect GPUs, download models/datasets, or execute training.
"""

from __future__ import annotations

import argparse
import shlex
from typing import Iterable, List, Optional


DEFAULTS = {
    "sft": {
        "module": "openrlhf.cli.train_sft",
        "output_dir": "./checkpoint/sft",
        "max_len": "2048",
        "batch_size": "128",
        "micro_batch_size": "2",
        "lr": "5e-6",
        "zero_stage": "2",
        "epochs": "1",
        "input_key": "input",
        "output_key": "output",
        "wandb_project": "openrlhf_train_sft",
    },
    "rm": {
        "module": "openrlhf.cli.train_rm",
        "output_dir": "./checkpoint/rm",
        "max_len": "512",
        "batch_size": "128",
        "micro_batch_size": "1",
        "lr": "9e-6",
        "zero_stage": "3",
        "epochs": "1",
        "chosen_key": "chosen",
        "rejected_key": "rejected",
        "wandb_project": "openrlhf_train_rm",
    },
    "dpo": {
        "module": "openrlhf.cli.train_dpo",
        "output_dir": "./checkpoint/dpo",
        "max_len": "512",
        "batch_size": "128",
        "micro_batch_size": "1",
        "lr": "5e-7",
        "zero_stage": "3",
        "epochs": "1",
        "chosen_key": "chosen",
        "rejected_key": "rejected",
        "beta": "0.1",
        "wandb_project": "openrlhf_train_dpo",
    },
}


def add_shared(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", required=True, help="Model path or hub ID for --model.model_name_or_path.")
    parser.add_argument("--dataset", required=True, help="Dataset path or hub ID for --data.dataset.")
    parser.add_argument("--output-dir", help="Final model output directory.")
    parser.add_argument("--max-len", help="Value for --data.max_len.")
    parser.add_argument("--batch-size", help="Global --train.batch_size.")
    parser.add_argument("--micro-batch-size", help="Per-GPU --train.micro_batch_size.")
    parser.add_argument("--epochs", help="Value for --train.max_epochs.")
    parser.add_argument("--lr", help="Value for --adam.lr.")
    parser.add_argument("--zero-stage", choices=["0", "1", "2", "3"], help="Value for --ds.zero_stage.")
    parser.add_argument("--param-dtype", default="bf16", help="Value for --ds.param_dtype (default: bf16).")
    parser.add_argument("--attn-implementation", help="Value for --ds.attn_implementation, e.g. flash_attention_2.")
    parser.add_argument("--packing", action="store_true", help="Add --ds.packing_samples.")
    parser.add_argument("--gradient-checkpointing", action="store_true", help="Add --model.gradient_checkpointing_enable.")
    parser.add_argument("--save-steps", default="-1", help="Value for --ckpt.save_steps (default: -1 disables periodic saves).")
    parser.add_argument("--eval-steps", default="-1", help="Value for --eval.steps (default: -1 means trainer default).")
    parser.add_argument("--logging-steps", default="1", help="Value for --logger.logging_steps.")
    parser.add_argument("--load-enable", action="store_true", help="Add --ckpt.load_enable.")
    parser.add_argument("--ckpt-path", help="Value for --ckpt.path, used for periodic save/resume.")
    parser.add_argument("--save-hf", action="store_true", help="Add --ckpt.save_hf for periodic HF-format checkpoints.")
    parser.add_argument("--disable-ds-ckpt", action="store_true", help="Add --ckpt.disable_ds.")
    parser.add_argument("--wandb-key-placeholder", action="store_true", help="Add a placeholder --logger.wandb.key, not a real secret.")
    parser.add_argument("--tensorboard-dir", help="Value for --logger.tensorboard_dir.")
    parser.add_argument("--lora-rank", help="Value for --ds.lora.rank; nonzero enables LoRA construction.")
    parser.add_argument("--lora-alpha", help="Value for --ds.lora.alpha.")
    parser.add_argument("--lora-dropout", help="Value for --ds.lora.dropout.")
    parser.add_argument("--lora-target-modules", nargs="+", help="Values for --ds.lora.target_modules.")
    parser.add_argument("--load-in-4bit", action="store_true", help="Add --ds.load_in_4bit.")
    parser.add_argument("--use-liger-kernel", action="store_true", help="Add --ds.use_liger_kernel.")
    parser.add_argument("--ring-attn-size", help="Value for --ds.ring_attn_size; requires packing in OpenRLHF.")
    parser.add_argument("--extra", action="append", default=[], help="Append an extra raw flag/value fragment after generated flags.")


def with_default(args: argparse.Namespace, kind: str, name: str) -> str:
    value = getattr(args, name)
    if value is not None:
        return str(value)
    return DEFAULTS[kind][name]


def append_pair(parts: List[str], flag: str, value: Optional[object]) -> None:
    if value is not None and str(value) != "":
        parts.extend([flag, str(value)])


def append_bool(parts: List[str], enabled: bool, flag: str) -> None:
    if enabled:
        parts.append(flag)


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def build_command(kind: str, args: argparse.Namespace) -> List[str]:
    defaults = DEFAULTS[kind]
    parts = ["deepspeed", "--module", defaults["module"]]

    append_pair(parts, "--model.model_name_or_path", args.model)
    if kind == "dpo" and args.ref_model:
        append_pair(parts, "--ref.model_name_or_path", args.ref_model)
    append_pair(parts, "--data.dataset", args.dataset)

    if kind == "sft":
        append_pair(parts, "--data.input_key", args.input_key or defaults["input_key"])
        append_pair(parts, "--data.output_key", args.output_key or defaults["output_key"])
        append_bool(parts, args.multiturn, "--data.multiturn")
        append_bool(parts, args.pretrain_mode, "--model.pretrain_mode_enable")
    else:
        append_pair(parts, "--data.chosen_key", args.chosen_key or defaults["chosen_key"])
        append_pair(parts, "--data.rejected_key", args.rejected_key or defaults["rejected_key"])
        append_pair(parts, "--data.prompt_key", args.prompt_key)
        if kind == "rm":
            append_pair(parts, "--model.loss_type", args.loss_type)
            append_bool(parts, args.margin_loss, "--model.margin_loss_enable")
            append_bool(parts, args.compute_fp32_loss, "--model.compute_fp32_loss_enable")
            append_pair(parts, "--ds.value_head_prefix", args.value_head_prefix)
        if kind == "dpo":
            append_pair(parts, "--model.beta", args.beta or defaults["beta"])
            append_bool(parts, args.ipo, "--model.ipo_enable")
            append_pair(parts, "--model.label_smoothing", args.label_smoothing)
            append_pair(parts, "--model.nll_loss_coef", args.nll_loss_coef)
            append_bool(parts, args.ref_offload, "--ref.offload")

    append_bool(parts, args.apply_chat_template, "--data.apply_chat_template")
    append_pair(parts, "--data.input_template", args.input_template)
    append_pair(parts, "--data.max_len", with_default(args, kind, "max_len"))
    append_pair(parts, "--data.max_samples", args.max_samples)
    append_pair(parts, "--data.dataset_split", args.dataset_split)
    append_pair(parts, "--eval.dataset", args.eval_dataset)
    append_pair(parts, "--eval.split", args.eval_split)

    append_pair(parts, "--train.batch_size", with_default(args, kind, "batch_size"))
    append_pair(parts, "--train.micro_batch_size", with_default(args, kind, "micro_batch_size"))
    append_pair(parts, "--train.max_epochs", with_default(args, kind, "epochs"))
    append_pair(parts, "--adam.lr", with_default(args, kind, "lr"))
    append_pair(parts, "--ds.zero_stage", with_default(args, kind, "zero_stage"))
    append_pair(parts, "--ds.param_dtype", args.param_dtype)
    append_pair(parts, "--ds.attn_implementation", args.attn_implementation)
    append_bool(parts, args.packing, "--ds.packing_samples")
    append_bool(parts, args.gradient_checkpointing, "--model.gradient_checkpointing_enable")

    append_pair(parts, "--ds.lora.rank", args.lora_rank)
    append_pair(parts, "--ds.lora.alpha", args.lora_alpha)
    append_pair(parts, "--ds.lora.dropout", args.lora_dropout)
    if args.lora_target_modules:
        parts.append("--ds.lora.target_modules")
        parts.extend(args.lora_target_modules)
    append_bool(parts, args.load_in_4bit, "--ds.load_in_4bit")
    append_bool(parts, args.use_liger_kernel, "--ds.use_liger_kernel")
    append_pair(parts, "--ds.ring_attn_size", args.ring_attn_size)

    append_pair(parts, "--ckpt.output_dir", args.output_dir or defaults["output_dir"])
    append_pair(parts, "--ckpt.save_steps", args.save_steps)
    append_pair(parts, "--eval.steps", args.eval_steps)
    append_pair(parts, "--logger.logging_steps", args.logging_steps)
    append_pair(parts, "--ckpt.path", args.ckpt_path)
    append_bool(parts, args.load_enable, "--ckpt.load_enable")
    append_bool(parts, args.save_hf, "--ckpt.save_hf")
    append_bool(parts, args.disable_ds_ckpt, "--ckpt.disable_ds")
    append_pair(parts, "--logger.tensorboard_dir", args.tensorboard_dir)
    if args.wandb_key_placeholder:
        append_pair(parts, "--logger.wandb.key", "WANDB_TOKEN_PLACEHOLDER")

    for fragment in args.extra:
        parts.extend(shlex.split(fragment))

    return parts


def add_sft(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("sft", help="Build an SFT command skeleton.")
    add_shared(parser)
    parser.add_argument("--input-key", help="Value for --data.input_key.")
    parser.add_argument("--output-key", help="Value for --data.output_key.")
    parser.add_argument("--input-template", help="Value for --data.input_template.")
    parser.add_argument("--apply-chat-template", action="store_true", help="Add --data.apply_chat_template.")
    parser.add_argument("--multiturn", action="store_true", help="Add --data.multiturn; requires chat template at runtime.")
    parser.add_argument("--pretrain-mode", action="store_true", help="Add --model.pretrain_mode_enable.")
    parser.add_argument("--max-samples", help="Value for --data.max_samples.")
    parser.add_argument("--dataset-split", help="Value for --data.dataset_split.")
    parser.add_argument("--eval-dataset", help="Value for --eval.dataset.")
    parser.add_argument("--eval-split", help="Value for --eval.split.")
    parser.set_defaults(kind="sft")


def add_rm(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("rm", help="Build a reward-model command skeleton.")
    add_shared(parser)
    parser.add_argument("--chosen-key", help="Value for --data.chosen_key.")
    parser.add_argument("--rejected-key", help="Value for --data.rejected_key.")
    parser.add_argument("--prompt-key", help="Value for --data.prompt_key.")
    parser.add_argument("--input-template", help="Value for --data.input_template.")
    parser.add_argument("--apply-chat-template", action="store_true", help="Add --data.apply_chat_template.")
    parser.add_argument("--max-samples", help="Value for --data.max_samples.")
    parser.add_argument("--dataset-split", help="Value for --data.dataset_split.")
    parser.add_argument("--eval-dataset", help="Value for --eval.dataset.")
    parser.add_argument("--eval-split", help="Value for --eval.split.")
    parser.add_argument("--loss-type", choices=["sigmoid", "logexp"], help="Value for --model.loss_type.")
    parser.add_argument("--margin-loss", action="store_true", help="Add --model.margin_loss_enable.")
    parser.add_argument("--compute-fp32-loss", action="store_true", help="Add --model.compute_fp32_loss_enable.")
    parser.add_argument("--value-head-prefix", help="Value for --ds.value_head_prefix.")
    parser.set_defaults(kind="rm")


def add_dpo(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("dpo", help="Build a DPO/IPO/cDPO command skeleton.")
    add_shared(parser)
    parser.add_argument("--ref-model", help="Value for --ref.model_name_or_path.")
    parser.add_argument("--chosen-key", help="Value for --data.chosen_key.")
    parser.add_argument("--rejected-key", help="Value for --data.rejected_key.")
    parser.add_argument("--prompt-key", help="Value for --data.prompt_key.")
    parser.add_argument("--input-template", help="Value for --data.input_template.")
    parser.add_argument("--apply-chat-template", action="store_true", help="Add --data.apply_chat_template.")
    parser.add_argument("--max-samples", help="Value for --data.max_samples.")
    parser.add_argument("--dataset-split", help="Value for --data.dataset_split.")
    parser.add_argument("--eval-dataset", help="Value for --eval.dataset.")
    parser.add_argument("--eval-split", help="Value for --eval.split.")
    parser.add_argument("--beta", help="Value for --model.beta.")
    parser.add_argument("--ipo", action="store_true", help="Add --model.ipo_enable.")
    parser.add_argument("--label-smoothing", help="Value for --model.label_smoothing for cDPO.")
    parser.add_argument("--nll-loss-coef", help="Value for --model.nll_loss_coef.")
    parser.add_argument("--ref-offload", action="store_true", help="Add --ref.offload.")
    parser.set_defaults(kind="dpo")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print safe OpenRLHF training command skeletons for SFT, RM, or DPO.",
        epilog="The generated command is for review only; running it may require GPUs, downloads, and optional dependencies.",
    )
    subparsers = parser.add_subparsers(dest="kind", required=True)
    add_sft(subparsers)
    add_rm(subparsers)
    add_dpo(subparsers)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if getattr(args, "ring_attn_size", None) and not args.packing:
        raise SystemExit("--ring-attn-size requires --packing for OpenRLHF runtime compatibility")
    if getattr(args, "multiturn", False) and not getattr(args, "apply_chat_template", False):
        raise SystemExit("--multiturn requires --apply-chat-template for OpenRLHF runtime compatibility")

    command = build_command(args.kind, args)
    print(shell_join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
