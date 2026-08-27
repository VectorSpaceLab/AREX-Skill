#!/usr/bin/env python3
"""Print safe TinyViT launcher templates.

The helper only prints commands for evaluation, sparse-logit saving, logit
checks, finetuning, and training. It does not launch distributed jobs.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Request:
    task: str
    cfg: Optional[str]
    data_path: Optional[str]
    checkpoint: Optional[str]
    teacher_checkpoint: Optional[str]
    output: Optional[str]
    batch_size: int
    epochs: int
    logits_dir: Optional[str]
    extra: list[str]


def q(value: str) -> str:
    return f'"{value}"' if any(ch.isspace() for ch in value) else value


def build(req: Request) -> str:
    extra = " ".join(req.extra).strip()
    if req.task == "eval-1k":
        if not req.cfg or not req.data_path or not req.checkpoint:
            raise SystemExit("eval-1k requires --cfg, --data-path, and --checkpoint")
        return (
            f"python -m torch.distributed.launch --nproc_per_node 8 main.py --cfg {q(req.cfg)} --data-path {q(req.data_path)} "
            f"--batch-size {req.batch_size} --eval --resume {q(req.checkpoint)} {extra}".strip()
        )
    if req.task == "save-logits":
        if not req.cfg or not req.data_path or not req.teacher_checkpoint or not req.logits_dir:
            raise SystemExit("save-logits requires --cfg, --data-path, --teacher-checkpoint, and --logits-dir")
        return (
            f"python -m torch.distributed.launch --nproc_per_node 8 save_logits.py --cfg {q(req.cfg)} --data-path {q(req.data_path)} "
            f"--batch-size 128 --eval --resume {q(req.teacher_checkpoint)} --opts DISTILL.TEACHER_LOGITS_PATH {q(req.logits_dir)} {extra}"
            .strip()
        )
    if req.task == "check-logits":
        if not req.cfg or not req.data_path or not req.teacher_checkpoint or not req.logits_dir:
            raise SystemExit("check-logits requires --cfg, --data-path, --teacher-checkpoint, and --logits-dir")
        return (
            f"python -m torch.distributed.launch --nproc_per_node 8 save_logits.py --cfg {q(req.cfg)} --data-path {q(req.data_path)} "
            f"--batch-size 128 --eval --resume {q(req.teacher_checkpoint)} --check-saved-logits --opts DISTILL.TEACHER_LOGITS_PATH {q(req.logits_dir)} {extra}"
            .strip()
        )
    if req.task == "train-1k":
        if not req.cfg or not req.data_path:
            raise SystemExit("train-1k requires --cfg and --data-path")
        return (
            f"python -m torch.distributed.launch --nproc_per_node 8 main.py --cfg {q(req.cfg)} --data-path {q(req.data_path)} "
            f"--batch-size {req.batch_size} --output {q(req.output or './output')} {extra}".strip()
        )
    if req.task == "finetune-22kto1k":
        if not req.cfg or not req.data_path or not req.checkpoint:
            raise SystemExit("finetune-22kto1k requires --cfg, --data-path, and --checkpoint")
        return (
            f"python -m torch.distributed.launch --nproc_per_node 8 main.py --cfg {q(req.cfg)} --data-path {q(req.data_path)} "
            f"--batch-size {req.batch_size} --pretrained {q(req.checkpoint)} --output {q(req.output or './output')} {extra}"
            .strip()
        )
    if req.task == "finetune-highres-384":
        if not req.cfg or not req.data_path or not req.checkpoint:
            raise SystemExit("finetune-highres-384 requires --cfg, --data-path, and --checkpoint")
        return (
            f"python -m torch.distributed.launch --nproc_per_node 8 main.py --cfg {q(req.cfg)} --data-path {q(req.data_path)} "
            f"--batch-size {req.batch_size} --pretrained {q(req.checkpoint)} --output {q(req.output or './output')} --accumulation-steps 4 {extra}"
            .strip()
        )
    if req.task == "finetune-highres-512":
        if not req.cfg or not req.data_path or not req.checkpoint:
            raise SystemExit("finetune-highres-512 requires --cfg, --data-path, and --checkpoint")
        return (
            f"python -m torch.distributed.launch --nproc_per_node 8 main.py --cfg {q(req.cfg)} --data-path {q(req.data_path)} "
            f"--batch-size {req.batch_size} --pretrained {q(req.checkpoint)} --output {q(req.output or './output')} --accumulation-steps 4 {extra}"
            .strip()
        )
    if req.task == "eval-22k":
        if not req.cfg or not req.data_path or not req.checkpoint:
            raise SystemExit("eval-22k requires --cfg, --data-path, and --checkpoint")
        return (
            f"python -m torch.distributed.launch --nproc_per_node 8 main.py --cfg {q(req.cfg)} --data-path {q(req.data_path)} "
            f"--batch-size {req.batch_size} --eval --resume {q(req.checkpoint)} --opts DATA.DATASET imagenet {extra}".strip()
        )
    raise SystemExit(f"unsupported task: {req.task}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Print safe TinyViT command templates")
    parser.add_argument(
        "--task",
        required=True,
        choices=[
            "eval-1k",
            "save-logits",
            "check-logits",
            "train-1k",
            "finetune-22kto1k",
            "finetune-highres-384",
            "finetune-highres-512",
            "eval-22k",
        ],
    )
    parser.add_argument("--cfg")
    parser.add_argument("--data-path")
    parser.add_argument("--checkpoint")
    parser.add_argument("--teacher-checkpoint")
    parser.add_argument("--output")
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--logits-dir")
    parser.add_argument("--extra", action="append", default=[])
    args = parser.parse_args()

    req = Request(
        task=args.task,
        cfg=args.cfg,
        data_path=args.data_path,
        checkpoint=args.checkpoint,
        teacher_checkpoint=args.teacher_checkpoint,
        output=args.output,
        batch_size=args.batch_size,
        epochs=args.epochs,
        logits_dir=args.logits_dir,
        extra=args.extra,
    )
    print(build(req))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
