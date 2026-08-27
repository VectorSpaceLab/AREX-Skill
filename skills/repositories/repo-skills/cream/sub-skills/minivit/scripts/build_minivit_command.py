#!/usr/bin/env python3
"""Print MiniViT command templates without running training or evaluation."""

from __future__ import annotations

import argparse
import json
import shlex
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MiniDeiTVariant:
    model: str
    batch_train: int
    batch_eval: int
    drop_path: float
    input_size: int = 224


@dataclass(frozen=True)
class MiniSwinVariant:
    cfg: str
    tag: str
    batch_train: int
    batch_eval: int
    student_layers: str
    teacher_layers: str
    supports_distill_train: bool = True


MINI_DEIT = {
    "tiny": MiniDeiTVariant("mini_deit_tiny_patch16_224", 128, 128, 0.0),
    "small": MiniDeiTVariant("mini_deit_small_patch16_224", 128, 128, 0.0),
    "base": MiniDeiTVariant("mini_deit_base_patch16_224", 128, 128, 0.1),
    "base-384": MiniDeiTVariant("mini_deit_base_patch16_384", 32, 32, 0.1, input_size=384),
}

MINI_SWIN = {
    "tiny": MiniSwinVariant(
        "configs/swin_tiny_patch4_window7_224_minivit_sharenum6.yaml",
        "mini-swin-tiny",
        128,
        64,
        "11_9_7_5_3_1",
        "23_21_15_9_3_1",
    ),
    "small": MiniSwinVariant(
        "configs/swin_small_patch4_window7_224_minivit_sharenum2.yaml",
        "mini-swin-small",
        128,
        64,
        "23_21_15_9_3_1",
        "23_21_15_9_3_1",
    ),
    "base": MiniSwinVariant(
        "configs/swin_base_patch4_window7_224_minivit_sharenum2.yaml",
        "mini-swin-base",
        128,
        64,
        "23_21_15_9_3_1",
        "23_21_15_9_3_1",
    ),
    "base-384": MiniSwinVariant(
        "configs/swin_base_patch4_window7_224to384_minivit_sharenum2_adamw.yaml",
        "mini-swin-base-224to384",
        16,
        32,
        "23_21_15_9_3_1",
        "23_21_15_9_3_1",
        supports_distill_train=False,
    ),
}

WORKFLOWS = [
    "mini-deit-train",
    "mini-deit-eval",
    "mini-deit-finetune-384",
    "mini-swin-train",
    "mini-swin-eval",
    "mini-swin-finetune-384",
]

PLACEHOLDER = {
    "data": "/path/to/ImageNet",
    "output": "/path/to/output",
    "checkpoint": "/path/to/checkpoint.pth",
    "teacher": "/path/to/teacher.pth",
}


def quote(value: str | int | float) -> str:
    return shlex.quote(str(value))


def join(parts: Iterable[str | int | float]) -> str:
    return " ".join(quote(part) for part in parts)


def launcher(script: str, nproc: int, use_env: bool) -> list[str]:
    parts = ["python", "-m", "torch.distributed.launch", f"--nproc_per_node={nproc}"]
    if use_env:
        parts.append("--use_env")
    parts.append(script)
    return parts


def parse_layer_list(value: str) -> list[int]:
    stripped = value.strip().strip("[]")
    if not stripped:
        return []
    return [int(part) for part in stripped.split("_") if part]


def layer_warnings(student_layers: str, teacher_layers: str, student_max: int) -> list[str]:
    warnings: list[str] = []
    try:
        student = parse_layer_list(student_layers)
        teacher = parse_layer_list(teacher_layers)
    except ValueError as exc:
        return [f"could not parse layer list: {exc}"]
    if len(student) != len(teacher):
        warnings.append(f"student/teacher layer-list lengths differ ({len(student)} vs {len(teacher)})")
    if any(layer < 0 or layer > student_max for layer in student):
        warnings.append(f"student layer ids should be in [0, {student_max}] for this variant")
    if any(layer < 0 for layer in teacher):
        warnings.append("teacher layer ids must be non-negative")
    return warnings


def deit_parts(args: argparse.Namespace) -> tuple[list[str], list[str], str]:
    variant = MINI_DEIT[args.variant]
    data = args.data_path or PLACEHOLDER["data"]
    output = args.output or PLACEHOLDER["output"]
    warnings: list[str] = []
    note = "Run from the Mini-DeiT project directory in a Cream checkout."

    if args.workflow == "mini-deit-train":
        if args.variant == "base-384":
            warnings.append("Base-384 is normally a finetune/eval path; consider --workflow mini-deit-finetune-384")
        parts = launcher("main.py", args.nproc_per_node, use_env=True) + [
            "--model", variant.model,
            "--batch-size", args.batch_size or variant.batch_train,
            "--data-path", data,
            "--output_dir", output,
            "--teacher-model", args.teacher_model,
            "--distillation-type", args.distillation_type,
            "--distillation-alpha", args.distillation_alpha,
            "--drop-path", variant.drop_path,
        ]
        if args.teacher_path:
            parts += ["--teacher-path", args.teacher_path]
        else:
            warnings.append("no Mini-DeiT --teacher-path supplied; running may use/download a pretrained teacher")
        if variant.input_size != 224:
            parts += ["--input-size", variant.input_size]
        if args.dataset_format == "tar":
            parts.append("--load-tar")
        return parts + args.extra_args, warnings, note

    if args.workflow == "mini-deit-eval":
        checkpoint = args.checkpoint or PLACEHOLDER["checkpoint"]
        if not args.checkpoint:
            warnings.append("checkpoint placeholder emitted; replace before running")
        parts = launcher("main.py", args.nproc_per_node, use_env=True) + [
            "--model", variant.model,
            "--batch-size", args.batch_size or variant.batch_eval,
            "--data-path", data,
            "--output_dir", output,
            "--resume", checkpoint,
        ]
        if variant.input_size != 224:
            parts += ["--input-size", variant.input_size]
        parts.append("--eval")
        if args.dataset_format == "tar":
            parts.append("--load-tar")
        return parts + args.extra_args, warnings, note

    if args.workflow == "mini-deit-finetune-384":
        checkpoint = args.checkpoint or PLACEHOLDER["checkpoint"]
        if not args.checkpoint:
            warnings.append("224-resolution checkpoint placeholder emitted; replace before running")
        parts = launcher("main.py", args.nproc_per_node, use_env=True) + [
            "--model", MINI_DEIT["base-384"].model,
            "--batch-size", args.batch_size or MINI_DEIT["base-384"].batch_train,
            "--data-path", data,
            "--output_dir", output,
            "--finetune", checkpoint,
            "--input-size", 384,
            "--lr", "5e-6",
            "--min-lr", "5e-6",
            "--weight-decay", "1e-8",
            "--epochs", args.epochs,
        ]
        if args.dataset_format == "tar":
            parts.append("--load-tar")
        return parts + args.extra_args, warnings, note

    raise AssertionError(args.workflow)


def swin_parts(args: argparse.Namespace) -> tuple[list[str], list[str], str]:
    variant = MINI_SWIN[args.variant]
    data = args.data_path or PLACEHOLDER["data"]
    output = args.output or PLACEHOLDER["output"]
    warnings: list[str] = []
    note = "Run from the Mini-Swin project directory in a Cream checkout."

    if args.workflow == "mini-swin-train":
        if not variant.supports_distill_train:
            warnings.append("base-384 is normally finetune/eval; consider --workflow mini-swin-finetune-384")
        teacher = args.teacher or PLACEHOLDER["teacher"]
        if not args.teacher:
            warnings.append("teacher checkpoint placeholder emitted; replace before running distillation")
        student_layers = args.student_layer_list or variant.student_layers
        teacher_layers = args.teacher_layer_list or variant.teacher_layers
        warnings += layer_warnings(student_layers, teacher_layers, 11 if args.variant == "tiny" else 23)
        parts = launcher("main.py", args.nproc_per_node, use_env=False) + [
            "--cfg", variant.cfg,
            "--data-path", data,
            "--output", output,
            "--tag", args.tag or variant.tag,
            "--batch-size", args.batch_size or variant.batch_train,
            "--is_sep_layernorm",
            "--is_transform_heads",
            "--is_transform_ffn",
            "--do_distill",
            "--alpha", args.alpha,
            "--teacher", teacher,
            "--attn_loss",
            "--hidden_loss",
            "--hidden_relation",
            "--student_layer_list", student_layers,
            "--teacher_layer_list", teacher_layers,
            "--hidden_weight", args.hidden_weight,
        ]
    elif args.workflow == "mini-swin-eval":
        checkpoint = args.checkpoint or PLACEHOLDER["checkpoint"]
        if not args.checkpoint:
            warnings.append("checkpoint placeholder emitted; replace before running")
        parts = launcher("main.py", args.nproc_per_node, use_env=False) + [
            "--cfg", variant.cfg,
            "--data-path", data,
            "--batch-size", args.batch_size or variant.batch_eval,
            "--is_sep_layernorm",
            "--is_transform_ffn",
            "--is_transform_heads",
            "--resume", checkpoint,
            "--eval",
        ]
    elif args.workflow == "mini-swin-finetune-384":
        checkpoint = args.checkpoint or PLACEHOLDER["checkpoint"]
        if not args.checkpoint:
            warnings.append("224-resolution checkpoint placeholder emitted; replace before running")
        finetune = MINI_SWIN["base-384"]
        parts = launcher("main.py", args.nproc_per_node, use_env=False) + [
            "--cfg", finetune.cfg,
            "--data-path", data,
            "--output", output,
            "--tag", args.tag or finetune.tag,
            "--batch-size", args.batch_size or finetune.batch_train,
            "--accumulation-steps", args.accumulation_steps,
            "--is_sep_layernorm",
            "--is_transform_heads",
            "--is_transform_ffn",
            "--resume", checkpoint,
            "--resume_weight_only",
            "--train_224to384",
        ]
    else:
        raise AssertionError(args.workflow)

    if args.dataset_format == "tar":
        parts.append("--load_tar")
    if args.amp_opt_level:
        parts += ["--amp-opt-level", args.amp_opt_level]
    return parts + args.extra_args, warnings, note


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print MiniViT Mini-DeiT/Mini-Swin command templates without executing them.")
    parser.add_argument("--workflow", choices=WORKFLOWS, help="Template family to print.")
    parser.add_argument("--task", choices=WORKFLOWS, help=argparse.SUPPRESS)
    parser.add_argument("--variant", choices=sorted(set(MINI_DEIT) | set(MINI_SWIN)), help="Variant key; defaults to tiny except finetune-384 templates.")
    parser.add_argument("--data-path", help="ImageNet root to include in the template.")
    parser.add_argument("--output", help="Output root to include in the template.")
    parser.add_argument("--checkpoint", help="Checkpoint path for eval/resume/finetune templates.")
    parser.add_argument("--teacher", help="Mini-Swin teacher checkpoint path.")
    parser.add_argument("--teacher-path", help="Mini-DeiT teacher checkpoint path.")
    parser.add_argument("--teacher-model", default="regnety_160", help="Mini-DeiT teacher model name.")
    parser.add_argument("--distillation-type", default="soft", choices=["none", "soft", "hard"], help="Mini-DeiT distillation type.")
    parser.add_argument("--distillation-alpha", default="1.0", help="Mini-DeiT distillation alpha.")
    parser.add_argument("--alpha", default="0.0", help="Mini-Swin distillation alpha.")
    parser.add_argument("--hidden-weight", default="0.1", help="Mini-Swin hidden loss weight.")
    parser.add_argument("--student-layer-list", help="Override Mini-Swin student layer list, e.g. 11_9_7_5_3_1.")
    parser.add_argument("--teacher-layer-list", help="Override Mini-Swin teacher layer list, e.g. 23_21_15_9_3_1.")
    parser.add_argument("--batch-size", type=int, help="Override documented batch size.")
    parser.add_argument("--nproc-per-node", type=int, default=8, help="Number placed in the distributed-launch template.")
    parser.add_argument("--accumulation-steps", type=int, default=2, help="Mini-Swin 224-to-384 accumulation steps.")
    parser.add_argument("--epochs", type=int, default=30, help="Mini-DeiT Base-384 finetune epochs.")
    parser.add_argument("--dataset-format", choices=["folder", "tar"], default="folder", help="Include the branch-specific tar-loading flag.")
    parser.add_argument("--tag", help="Mini-Swin tag override.")
    parser.add_argument("--amp-opt-level", choices=["O0", "O1", "O2"], help="Optional Mini-Swin Apex AMP opt level to include; use O0 when Apex is unavailable.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    parser.add_argument("--extra-args", nargs=argparse.REMAINDER, default=[], help="Arguments appended verbatim after '--extra-args'.")
    return parser


def normalize_args(args: argparse.Namespace) -> None:
    if args.workflow and args.task and args.workflow != args.task:
        raise SystemExit("--workflow and --task disagree")
    args.workflow = args.workflow or args.task
    if not args.workflow:
        raise SystemExit("one of --workflow or --task is required")
    if not args.variant:
        args.variant = "base-384" if args.workflow.endswith("finetune-384") else "tiny"
    if args.workflow.startswith("mini-deit") and args.variant not in MINI_DEIT:
        raise SystemExit(f"variant {args.variant!r} is not valid for Mini-DeiT")
    if args.workflow.startswith("mini-swin") and args.variant not in MINI_SWIN:
        raise SystemExit(f"variant {args.variant!r} is not valid for Mini-Swin")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    normalize_args(args)
    if args.workflow.startswith("mini-deit"):
        parts, warnings, note = deit_parts(args)
    else:
        parts, warnings, note = swin_parts(args)
    command = join(parts)
    if args.format == "json":
        print(json.dumps({"workflow": args.workflow, "variant": args.variant, "cwd_note": note, "command": command, "warnings": warnings}, indent=2))
    else:
        print(f"# {note}")
        print("# Template only: this helper does not execute the command.")
        for warning in warnings:
            print(f"# WARNING: {warning}")
        print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
