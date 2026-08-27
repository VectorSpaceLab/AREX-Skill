#!/usr/bin/env python3
"""Build a safe ms-swift training command skeleton without launching training."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from typing import Iterable, List, Optional


DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_DATASET = "./train.jsonl"


def str_bool(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return "true"
    if text in {"0", "false", "no", "n", "off"}:
        return "false"
    raise argparse.ArgumentTypeError(f"expected boolean, got {value!r}")


def add_flag(command: List[str], name: str, value: Optional[object]) -> None:
    if value is None:
        return
    command.append(f"--{name}")
    if isinstance(value, (dict, list)):
        command.append(json.dumps(value, ensure_ascii=False))
    else:
        command.append(str(value))


def add_repeated(command: List[str], name: str, values: Optional[Iterable[str]]) -> None:
    if not values:
        return
    command.append(f"--{name}")
    command.extend(str(item) for item in values)


def build_command(args: argparse.Namespace) -> List[str]:
    command: List[str] = ["swift", args.route]
    add_flag(command, "model", args.model)
    add_repeated(command, "dataset", args.dataset)
    add_repeated(command, "cached_dataset", args.cached_dataset)
    add_flag(command, "train_type", args.train_type)
    add_flag(command, "output_dir", args.output_dir)
    add_flag(command, "max_length", args.max_length)
    add_flag(command, "per_device_train_batch_size", args.per_device_train_batch_size)
    add_flag(command, "gradient_accumulation_steps", args.gradient_accumulation_steps)
    add_flag(command, "learning_rate", args.learning_rate)
    add_flag(command, "num_train_epochs", args.num_train_epochs)
    add_flag(command, "max_steps", args.max_steps)
    add_flag(command, "split_dataset_ratio", args.split_dataset_ratio)
    add_repeated(command, "val_dataset", args.val_dataset)
    add_flag(command, "save_steps", args.save_steps)
    add_flag(command, "save_total_limit", args.save_total_limit)
    add_flag(command, "logging_steps", args.logging_steps)
    add_flag(command, "torch_dtype", args.torch_dtype)
    add_flag(command, "use_hf", args.use_hf)
    add_flag(command, "check_model", args.check_model)
    add_flag(command, "template", args.template)

    if args.route == "pt":
        add_flag(command, "use_chat_template", "false")
        add_flag(command, "loss_scale", "all")
    elif args.use_chat_template is not None:
        add_flag(command, "use_chat_template", args.use_chat_template)
    if args.loss_scale is not None and args.route != "pt":
        add_flag(command, "loss_scale", args.loss_scale)

    if args.train_type in {"lora", "qlora"}:
        add_flag(command, "lora_rank", args.lora_rank)
        add_flag(command, "lora_alpha", args.lora_alpha)
        add_repeated(command, "target_modules", args.target_modules)
        add_repeated(command, "modules_to_save", args.modules_to_save)
    if args.train_type == "qlora":
        add_flag(command, "quant_method", args.quant_method)

    add_flag(command, "packing", args.packing)
    add_flag(command, "padding_free", args.padding_free)
    add_flag(command, "attn_impl", args.attn_impl)
    add_flag(command, "lazy_tokenize", args.lazy_tokenize)
    add_flag(command, "streaming", args.streaming)
    add_flag(command, "deepspeed", args.deepspeed)
    add_flag(command, "fsdp", args.fsdp)
    if args.ddp_use_reentrant_false:
        add_flag(command, "gradient_checkpointing_kwargs", {"use_reentrant": False})
    add_flag(command, "resume_from_checkpoint", args.resume_from_checkpoint)
    add_flag(command, "resume_only_model", args.resume_only_model)
    add_repeated(command, "adapters", args.adapters)
    add_flag(command, "create_checkpoint_symlink", args.create_checkpoint_symlink)
    add_flag(command, "freeze_llm", args.freeze_llm)
    add_flag(command, "freeze_vit", args.freeze_vit)
    add_flag(command, "freeze_aligner", args.freeze_aligner)
    return command


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a shell-quoted ms-swift training command skeleton. It does not run training.")
    parser.add_argument("--route", choices=["sft", "pt"], default="sft")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--dataset", nargs="+", default=[DEFAULT_DATASET])
    parser.add_argument("--cached-dataset", dest="cached_dataset", nargs="+")
    parser.add_argument("--train-type", choices=["lora", "qlora", "full"], default="lora")
    parser.add_argument("--output-dir", default="output/ms_swift_training")
    parser.add_argument("--max-length", type=int, default=2048)
    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=16)
    parser.add_argument("--learning-rate")
    parser.add_argument("--num-train-epochs")
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--split-dataset-ratio", type=float)
    parser.add_argument("--val-dataset", nargs="+")
    parser.add_argument("--save-steps", type=int)
    parser.add_argument("--save-total-limit", type=int)
    parser.add_argument("--logging-steps", type=int)
    parser.add_argument("--torch-dtype", choices=["float16", "bfloat16", "float32"])
    parser.add_argument("--use-hf", type=str_bool)
    parser.add_argument("--check-model", type=str_bool)
    parser.add_argument("--template")
    parser.add_argument("--use-chat-template", type=str_bool)
    parser.add_argument("--loss-scale")
    parser.add_argument("--lora-rank", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--target-modules", nargs="+")
    parser.add_argument("--modules-to-save", nargs="+")
    parser.add_argument("--quant-method")
    parser.add_argument("--packing", type=str_bool)
    parser.add_argument("--padding-free", type=str_bool)
    parser.add_argument("--attn-impl")
    parser.add_argument("--lazy-tokenize", type=str_bool)
    parser.add_argument("--streaming", type=str_bool)
    parser.add_argument("--deepspeed")
    parser.add_argument("--fsdp")
    parser.add_argument("--ddp-use-reentrant-false", action="store_true")
    parser.add_argument("--resume-from-checkpoint")
    parser.add_argument("--resume-only-model", type=str_bool)
    parser.add_argument("--adapters", nargs="+")
    parser.add_argument("--create-checkpoint-symlink", type=str_bool)
    parser.add_argument("--freeze-llm", type=str_bool)
    parser.add_argument("--freeze-vit", type=str_bool)
    parser.add_argument("--freeze-aligner", type=str_bool)
    parser.add_argument("--with-env", action="append", default=[], metavar="KEY=VALUE",
                        help="Prefix the printed command with environment assignments. Can be repeated.")
    parser.add_argument("--multiline", action="store_true", help="Print as a backslash-continued shell command.")
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> List[str]:
    warnings: List[str] = []
    if not args.dataset and not args.cached_dataset:
        warnings.append("No dataset or cached dataset was provided; ms-swift training requires one of them.")
    if args.route == "pt" and args.use_chat_template == "true":
        warnings.append("swift pt normally uses --use_chat_template false; the printed command keeps the pt default.")
    if (args.packing == "true" or args.padding_free == "true") and not args.attn_impl:
        warnings.append("packing/padding_free require a flash attention implementation such as --attn_impl flash_attn.")
    if args.deepspeed and args.fsdp:
        warnings.append("DeepSpeed and FSDP should not be combined.")
    if args.train_type == "qlora":
        warnings.append("QLoRA is memory-efficient but is not the right choice when merged vLLM/SGLang/LMDeploy acceleration is required after training.")
    return warnings


def format_command(command: List[str], env_items: List[str], multiline: bool) -> str:
    env_prefix = []
    for item in env_items:
        if "=" not in item or item.startswith("="):
            raise SystemExit(f"invalid --with-env value {item!r}; expected KEY=VALUE")
        key, value = item.split("=", 1)
        env_prefix.append(f"{key}={shlex.quote(value)}")
    quoted = [shlex.quote(part) for part in command]
    pieces = env_prefix + quoted
    if not multiline:
        return " ".join(pieces)
    return " \\\n  ".join(pieces)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    command = build_command(args)
    print(format_command(command, args.with_env, args.multiline))
    warnings = validate_args(args)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    return 0 if not any("requires one" in warning for warning in warnings) else 2


if __name__ == "__main__":
    raise SystemExit(main())
