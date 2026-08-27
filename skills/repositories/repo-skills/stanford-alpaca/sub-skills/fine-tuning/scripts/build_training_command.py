#!/usr/bin/env python
"""Build safe Stanford Alpaca fine-tuning command text.

This helper only prints a shell command. It never imports torch, reads the
training data, launches torchrun, writes checkpoints, or starts training.
"""

import argparse
import shlex
from typing import Iterable, List, Optional


FSDP_LAYER_BY_FAMILY = {
    "llama": "LlamaDecoderLayer",
    "opt": "OPTDecoderLayer",
}


def _str_bool(value: bool) -> str:
    return "True" if value else "False"


def infer_model_family(model_name_or_path: str) -> Optional[str]:
    lowered = model_name_or_path.lower()
    if "llama" in lowered:
        return "llama"
    if "opt" in lowered:
        return "opt"
    return None


def quote_parts(parts: Iterable[str]) -> List[str]:
    return [shlex.quote(str(part)) for part in parts]


def add_flag(parts: List[str], flag: str, value) -> None:
    parts.extend([flag, str(value)])


def build_parts(args: argparse.Namespace) -> List[str]:
    parts: List[str] = [
        "torchrun",
        "--nproc_per_node",
        str(args.nproc_per_node),
        "--master_port",
        str(args.master_port),
        args.trainer_script,
    ]

    add_flag(parts, "--model_name_or_path", args.model_name_or_path)
    add_flag(parts, "--data_path", args.data_path)
    add_flag(parts, "--bf16", _str_bool(args.bf16))
    add_flag(parts, "--output_dir", args.output_dir)
    add_flag(parts, "--num_train_epochs", args.num_train_epochs)
    add_flag(parts, "--per_device_train_batch_size", args.per_device_train_batch_size)
    add_flag(parts, "--per_device_eval_batch_size", args.per_device_eval_batch_size)
    add_flag(parts, "--gradient_accumulation_steps", args.gradient_accumulation_steps)
    add_flag(parts, "--evaluation_strategy", args.evaluation_strategy)
    add_flag(parts, "--save_strategy", args.save_strategy)
    add_flag(parts, "--save_steps", args.save_steps)
    add_flag(parts, "--save_total_limit", args.save_total_limit)
    add_flag(parts, "--learning_rate", args.learning_rate)
    add_flag(parts, "--weight_decay", args.weight_decay)
    add_flag(parts, "--warmup_ratio", args.warmup_ratio)

    if args.recipe.startswith("fsdp"):
        add_flag(parts, "--lr_scheduler_type", args.lr_scheduler_type)
        add_flag(parts, "--logging_steps", args.logging_steps)
        fsdp_mode = "full_shard auto_wrap offload" if args.recipe == "fsdp-offload" else "full_shard auto_wrap"
        add_flag(parts, "--fsdp", fsdp_mode)
        add_flag(parts, "--fsdp_transformer_layer_cls_to_wrap", resolve_layer_class(args))
    elif args.recipe == "deepspeed-offload":
        add_flag(parts, "--deepspeed", args.deepspeed_config)
    else:
        raise ValueError(f"Unknown recipe: {args.recipe}")

    add_flag(parts, "--tf32", _str_bool(args.tf32))
    return parts


def resolve_layer_class(args: argparse.Namespace) -> str:
    if args.fsdp_transformer_layer_cls_to_wrap:
        return args.fsdp_transformer_layer_cls_to_wrap

    family = args.model_family
    if family == "auto":
        family = infer_model_family(args.model_name_or_path)
    if family in FSDP_LAYER_BY_FAMILY:
        return FSDP_LAYER_BY_FAMILY[family]

    raise SystemExit(
        "FSDP recipe needs a transformer layer class. Pass --model_family llama, "
        "--model_family opt, or --fsdp_transformer_layer_cls_to_wrap <ClassName>."
    )


def format_command(parts: List[str], single_line: bool) -> str:
    quoted = quote_parts(parts)
    if single_line:
        return " ".join(quoted)

    launcher = " ".join(quoted[:6])
    rest = quoted[6:]
    continuation = "\\"
    lines = [f"{launcher} {continuation}"]
    segments = [" ".join(rest[index : index + 2]) for index in range(0, len(rest), 2)]
    for index, segment in enumerate(segments):
        suffix = f" {continuation}" if index < len(segments) - 1 else ""
        lines.append(f"    {segment}{suffix}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a safe torchrun command for Stanford Alpaca supervised fine-tuning.",
        epilog="The command is a preview only; copy it deliberately to launch training.",
    )
    parser.add_argument("--model_name_or_path", required=True, help="HF model id or local checkpoint/tokenizer path.")
    parser.add_argument("--data_path", required=True, help="Validated Alpaca-style JSON training data path.")
    parser.add_argument("--output_dir", required=True, help="Training output/checkpoint directory.")
    parser.add_argument(
        "--recipe",
        choices=["fsdp-full-shard", "fsdp-offload", "deepspeed-offload"],
        default="fsdp-full-shard",
        help="Training sharding/offload recipe to render.",
    )
    parser.add_argument(
        "--model_family",
        choices=["auto", "llama", "opt"],
        default="auto",
        help="Model family used to infer the FSDP layer class when --recipe is FSDP.",
    )
    parser.add_argument(
        "--fsdp_transformer_layer_cls_to_wrap",
        default=None,
        help="Override FSDP auto-wrap class, e.g. LlamaDecoderLayer or OPTDecoderLayer.",
    )
    parser.add_argument("--trainer_script", default="scripts/train_alpaca_sft.py", help="Skill-owned trainer script path to render.")
    parser.add_argument(
        "--deepspeed_config",
        default="scripts/default_offload_opt_param.json",
        help="DeepSpeed ZeRO-3 offload config path for deepspeed-offload recipe.",
    )
    parser.add_argument("--nproc_per_node", type=int, default=4, help="Number of torchrun processes/GPU devices on this node.")
    parser.add_argument("--master_port", default="29500", help="torchrun master port.")
    parser.add_argument("--num_train_epochs", default="3", help="Number of training epochs.")
    parser.add_argument("--per_device_train_batch_size", type=int, default=4, help="Micro-batch per GPU/process.")
    parser.add_argument("--per_device_eval_batch_size", type=int, default=4, help="Eval micro-batch.")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=8, help="Accumulation steps.")
    parser.add_argument("--target_global_batch_size", type=int, default=128, help="Target batch size used for warning comments.")
    parser.add_argument("--learning_rate", default="2e-5", help="Learning rate.")
    parser.add_argument("--weight_decay", default="0.", help="Weight decay.")
    parser.add_argument("--warmup_ratio", default="0.03", help="Warmup ratio.")
    parser.add_argument("--lr_scheduler_type", default="cosine", help="HF scheduler type for FSDP recipes.")
    parser.add_argument("--logging_steps", default="1", help="Logging steps for FSDP recipes.")
    parser.add_argument("--evaluation_strategy", default="no", choices=["no", "steps", "epoch"], help="HF evaluation strategy.")
    parser.add_argument("--save_strategy", default="steps", choices=["no", "steps", "epoch"], help="HF save strategy.")
    parser.add_argument("--save_steps", default="2000", help="Checkpoint save interval.")
    parser.add_argument("--save_total_limit", default="1", help="Maximum checkpoints to keep.")
    parser.add_argument("--bf16", action=argparse.BooleanOptionalAction, default=True, help="Render --bf16 True/False.")
    parser.add_argument("--tf32", action=argparse.BooleanOptionalAction, default=True, help="Render --tf32 True/False.")
    parser.add_argument("--single_line", action="store_true", help="Print the command on one line.")
    parser.add_argument("--no_comments", action="store_true", help="Suppress explanatory shell comments.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    parts = build_parts(args)
    global_batch = args.nproc_per_node * args.per_device_train_batch_size * args.gradient_accumulation_steps

    if not args.no_comments:
        print("# Safe preview: this helper prints command text and does not launch training.")
        print(
            "# global_batch_size = "
            f"{args.nproc_per_node} * {args.per_device_train_batch_size} * "
            f"{args.gradient_accumulation_steps} = {global_batch}"
        )
        if global_batch != args.target_global_batch_size:
            print(f"# Warning: global batch differs from target {args.target_global_batch_size}.")
        if args.recipe == "deepspeed-offload":
            print("# Requires deepspeed installed in the training environment.")

    print(format_command(parts, single_line=args.single_line))


if __name__ == "__main__":
    main()
