#!/usr/bin/env python3
"""Print safe TinyCLIP launcher templates.

The helper never downloads checkpoints or launches training. It prints command
strings for zero-shot evaluation, inference, and pretraining-stage planning.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Request:
    task: str
    imagenet_val: Optional[str]
    resume: Optional[str]
    model: str
    gpus: int
    data_path: Optional[str]
    stage: Optional[str]
    extra: list[str]


def q(value: str) -> str:
    return f'"{value}"' if any(ch.isspace() for ch in value) else value


def build(req: Request) -> str:
    extra = " ".join(req.extra).strip()
    if req.task == "zero-shot-eval":
        if not req.imagenet_val or not req.resume:
            raise SystemExit("zero-shot-eval requires --imagenet-val and --resume")
        return (
            f"python -m torch.distributed.launch --use_env --nproc_per_node {req.gpus} src/training/main_for_test.py "
            f"--imagenet-val {q(req.imagenet_val)} --model {q(req.model)} --eval --resume {q(req.resume)} {extra}".strip()
        )
    if req.task == "zero-shot-auto":
        if not req.imagenet_val or not req.resume:
            raise SystemExit("zero-shot-auto requires --imagenet-val and --resume")
        return (
            f"python -m torch.distributed.launch --use_env --nproc_per_node {req.gpus} src/training/main_for_test.py "
            f"--imagenet-val {q(req.imagenet_val)} --model ViT-B-32 --prune-image --prune-text --eval --resume {q(req.resume)} {extra}"
            .strip()
        )
    if req.task == "inference":
        if not req.resume:
            raise SystemExit("inference requires --resume")
        return (
            f"python inference.py --resume {q(req.resume)} --model {q(req.model)} {extra}".strip()
        )
    if req.task == "pretrain-stage":
        if not req.data_path or not req.stage:
            raise SystemExit("pretrain-stage requires --data-path and --stage")
        return (
            f"python -m torch.distributed.launch --use_env --nproc_per_node {req.gpus} src/training/main.py "
            f"--data-path {q(req.data_path)} --stage {q(req.stage)} --model {q(req.model)} {extra}".strip()
        )
    raise SystemExit(f"unsupported task: {req.task}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Print safe TinyCLIP command templates")
    parser.add_argument(
        "--task",
        required=True,
        choices=["zero-shot-eval", "zero-shot-auto", "inference", "pretrain-stage"],
    )
    parser.add_argument("--imagenet-val")
    parser.add_argument("--resume")
    parser.add_argument("--model", default="TinyCLIP-ViT-39M-16-Text-19M")
    parser.add_argument("--gpus", type=int, default=8)
    parser.add_argument("--data-path")
    parser.add_argument("--stage")
    parser.add_argument("--extra", action="append", default=[])
    args = parser.parse_args()

    req = Request(
        task=args.task,
        imagenet_val=args.imagenet_val,
        resume=args.resume,
        model=args.model,
        gpus=args.gpus,
        data_path=args.data_path,
        stage=args.stage,
        extra=args.extra,
    )
    print(build(req))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
