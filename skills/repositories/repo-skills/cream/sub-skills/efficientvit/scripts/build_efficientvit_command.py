#!/usr/bin/env python3
"""Print safe command templates for EfficientViT workflows.

This helper never downloads checkpoints or launches distributed jobs.
It just prints launcher strings for classification and downstream tasks.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Request:
    task: str
    model: str
    data_path: Optional[str]
    checkpoint: Optional[str]
    config: Optional[str]
    pretrained_backbone: Optional[str]
    device: str
    batch_size: int
    gpus: int
    extra: list[str]


def q(value: str) -> str:
    return f'"{value}"' if any(ch.isspace() for ch in value) else value


def build(req: Request) -> str:
    extra = " ".join(req.extra).strip()
    if req.task == "classify-eval":
        if not req.data_path or not req.checkpoint:
            raise SystemExit("classify-eval requires --data-path and --checkpoint")
        return (
            f"python main.py --eval --model {q(req.model)} --resume {q(req.checkpoint)} "
            f"--data-path {q(req.data_path)} {extra}".strip()
        )
    if req.task == "classify-train":
        if not req.data_path:
            raise SystemExit("classify-train requires --data-path")
        return (
            f"python -m torch.distributed.launch --nproc_per_node={req.gpus} --master_port 12345 --use_env main.py "
            f"--model {q(req.model)} --data-path {q(req.data_path)} --dist-eval {extra}".strip()
        )
    if req.task == "speed-test":
        return (
            f"python scripts/benchmark_efficientvit.py --model {q(req.model)} --device {q(req.device)} "
            f"--batch-size {req.batch_size} {extra}".strip()
        )
    if req.task == "downstream-test":
        if not req.config or not req.checkpoint:
            raise SystemExit("downstream-test requires --config and --checkpoint")
        metrics = "bbox segm" if "mask" in req.config else "bbox"
        return f"bash ./dist_test.sh {q(req.config)} {q(req.checkpoint)} {req.gpus} --eval {metrics} {extra}".strip()
    if req.task == "downstream-train":
        if not req.config or not req.pretrained_backbone:
            raise SystemExit("downstream-train requires --config and --pretrained-backbone")
        return (
            f"bash ./dist_train.sh {q(req.config)} {req.gpus} --cfg-options model.backbone.pretrained={q(req.pretrained_backbone)} {extra}"
            .strip()
        )
    raise SystemExit(f"unsupported task: {req.task}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Print safe EfficientViT commands")
    parser.add_argument(
        "--task",
        required=True,
        choices=["classify-eval", "classify-train", "speed-test", "downstream-test", "downstream-train"],
    )
    parser.add_argument("--model", default="EfficientViT_M4")
    parser.add_argument("--data-path")
    parser.add_argument("--checkpoint")
    parser.add_argument("--config")
    parser.add_argument("--pretrained-backbone")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--gpus", type=int, default=8)
    parser.add_argument("--extra", action="append", default=[])
    args = parser.parse_args()

    req = Request(
        task=args.task,
        model=args.model,
        data_path=args.data_path,
        checkpoint=args.checkpoint,
        config=args.config,
        pretrained_backbone=args.pretrained_backbone,
        device=args.device,
        batch_size=args.batch_size,
        gpus=args.gpus,
        extra=args.extra,
    )
    print(build(req))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
