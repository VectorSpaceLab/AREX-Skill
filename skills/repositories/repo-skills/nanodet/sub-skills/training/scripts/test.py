#!/usr/bin/env python3
"""Run NanoDet validation or test-time evaluation from a config and checkpoint."""

from __future__ import annotations

import argparse
import datetime
import os
import warnings

import pytorch_lightning as pl
import torch

from nanodet.data.collate import naive_collate
from nanodet.data.dataset import build_dataset
from nanodet.evaluator import build_evaluator
from nanodet.trainer.task import TrainingTask
from nanodet.util import (
    NanoDetLightningLogger,
    cfg,
    convert_old_model,
    load_config,
    mkdir,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run NanoDet validation or test.")
    parser.add_argument("--task", type=str, default="val", help="task to run, test or val")
    parser.add_argument("--config", type=str, required=True, help="model config file path")
    parser.add_argument("--model", type=str, required=True, help="checkpoint file (.ckpt) path")
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Force the CPU branch even if the config requests GPUs.",
    )
    return parser.parse_args()


def main(args: argparse.Namespace) -> None:
    load_config(cfg, args.config)
    local_rank = -1
    torch.backends.cudnn.enabled = True
    torch.backends.cudnn.benchmark = True

    if args.cpu:
        cfg.defrost()
        cfg.device.gpu_ids = -1
        cfg.freeze()

    cfg.defrost()
    timestr = datetime.datetime.now().__format__("%Y%m%d%H%M%S")
    cfg.save_dir = os.path.join(cfg.save_dir, timestr)
    cfg.freeze()
    mkdir(local_rank, cfg.save_dir)
    logger = NanoDetLightningLogger(cfg.save_dir)

    assert args.task in ["val", "test"]
    cfg.defrost()
    cfg.update({"test_mode": args.task})
    cfg.freeze()

    logger.info("Setting up data...")
    val_dataset = build_dataset(cfg.data.val, args.task)
    val_dataloader = torch.utils.data.DataLoader(
        val_dataset,
        batch_size=cfg.device.batchsize_per_gpu,
        shuffle=False,
        num_workers=cfg.device.workers_per_gpu,
        pin_memory=True,
        collate_fn=naive_collate,
        drop_last=False,
    )
    evaluator = build_evaluator(cfg.evaluator, val_dataset)

    logger.info("Creating model...")
    task = TrainingTask(cfg, evaluator)

    ckpt = torch.load(args.model, map_location=lambda storage, loc: storage)
    if "pytorch-lightning_version" not in ckpt:
        warnings.warn(
            "Warning! Old .pth checkpoint is deprecated. "
            "Convert the checkpoint with scripts/convert_old_checkpoint.py"
        )
        ckpt = convert_old_model(ckpt)
    task.load_state_dict(ckpt["state_dict"])

    if cfg.device.gpu_ids == -1:
        logger.info("Using CPU evaluation")
        accelerator, devices = "cpu", None
    else:
        accelerator, devices = "gpu", cfg.device.gpu_ids

    trainer = pl.Trainer(
        default_root_dir=cfg.save_dir,
        accelerator=accelerator,
        devices=devices,
        log_every_n_steps=cfg.log.interval,
        num_sanity_val_steps=0,
        logger=logger,
    )
    logger.info("Starting testing...")
    trainer.test(task, val_dataloader)


if __name__ == "__main__":
    main(parse_args())
