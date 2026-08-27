#!/usr/bin/env python3
"""Self-contained DAMO-YOLO evaluation entry point for generated skills.

This adapts the repository's eval launcher so future agents can run it from an
installed `damo` package without importing repo-local `tools/eval.py`.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import torch
from loguru import logger

from damo.apis.detector_inference import inference
from damo.base_models.core.ops import RepConv
from damo.config.base import parse_config
from damo.dataset import build_dataloader, build_dataset
from damo.detectors.detector import build_ddp_model, build_local_model
from damo.utils import fuse_model, get_model_info, setup_logger, synchronize


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("DAMO-YOLO evaluation entry point")
    parser.add_argument("-f", "--config_file", required=True, help="DAMO-YOLO Python config file")
    parser.add_argument("-c", "--ckpt", required=True, help="PyTorch checkpoint to evaluate")
    parser.add_argument("--workdir", help="Directory used to resolve relative paths inside the config")
    parser.add_argument("--local_rank", "--local-rank", dest="local_rank", type=int, default=None)
    parser.add_argument("--conf", default=None, type=float, help="Parsed for source compatibility; edit config for reliable thresholds")
    parser.add_argument("--nms", default=None, type=float, help="Parsed for source compatibility; edit config for reliable thresholds")
    parser.add_argument("--tsize", default=None, type=int, help="Parsed for source compatibility; edit config for reliable image size")
    parser.add_argument("--seed", default=None, type=int, help="Parsed for source compatibility; this entry point does not reseed")
    parser.add_argument("--fuse", action="store_true", help="Fuse conv and bn for evaluation")
    parser.add_argument("--test", action="store_true", help="Parsed for source compatibility; edit dataset.val_ann for test-dev")
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


def mkdir(path: str) -> None:
    if path and not os.path.exists(path):
        os.makedirs(path)


def main() -> int:
    args = make_parser().parse_args()
    _prepare_workdir(args.workdir)
    local_rank = _local_rank(args.local_rank)

    if not torch.cuda.is_available():
        raise SystemExit("ERROR: DAMO-YOLO evaluation requires CUDA because the eval code sets CUDA devices and uses NCCL.")
    if not torch.distributed.is_nccl_available():
        raise SystemExit("ERROR: torch.distributed NCCL backend is not available in this environment.")

    torch.cuda.set_device(local_rank)
    torch.distributed.init_process_group(backend="nccl", init_method="env://")
    synchronize()

    config = parse_config(args.config_file)
    config.merge(args.opts)

    device = "cuda"
    save_dir = os.path.join(config.miscs.output_dir, config.miscs.exp_name)
    if local_rank == 0:
        os.makedirs(save_dir, exist_ok=True)

    setup_logger(save_dir, distributed_rank=local_rank, mode="w")
    logger.info("DAMO-YOLO eval args: {}", args)

    model = build_local_model(config, device)
    model.head.nms = True
    model.cuda(local_rank)
    model.eval()

    loc = f"cuda:{local_rank}"
    logger.info("loading checkpoint from {}", args.ckpt)
    ckpt = torch.load(args.ckpt, map_location=loc)
    state_dict = ckpt.get("model", ckpt)
    new_state_dict = {k.replace("module", ""): v for k, v in state_dict.items()}
    model.load_state_dict(new_state_dict, strict=False)
    logger.info("loaded checkpoint done")

    for layer in model.modules():
        if isinstance(layer, RepConv):
            layer.switch_to_deploy()

    infer_shape = sum(config.test.augment.transform.image_max_range) // 2
    logger.info("Model Summary: {}", get_model_info(model, (infer_shape, infer_shape)))

    model = build_ddp_model(model, local_rank=local_rank)
    if args.fuse:
        logger.info("Fusing model")
        model = fuse_model(model)

    output_folders = [None] * len(config.dataset.val_ann)
    if local_rank == 0 and config.miscs.output_dir:
        for idx, dataset_name in enumerate(config.dataset.val_ann):
            output_folder = os.path.join(config.miscs.output_dir, "inference", dataset_name)
            mkdir(output_folder)
            output_folders[idx] = output_folder

    val_dataset = build_dataset(config, config.dataset.val_ann, is_train=False)
    val_loader = build_dataloader(
        val_dataset,
        config.test.augment,
        batch_size=config.test.batch_size,
        num_workers=config.miscs.num_workers,
        is_train=False,
        size_div=32,
    )

    for output_folder, dataset_name, data_loader_val in zip(output_folders, config.dataset.val_ann, val_loader):
        inference(
            model,
            data_loader_val,
            dataset_name,
            iou_types=("bbox",),
            box_only=False,
            device=device,
            output_folder=output_folder,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
