#!/usr/bin/env python3
"""Self-contained DAMO-YOLO training entry point for generated skills.

This adapts the repository's training launcher so future agents can run it from
an installed `damo` package without importing repo-local `tools/train.py`.
Config files and dataset paths are still user inputs.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import torch
from loguru import logger

from damo.apis import Trainer
from damo.config.base import parse_config
from damo.utils import synchronize


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("DAMO-YOLO training entry point")
    parser.add_argument("-f", "--config_file", required=True, help="DAMO-YOLO Python config file")
    parser.add_argument("--workdir", help="Directory used to resolve relative paths inside the config")
    parser.add_argument("--local_rank", "--local-rank", dest="local_rank", type=int, default=None)
    parser.add_argument("--tea_config", "--tea-config", dest="tea_config", default=None)
    parser.add_argument("--tea_ckpt", "--tea-ckpt", dest="tea_ckpt", default=None)
    parser.add_argument(
        "opts",
        help="Top-level config overrides accepted by Config.merge(); prefer config-file edits for nested keys",
        nargs=argparse.REMAINDER,
    )
    return parser


def _local_rank(value: int | None) -> int:
    if value is not None:
        return value
    return int(os.environ.get("LOCAL_RANK", os.environ.get("RANK", "0")))


def _prepare_workdir(workdir: str | None) -> None:
    if not workdir:
        return
    path = Path(workdir).resolve()
    if not path.is_dir():
        raise SystemExit(f"ERROR: --workdir does not exist or is not a directory: {path}")
    os.chdir(path)


def main() -> int:
    args = make_parser().parse_args()
    _prepare_workdir(args.workdir)
    local_rank = _local_rank(args.local_rank)

    if not torch.cuda.is_available():
        raise SystemExit("ERROR: DAMO-YOLO training requires CUDA because the training code sets CUDA devices and uses NCCL.")
    if not torch.distributed.is_nccl_available():
        raise SystemExit("ERROR: torch.distributed NCCL backend is not available in this environment.")

    torch.cuda.set_device(local_rank)
    torch.distributed.init_process_group(backend="nccl", init_method="env://")
    synchronize()

    if args.tea_config is not None:
        if args.tea_ckpt is None:
            raise SystemExit("ERROR: --tea_config requires --tea_ckpt for DAMO-YOLO distillation.")
        tea_config = parse_config(args.tea_config)
    else:
        tea_config = None

    config = parse_config(args.config_file)
    config.merge(args.opts)

    logger.info("DAMO-YOLO train args: {}", args)
    trainer = Trainer(config, args, tea_config)
    trainer.train(local_rank)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
