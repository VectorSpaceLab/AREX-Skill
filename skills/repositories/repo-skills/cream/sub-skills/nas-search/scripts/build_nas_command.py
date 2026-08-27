#!/usr/bin/env python3
"""Print safe launcher templates for the Cream monorepo NAS projects.

This helper does not run training or search. It only validates the requested
project family and prints a command template that future agents can adapt.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Request:
    project: str
    data_path: Optional[str]
    config: Optional[str]
    checkpoint: Optional[str]
    output: Optional[str]
    name: Optional[str]
    dataset: Optional[str]
    num_gpus: int
    min_param_limits: Optional[str]
    param_limits: Optional[str]
    extra: list[str]


def q(value: str) -> str:
    return f'"{value}"' if any(ch.isspace() for ch in value) else value


def require(req: Request, *fields: str) -> None:
    missing = [field for field in fields if getattr(req, field) in (None, "")]
    if missing:
        raise SystemExit(f"missing required field(s) for {req.project}: {', '.join(missing)}")


def join_extra(items: list[str]) -> str:
    return " ".join(items).strip()


def build(req: Request) -> str:
    extra = join_extra(req.extra)
    if req.project == "autoformer-train":
        require(req, "data_path", "config")
        return (
            f"python -m torch.distributed.launch --nproc_per_node={req.num_gpus} --use_env supernet_train.py "
            f"--data-path {q(req.data_path)} --gp --change_qk --relative_position --mode super "
            f"--dist-eval --cfg {q(req.config)} --epochs 500 --warmup-epochs 20 "
            f"--output {q(req.output or './outputs')} --batch-size 128 {extra}"
        )
    if req.project == "autoformer-search":
        require(req, "data_path", "config", "checkpoint", "min_param_limits", "param_limits")
        return (
            f"python -m torch.distributed.launch --nproc_per_node={req.num_gpus} --use_env evolution.py "
            f"--data-path {q(req.data_path)} --gp --change_qk --relative_position --dist-eval "
            f"--cfg {q(req.config)} --resume {q(req.checkpoint)} --min-param-limits {q(req.min_param_limits)} "
            f"--param-limits {q(req.param_limits)} --data-set EVO_IMNET {extra}"
        )
    if req.project == "autoformer-eval":
        require(req, "data_path", "config", "checkpoint")
        return (
            f"python -m torch.distributed.launch --nproc_per_node={req.num_gpus} --use_env supernet_train.py "
            f"--data-path {q(req.data_path)} --gp --change_qk --relative_position --mode retrain --dist-eval "
            f"--cfg {q(req.config)} --resume {q(req.checkpoint)} --eval {extra}"
        )
    if req.project == "autoformer-v2-eval":
        require(req, "data_path", "config", "checkpoint")
        return (
            f"python -m torch.distributed.launch --nproc_per_node={req.num_gpus} --use_env evaluation.py "
            f"--data-path {q(req.data_path)} --dist-eval --cfg {q(req.config)} --resume {q(req.checkpoint)} --eval {extra}"
        )
    if req.project in {"cream-train", "cream-retrain", "cream-test"}:
        require(req, "config")
        mode = req.project.split("-", 1)[1]
        return f"python tools/main.py {mode} {q(req.config)} {extra}".strip()
    if req.project == "cdarts-search":
        require(req, "name")
        return f"python search.py --name {q(req.name)} {extra}".strip()
    if req.project == "cdarts-retrain":
        require(req, "name")
        return f"python retrain.py --name {q(req.name)} {extra}".strip()
    if req.project == "cdarts-test":
        require(req, "name")
        return f"python test.py --name {q(req.name)} {extra}".strip()
    if req.project == "cdarts-benchmark201-search":
        require(req, "name")
        return f"python search.py --name {q(req.name)} {extra}".strip()
    raise SystemExit(f"unsupported project: {req.project}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Print safe NAS command templates")
    parser.add_argument(
        "--project",
        required=True,
        choices=[
            "autoformer-train",
            "autoformer-search",
            "autoformer-eval",
            "autoformer-v2-eval",
            "cream-train",
            "cream-retrain",
            "cream-test",
            "cdarts-search",
            "cdarts-retrain",
            "cdarts-test",
            "cdarts-benchmark201-search",
        ],
    )
    parser.add_argument("--data-path")
    parser.add_argument("--config")
    parser.add_argument("--checkpoint")
    parser.add_argument("--output")
    parser.add_argument("--name")
    parser.add_argument("--dataset")
    parser.add_argument("--num-gpus", type=int, default=8)
    parser.add_argument("--min-param-limits")
    parser.add_argument("--param-limits")
    parser.add_argument("--extra", action="append", default=[], help="Extra args appended verbatim")
    args = parser.parse_args()

    req = Request(
        project=args.project,
        data_path=args.data_path,
        config=args.config,
        checkpoint=args.checkpoint,
        output=args.output,
        name=args.name,
        dataset=args.dataset,
        num_gpus=args.num_gpus,
        min_param_limits=args.min_param_limits,
        param_limits=args.param_limits,
        extra=args.extra,
    )
    print(build(req))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
