#!/usr/bin/env python3
"""Print safe command templates for iRPE workflows.

The helper only prints launcher strings for DeiT and DETR variants; it does
not execute training or evaluation.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Request:
    task: str
    imagenet_root: Optional[str]
    coco_root: Optional[str]
    checkpoint: Optional[str]
    enc_rpe2d: Optional[str]
    model: str
    gpus: int
    extra: list[str]


def q(value: str) -> str:
    return f'"{value}"' if any(ch.isspace() for ch in value) else value


def build(req: Request) -> str:
    extra = " ".join(req.extra).strip()
    if req.task == "deit-train":
        if not req.imagenet_root:
            raise SystemExit("deit-train requires --imagenet-root")
        return (
            f"python -m torch.distributed.launch --nproc_per_node={req.gpus} --use_env main.py --model {q(req.model)} "
            f"--data-path {q(req.imagenet_root)} --epochs 300 {extra}".strip()
        )
    if req.task == "deit-eval":
        if not req.imagenet_root or not req.checkpoint:
            raise SystemExit("deit-eval requires --imagenet-root and --checkpoint")
        return (
            f"python -m torch.distributed.launch --nproc_per_node={req.gpus} --use_env main.py --model {q(req.model)} "
            f"--data-path {q(req.imagenet_root)} --eval --resume {q(req.checkpoint)} {extra}".strip()
        )
    if req.task == "detr-train":
        if not req.coco_root:
            raise SystemExit("detr-train requires --coco-root")
        enc = req.enc_rpe2d or "<rpe-choice>"
        return (
            f"python -m torch.distributed.launch --nproc_per_node={req.gpus} main.py --enc_rpe2d {q(enc)} --coco_path {q(req.coco_root)} "
            f"--output_dir <output-dir> {extra}".strip()
        )
    if req.task == "detr-eval":
        if not req.coco_root or not req.checkpoint:
            raise SystemExit("detr-eval requires --coco-root and --checkpoint")
        enc = req.enc_rpe2d or "<rpe-choice>"
        return (
            f"python -m torch.distributed.launch --nproc_per_node={req.gpus} main.py --enc_rpe2d {q(enc)} --coco_path {q(req.coco_root)} "
            f"--resume {q(req.checkpoint)} --eval {extra}".strip()
        )
    raise SystemExit(f"unsupported task: {req.task}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Print safe iRPE command templates")
    parser.add_argument("--task", required=True, choices=["deit-train", "deit-eval", "detr-train", "detr-eval"])
    parser.add_argument("--imagenet-root")
    parser.add_argument("--coco-root")
    parser.add_argument("--checkpoint")
    parser.add_argument("--enc-rpe2d")
    parser.add_argument("--model", default="deit_tiny_patch16_224_ctx_product_50_shared_k")
    parser.add_argument("--gpus", type=int, default=8)
    parser.add_argument("--extra", action="append", default=[])
    args = parser.parse_args()

    req = Request(
        task=args.task,
        imagenet_root=args.imagenet_root,
        coco_root=args.coco_root,
        checkpoint=args.checkpoint,
        enc_rpe2d=args.enc_rpe2d,
        model=args.model,
        gpus=args.gpus,
        extra=args.extra,
    )
    print(build(req))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
