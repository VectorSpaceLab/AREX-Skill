#!/usr/bin/env python3
"""Render a safe IXC-2.5-Reward training command.

The helper is intentionally stdlib-only. It reads environment variables, builds
an explicit torchrun command for the source finetune.py launcher, and prints it
without executing training or importing model libraries.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from typing import Any, Dict, List, Optional, Sequence


def env_or_default(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


def env_int(name: str, default: int) -> int:
    raw = env_or_default(name, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def add_default_true_flag(parser: argparse.ArgumentParser, name: str, help_text: str) -> None:
    dest = name.replace("-", "_")
    setting = help_text
    for prefix in ("Enable ", "enable "):
        if setting.startswith(prefix):
            setting = setting[len(prefix):]
            break
    parser.add_argument(f"--{name}", dest=dest, action="store_true", help=help_text)
    parser.add_argument(
        f"--no-{name}",
        dest=dest,
        action="store_false",
        help=f"Disable {setting}",
    )
    parser.set_defaults(**{dest: True})


def q(value: Any) -> str:
    return shlex.quote(str(value))


def bool_literal(value: bool) -> str:
    return "True" if value else "False"


def default_output_dir(mode: str) -> str:
    return "output/ixc_reward_lora" if mode == "lora" else "output/ixc_reward"


def render_shell(args: argparse.Namespace) -> str:
    nnodes = args.nnodes
    gpus_per_node = args.gpus_per_node
    node_rank = args.node_rank
    master_addr = args.master_addr
    master_port = args.master_port

    exports = [
        "export CUDA_DEVICE_MAX_CONNECTIONS=1",
        f"export MASTER_PORT={q(master_port)}",
        "export CPUS_PER_TASK=12",
        f"export NNODES={q(nnodes)}",
        f"export GPUS_PER_NODE={q(gpus_per_node)}",
        f"export NODE_RANK={q(node_rank)}",
        f"export MASTER_ADDR={q(master_addr)}",
        f"export MASTER_PORT={q(master_port)}",
    ]

    torchrun_parts = [
        "torchrun",
        "--nnodes",
        str(nnodes),
        "--nproc_per_node",
        str(gpus_per_node),
        "--node_rank",
        str(node_rank),
        "--master_addr",
        str(master_addr),
        "--master_port",
        str(master_port),
        args.finetune_script,
        "--model_name_or_path",
        args.model_path,
        "--data_path",
        args.data_path,
        "--given_num",
        bool_literal(args.given_num),
        "--bf16",
        bool_literal(args.bf16),
        "--fix_vit",
        bool_literal(args.fix_vit),
        "--fix_sampler",
        bool_literal(args.fix_sampler),
        "--use_lora",
        bool_literal(args.mode == "lora"),
    ]

    if args.mode == "lora":
        torchrun_parts.extend(["--lora_r", str(args.lora_r)])

    torchrun_parts.extend(
        [
            "--hd_num",
            str(args.hd_num),
            "--output_dir",
            args.output_dir,
            "--num_train_epochs",
            str(args.num_train_epochs),
            "--batch_size",
            str(args.batch_size),
            "--per_device_train_batch_size",
            str(args.per_device_train_batch_size),
            "--per_device_eval_batch_size",
            str(args.per_device_eval_batch_size),
            "--gradient_accumulation_steps",
            str(args.gradient_accumulation_steps),
            "--evaluation_strategy",
            args.evaluation_strategy,
            "--save_strategy",
            args.save_strategy,
            "--save_total_limit",
            str(args.save_total_limit),
            "--learning_rate",
            str(args.learning_rate),
            "--weight_decay",
            str(args.weight_decay),
            "--adam_beta2",
            str(args.adam_beta2),
            "--warmup_ratio",
            str(args.warmup_ratio),
            "--lr_scheduler_type",
            args.lr_scheduler_type,
            "--logging_steps",
            str(args.logging_steps),
            "--report_to",
            args.report_to,
            "--max_length",
            str(args.max_length),
            "--deepspeed",
            args.deepspeed,
            "--gradient_checkpointing",
            bool_literal(args.gradient_checkpointing),
        ]
    )

    lines = ["# IXC-2.5-Reward training launcher (render only)"]
    if args.mode == "lora":
        lines.append("# LoRA adapters record the base model path; prefer an absolute local --model-path when training locally.")
    lines.extend(exports)
    lines.append("")
    lines.append(shlex.join(torchrun_parts))
    return "\n".join(lines)


def render_json(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "mode": args.mode,
        "env": {
            "CUDA_DEVICE_MAX_CONNECTIONS": "1",
            "MASTER_PORT": args.master_port,
            "CPUS_PER_TASK": "12",
            "NNODES": args.nnodes,
            "GPUS_PER_NODE": args.gpus_per_node,
            "NODE_RANK": args.node_rank,
            "MASTER_ADDR": args.master_addr,
        },
        "command": {
            "program": "torchrun",
            "script": args.finetune_script,
            "argv": [
                "--nnodes",
                str(args.nnodes),
                "--nproc_per_node",
                str(args.gpus_per_node),
                "--node_rank",
                str(args.node_rank),
                "--master_addr",
                args.master_addr,
                "--master_port",
                str(args.master_port),
                args.finetune_script,
                "--model_name_or_path",
                args.model_path,
                "--data_path",
                args.data_path,
                "--given_num",
                bool_literal(args.given_num),
                "--bf16",
                bool_literal(args.bf16),
                "--fix_vit",
                bool_literal(args.fix_vit),
                "--fix_sampler",
                bool_literal(args.fix_sampler),
                "--use_lora",
                bool_literal(args.mode == "lora"),
                *(["--lora_r", str(args.lora_r)] if args.mode == "lora" else []),
                "--hd_num",
                str(args.hd_num),
                "--output_dir",
                args.output_dir,
                "--num_train_epochs",
                str(args.num_train_epochs),
                "--batch_size",
                str(args.batch_size),
                "--per_device_train_batch_size",
                str(args.per_device_train_batch_size),
                "--per_device_eval_batch_size",
                str(args.per_device_eval_batch_size),
                "--gradient_accumulation_steps",
                str(args.gradient_accumulation_steps),
                "--evaluation_strategy",
                args.evaluation_strategy,
                "--save_strategy",
                args.save_strategy,
                "--save_total_limit",
                str(args.save_total_limit),
                "--learning_rate",
                str(args.learning_rate),
                "--weight_decay",
                str(args.weight_decay),
                "--adam_beta2",
                str(args.adam_beta2),
                "--warmup_ratio",
                str(args.warmup_ratio),
                "--lr_scheduler_type",
                args.lr_scheduler_type,
                "--logging_steps",
                str(args.logging_steps),
                "--report_to",
                args.report_to,
                "--max_length",
                str(args.max_length),
                "--deepspeed",
                args.deepspeed,
                "--gradient_checkpointing",
                bool_literal(args.gradient_checkpointing),
            ],
        },
        "notes": [
            "The renderer never executes training; it only prints a shell command.",
            "The source scripts use DeepSpeed ZeRO-2 and torchrun.",
            "Use a local absolute model path for LoRA when possible so adapter metadata remains stable.",
        ],
        "warnings": _collect_warnings(args),
    }


def _collect_warnings(args: argparse.Namespace) -> List[str]:
    warnings: List[str] = []
    if "iinternlm" in args.model_path:
        warnings.append("model path contains the README typo 'iinternlm'; did you mean 'internlm'?")
    if args.mode == "lora" and not os.path.isabs(args.model_path) and not args.model_path.startswith("internlm/"):
        warnings.append("LoRA adapters usually work best with an absolute local base-model path.")
    if args.hd_num > 18:
        warnings.append("hd_num is above the documented default of 18; this may increase VRAM usage.")
    if args.max_length > 16384:
        warnings.append("max_length exceeds the README default and may require large-GPU flash-attn capacity.")
    return warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a non-executing torchrun command for IXC-2.5-Reward training.",
    )
    parser.add_argument("--mode", choices=("full", "lora"), default="full", help="Render the full-parameter or LoRA launcher.")
    parser.add_argument("--model-path", default="internlm/internlm-xcomposer2d5-7b-reward", help="Model id or checkpoint path for --model_name_or_path.")
    parser.add_argument("--data-path", default="data.txt", help="Training manifest or JSON path for --data_path.")
    parser.add_argument("--output-dir", default=None, help="Output directory. Defaults to output/ixc_reward or output/ixc_reward_lora.")
    parser.add_argument("--finetune-script", default="finetune.py", help="Launcher script name to render after torchrun.")
    parser.add_argument("--deepspeed", default="ds_config_zero2.json", help="DeepSpeed config path.")

    parser.add_argument("--nnodes", type=int, default=env_int("MLP_WORKER_NUM", 1), help="torchrun --nnodes value.")
    parser.add_argument("--gpus-per-node", type=int, default=env_int("MLP_WORKER_GPU", 1), help="torchrun --nproc_per_node value.")
    parser.add_argument("--node-rank", type=int, default=env_int("MLP_ROLE_INDEX", 0), help="torchrun --node_rank value.")
    parser.add_argument("--master-addr", default=env_or_default("MLP_WORKER_0_HOST", "127.0.0.1"), help="torchrun --master_addr value.")
    parser.add_argument("--master-port", type=int, default=env_int("MLP_WORKER_0_PORT", 29501), help="torchrun --master_port value.")

    parser.add_argument("--given-num", dest="given_num", action="store_true", help="Render --given_num True.")
    parser.add_argument("--ratio-mode", dest="given_num", action="store_false", help="Render --given_num False for ratio-based sampling.")
    parser.set_defaults(given_num=True)

    add_default_true_flag(parser, "bf16", "Enable bf16")
    add_default_true_flag(parser, "fix-vit", "Freeze the ViT encoder")
    add_default_true_flag(parser, "fix-sampler", "Freeze the projection layer after ViT")
    add_default_true_flag(parser, "gradient-checkpointing", "Enable gradient checkpointing")

    parser.add_argument("--lora-r", type=int, default=512, help="LoRA rank used when mode is lora.")
    parser.add_argument("--hd-num", type=int, default=9, help="Reward-model hd_num value rendered into the command.")
    parser.add_argument("--max-length", type=int, default=8192, help="Maximum sequence length.")
    parser.add_argument("--num-train-epochs", type=int, default=1, help="Number of training epochs.")
    parser.add_argument("--batch-size", type=int, default=1, help="Source DataArguments batch_size.")
    parser.add_argument("--per-device-train-batch-size", type=int, default=1, help="Trainer per-device train batch size.")
    parser.add_argument("--per-device-eval-batch-size", type=int, default=1, help="Trainer per-device eval batch size.")
    parser.add_argument("--gradient-accumulation-steps", type=int, default=2, help="Gradient accumulation steps.")
    parser.add_argument("--evaluation-strategy", default="no", help="Trainer evaluation strategy.")
    parser.add_argument("--save-strategy", default="epoch", help="Trainer save strategy.")
    parser.add_argument("--save-total-limit", type=int, default=1, help="Trainer save_total_limit.")
    parser.add_argument("--learning-rate", type=float, default=1e-5, help="Learning rate.")
    parser.add_argument("--weight-decay", type=float, default=0.1, help="Weight decay.")
    parser.add_argument("--adam-beta2", type=float, default=0.95, help="Adam beta2.")
    parser.add_argument("--warmup-ratio", type=float, default=0.01, help="Warmup ratio.")
    parser.add_argument("--lr-scheduler-type", default="cosine", help="LR scheduler type.")
    parser.add_argument("--logging-steps", type=int, default=1, help="Logging steps.")
    parser.add_argument("--report-to", default="none", help="Trainer report_to setting.")
    parser.add_argument("--format", choices=("shell", "json"), default="shell", help="Output format.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.output_dir is None:
        args.output_dir = default_output_dir(args.mode)

    if args.nnodes < 1 or args.gpus_per_node < 1:
        parser.error("--nnodes and --gpus-per-node must be at least 1")
    if args.master_port < 1 or args.master_port > 65535:
        parser.error("--master-port must be between 1 and 65535")
    if args.hd_num < 1:
        parser.error("--hd-num must be positive")
    if args.max_length < 1:
        parser.error("--max-length must be positive")

    if args.format == "json":
        print(json.dumps(render_json(args), indent=2, ensure_ascii=False))
    else:
        print(render_shell(args))
        warnings = _collect_warnings(args)
        if warnings:
            print("\n# Warnings:")
            for warning in warnings:
                print(f"# - {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
