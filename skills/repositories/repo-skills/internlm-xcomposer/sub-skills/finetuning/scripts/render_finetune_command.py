#!/usr/bin/env python3
"""Render editable InternLM-XComposer 2.5 finetuning commands.

The helper is intentionally stdlib-only and non-executing. It prints a shell,
Markdown, or JSON plan for torchrun + DeepSpeed/FSDP launches. It never imports
model libraries, starts training, downloads checkpoints, or checks GPUs.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import asdict, dataclass, field
from typing import List, Optional, Sequence


DEFAULT_TARGET_MODULES = [
    "attention.wqkv",
    "attention.wo",
    "feed_forward.w1",
    "feed_forward.w2",
    "feed_forward.w3",
]

PRESETS = {
    "tiny": {
        "gpus": 1,
        "batch_size": 1,
        "gradient_accumulation_steps": 1,
        "max_length": 512,
    },
    "source": {
        "gpus": 8,
        "batch_size": 2,
        "gradient_accumulation_steps": 8,
        "max_length": 16384,
    },
}


@dataclass
class CommandPlan:
    preset: str
    mode: str
    launcher: str
    backend: str
    model: str
    data: str
    output_dir: str
    notes: List[str] = field(default_factory=list)
    env_lines: List[str] = field(default_factory=list)
    command_tokens: List[str] = field(default_factory=list)


@dataclass
class FilledArgs:
    preset: str
    mode: str
    launcher: str
    backend: str
    model: str
    data: str
    output_dir: str
    entrypoint: str
    gpus: int
    nnodes: int
    node_rank: int
    master_addr: str
    master_port: str
    sample_mode: str
    bf16: bool
    fix_vit: bool
    fix_sampler: bool
    use_lora: bool
    hd_num: int
    resolution: Optional[int]
    num_train_epochs: str
    batch_size: int
    per_device_train_batch_size: int
    per_device_eval_batch_size: int
    gradient_accumulation_steps: int
    learning_rate: str
    weight_decay: str
    adam_beta2: str
    warmup_ratio: str
    lr_scheduler_type: str
    logging_steps: int
    report_to: str
    max_length: int
    evaluation_strategy: str
    save_strategy: str
    save_total_limit: int
    deepspeed_config: str
    fsdp_args: str
    gradient_checkpointing: bool
    lora_r: int
    lora_alpha: int
    lora_dropout: str
    lora_target_modules: List[str]
    lora_bias: str
    extra_arg: List[str]


def _quote(value: str) -> str:
    return shlex.quote(str(value))


def _bool(value: bool) -> str:
    return "True" if value else "False"


def _split_modules(values: Sequence[str] | None) -> List[str]:
    if not values:
        return list(DEFAULT_TARGET_MODULES)
    modules: List[str] = []
    for raw in values:
        for item in raw.split(","):
            item = item.strip()
            if item:
                modules.append(item)
    return modules or list(DEFAULT_TARGET_MODULES)


def _fill_args(args: argparse.Namespace) -> FilledArgs:
    preset = PRESETS[args.preset]
    mode = args.mode
    output_dir = args.output_dir or ("output/finetune_lora" if mode == "lora" else "output/finetune")
    learning_rate = args.learning_rate or ("5e-5" if mode == "lora" else "1e-5")
    fix_vit = mode == "lora"
    fix_sampler = mode == "lora"
    use_lora = mode == "lora"
    return FilledArgs(
        preset=args.preset,
        mode=mode,
        launcher=args.launcher,
        backend=args.backend,
        model=args.model,
        data=args.data,
        output_dir=output_dir,
        entrypoint=args.entrypoint,
        gpus=args.gpus if args.gpus is not None else preset["gpus"],
        nnodes=args.nnodes,
        node_rank=args.node_rank,
        master_addr=args.master_addr,
        master_port=args.master_port,
        sample_mode=args.sample_mode,
        bf16=args.bf16,
        fix_vit=fix_vit,
        fix_sampler=fix_sampler,
        use_lora=use_lora,
        hd_num=args.hd_num,
        resolution=args.resolution,
        num_train_epochs=args.num_train_epochs,
        batch_size=args.batch_size if args.batch_size is not None else preset["batch_size"],
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_eval_batch_size,
        gradient_accumulation_steps=(
            args.gradient_accumulation_steps
            if args.gradient_accumulation_steps is not None
            else preset["gradient_accumulation_steps"]
        ),
        learning_rate=learning_rate,
        weight_decay=args.weight_decay,
        adam_beta2=args.adam_beta2,
        warmup_ratio=args.warmup_ratio,
        lr_scheduler_type=args.lr_scheduler_type,
        logging_steps=args.logging_steps,
        report_to=args.report_to,
        max_length=args.max_length if args.max_length is not None else preset["max_length"],
        evaluation_strategy=args.evaluation_strategy,
        save_strategy=args.save_strategy,
        save_total_limit=args.save_total_limit,
        deepspeed_config=args.deepspeed_config,
        fsdp_args=args.fsdp_args,
        gradient_checkpointing=args.gradient_checkpointing,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        lora_target_modules=_split_modules(args.lora_target_modules),
        lora_bias=args.lora_bias,
        extra_arg=list(args.extra_arg or []),
    )


def _training_tokens(cfg: FilledArgs) -> List[str]:
    tokens: List[str] = [
        "--model_name_or_path",
        "$MODEL",
        "--data_path",
        "$DATA",
        "--given_num",
        _bool(cfg.sample_mode == "given_num"),
        "--bf16",
        _bool(cfg.bf16),
        "--fix_vit",
        _bool(cfg.fix_vit),
        "--fix_sampler",
        _bool(cfg.fix_sampler),
        "--use_lora",
        _bool(cfg.use_lora),
        "--hd_num",
        str(cfg.hd_num),
        "--output_dir",
        cfg.output_dir,
        "--num_train_epochs",
        cfg.num_train_epochs,
        "--batch_size",
        str(cfg.batch_size),
        "--per_device_train_batch_size",
        str(cfg.per_device_train_batch_size),
        "--per_device_eval_batch_size",
        str(cfg.per_device_eval_batch_size),
        "--gradient_accumulation_steps",
        str(cfg.gradient_accumulation_steps),
        "--evaluation_strategy",
        cfg.evaluation_strategy,
        "--save_strategy",
        cfg.save_strategy,
        "--save_total_limit",
        str(cfg.save_total_limit),
        "--learning_rate",
        cfg.learning_rate,
        "--weight_decay",
        cfg.weight_decay,
        "--adam_beta2",
        cfg.adam_beta2,
        "--warmup_ratio",
        cfg.warmup_ratio,
        "--lr_scheduler_type",
        cfg.lr_scheduler_type,
        "--logging_steps",
        str(cfg.logging_steps),
        "--report_to",
        cfg.report_to,
        "--max_length",
        str(cfg.max_length),
    ]
    if cfg.resolution is not None:
        tokens.extend(["--resolution", str(cfg.resolution)])
    if cfg.backend == "deepspeed":
        tokens.extend(["--deepspeed", cfg.deepspeed_config])
    elif cfg.backend == "fsdp":
        tokens.extend(["--fsdp", cfg.fsdp_args])
    if cfg.gradient_checkpointing:
        tokens.extend(["--gradient_checkpointing", "True"])
    else:
        tokens.extend(["--gradient_checkpointing", "False"])

    if cfg.mode == "lora":
        tokens.extend([
            "--lora_r",
            str(cfg.lora_r),
            "--lora_alpha",
            str(cfg.lora_alpha),
            "--lora_dropout",
            cfg.lora_dropout,
            "--lora_target_modules",
        ])
        tokens.extend(cfg.lora_target_modules)
        tokens.extend(["--lora_bias", cfg.lora_bias])

    tokens.extend(cfg.extra_arg)
    return tokens


def build_plan(cfg: FilledArgs) -> CommandPlan:
    notes: List[str] = [
        "Non-executing render: review every path, GPU count, backend flag, and output directory before running.",
        "The 'tiny' preset is command-review oriented; use --preset source for source-template scale values.",
    ]
    if cfg.backend == "fsdp":
        notes.append("FSDP is rendered as Hugging Face Trainer args on finetune.py; the checked-in shell templates use DeepSpeed.")
    if cfg.backend == "deepspeed":
        notes.append("DeepSpeed mode follows the source-template pattern with torchrun plus --deepspeed.")
    if cfg.mode == "lora":
        notes.append("LoRA mode freezes ViT and sampler by default and renders PEFT LoRA arguments.")

    env_lines = [
        "export CUDA_DEVICE_MAX_CONNECTIONS=1",
        f"export MODEL={_quote(cfg.model)}",
        f"export DATA={_quote(cfg.data)}",
    ]

    if cfg.launcher == "torchrun":
        command_tokens = [
            "torchrun",
            "--nproc_per_node",
            str(cfg.gpus),
            "--nnodes",
            str(cfg.nnodes),
            "--node_rank",
            str(cfg.node_rank),
            "--master_addr",
            cfg.master_addr,
            "--master_port",
            str(cfg.master_port),
            cfg.entrypoint,
        ]
    else:
        command_tokens = ["python", cfg.entrypoint]
    command_tokens.extend(_training_tokens(cfg))

    return CommandPlan(
        preset=cfg.preset,
        mode=cfg.mode,
        launcher=cfg.launcher,
        backend=cfg.backend,
        model=cfg.model,
        data=cfg.data,
        output_dir=cfg.output_dir,
        notes=notes,
        env_lines=env_lines,
        command_tokens=command_tokens,
    )


def _render_command(tokens: Sequence[str]) -> str:
    if not tokens:
        return ""
    rendered: List[str] = []
    for index, token in enumerate(tokens):
        suffix = " \\" if index < len(tokens) - 1 else ""
        prefix = "" if index == 0 else "  "
        if token in {"$MODEL", "$DATA"}:
            value = f'"{token}"'
        else:
            value = _quote(token)
        rendered.append(f"{prefix}{value}{suffix}")
    return "\n".join(rendered)


def render_shell(plan: CommandPlan) -> str:
    lines: List[str] = []
    lines.append("# InternLM-XComposer 2.5 finetuning command plan")
    for note in plan.notes:
        lines.append(f"# {note}")
    lines.extend(plan.env_lines)
    lines.append(_render_command(plan.command_tokens))
    return "\n".join(lines)


def render_markdown(plan: CommandPlan) -> str:
    lines: List[str] = [
        "# InternLM-XComposer 2.5 finetuning command plan",
        "",
        "## Summary",
        "",
        f"- preset: `{plan.preset}`",
        f"- mode: `{plan.mode}`",
        f"- launcher: `{plan.launcher}`",
        f"- backend: `{plan.backend}`",
        f"- model: `{plan.model}`",
        f"- data: `{plan.data}`",
        f"- output dir: `{plan.output_dir}`",
        "",
        "## Notes",
        "",
    ]
    lines.extend(f"- {note}" for note in plan.notes)
    lines.extend(["", "## Command", "", "```bash"])
    lines.extend(plan.env_lines)
    lines.append(_render_command(plan.command_tokens))
    lines.append("```")
    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render non-executing InternLM-XComposer 2.5 finetuning commands.")
    parser.add_argument("--preset", choices=sorted(PRESETS), default="tiny", help="Default scale values: tiny for review, source for source-template scale.")
    parser.add_argument("--mode", choices=["full", "lora"], default="lora", help="Training mode to render.")
    parser.add_argument("--launcher", choices=["torchrun", "python"], default="torchrun", help="Process launcher to render.")
    parser.add_argument("--backend", choices=["deepspeed", "fsdp", "none"], default="deepspeed", help="Training backend flags to render.")
    parser.add_argument("--model", default="internlm/internlm-xcomposer2d5-7b", help="Base model id or local checkpoint path.")
    parser.add_argument("--data", default="data.txt", help="data.txt manifest or direct JSON list path.")
    parser.add_argument("--output-dir", help="Output directory; defaults by mode.")
    parser.add_argument("--entrypoint", default="finetune.py", help="Training script path to render.")
    parser.add_argument("--gpus", type=int, help="torchrun --nproc_per_node value; defaults by preset.")
    parser.add_argument("--nnodes", type=int, default=1)
    parser.add_argument("--node-rank", type=int, default=0)
    parser.add_argument("--master-addr", default="localhost")
    parser.add_argument("--master-port", default="6001")
    parser.add_argument("--sample-mode", choices=["given_num", "ratio"], default="given_num", help="How finetune.py should interpret data.txt numbers.")
    parser.add_argument("--bf16", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--hd-num", type=int, default=18)
    parser.add_argument("--resolution", type=int, help="Optional 2.5 image preprocessing resolution override.")
    parser.add_argument("--num-train-epochs", default="1")
    parser.add_argument("--batch-size", type=int, help="Custom data-mixer batch_size; defaults by preset.")
    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--per-device-eval-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, help="Defaults by preset.")
    parser.add_argument("--learning-rate", help="Defaults by mode: 1e-5 full, 5e-5 LoRA.")
    parser.add_argument("--weight-decay", default="0.1")
    parser.add_argument("--adam-beta2", default="0.95")
    parser.add_argument("--warmup-ratio", default="0.01")
    parser.add_argument("--lr-scheduler-type", default="cosine")
    parser.add_argument("--logging-steps", type=int, default=1)
    parser.add_argument("--report-to", default="none")
    parser.add_argument("--max-length", type=int, help="Defaults by preset.")
    parser.add_argument("--evaluation-strategy", default="no")
    parser.add_argument("--save-strategy", default="epoch")
    parser.add_argument("--save-total-limit", type=int, default=1)
    parser.add_argument("--deepspeed-config", default="ds_config_zero2.json")
    parser.add_argument("--fsdp-args", default="full_shard auto_wrap", help="Value passed to --fsdp when backend=fsdp.")
    parser.add_argument("--gradient-checkpointing", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--lora-r", type=int, default=64)
    parser.add_argument("--lora-alpha", type=int, default=64)
    parser.add_argument("--lora-dropout", default="0.05")
    parser.add_argument("--lora-target-modules", action="append", help="Comma-separated or repeated LoRA target module names.")
    parser.add_argument("--lora-bias", choices=["none", "all", "lora_only"], default="none")
    parser.add_argument("--extra-arg", action="append", help="Append a raw extra training argument token. Repeat for multiple tokens.")
    parser.add_argument("--format", choices=["shell", "markdown", "json"], default="shell")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    cfg = _fill_args(args)
    if cfg.gpus < 1:
        print("error: --gpus must be >= 1", file=sys.stderr)
        return 2
    if cfg.nnodes < 1:
        print("error: --nnodes must be >= 1", file=sys.stderr)
        return 2
    if cfg.backend == "fsdp" and cfg.launcher == "python":
        print("warning: FSDP normally needs torchrun for multi-process execution", file=sys.stderr)
    plan = build_plan(cfg)
    if args.format == "json":
        print(json.dumps(asdict(plan), indent=2))
    elif args.format == "markdown":
        print(render_markdown(plan))
    else:
        print(render_shell(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
