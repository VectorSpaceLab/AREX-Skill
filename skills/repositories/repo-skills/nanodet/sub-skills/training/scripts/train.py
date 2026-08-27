#!/usr/bin/env python3
"""Run NanoDet training from a YAML config.

This is a skill-owned wrapper adapted from the repository's training CLI.
"""

from __future__ import annotations

import argparse
import os
import warnings

import pytorch_lightning as pl
import torch
from pytorch_lightning.callbacks import TQDMProgressBar

from nanodet.data.collate import naive_collate
from nanodet.data.dataset import build_dataset
from nanodet.evaluator import build_evaluator
from nanodet.trainer.task import TrainingTask
from nanodet.util import (
    NanoDetLightningLogger,
    cfg,
    convert_old_model,
    env_utils,
    load_config,
    load_model_weight,
    mkdir,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run NanoDet training from a config.")
    parser.add_argument("config", help="Train config file path")
    parser.add_argument(
        "--local_rank",
        default=-1,
        type=int,
        help="Node rank for distributed training",
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Force the CPU branch even if the config requests GPUs.",
    )
    return parser.parse_args()


def main(args: argparse.Namespace) -> None:
    load_config(cfg, args.config)
    if cfg.model.arch.head.num_classes != len(cfg.class_names):
        raise ValueError(
            "cfg.model.arch.head.num_classes must equal len(cfg.class_names), "
            f"but got {cfg.model.arch.head.num_classes} and {len(cfg.class_names)}"
        )

    if args.cpu:
        cfg.defrost()
        cfg.device.gpu_ids = -1
        cfg.device.precision = 32
        cfg.freeze()

    local_rank = int(args.local_rank)
    torch.backends.cudnn.enabled = True
    torch.backends.cudnn.benchmark = True
    mkdir(local_rank, cfg.save_dir)

    logger = NanoDetLightningLogger(cfg.save_dir)
    logger.dump_cfg(cfg)

    if args.seed is not None:
        logger.info(f"Set random seed to {args.seed}")
        pl.seed_everything(args.seed)

    logger.info("Setting up data...")
    train_dataset = build_dataset(cfg.data.train, "train")
    val_dataset = build_dataset(cfg.data.val, "test")
    evaluator = build_evaluator(cfg.evaluator, val_dataset)

    train_dataloader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=cfg.device.batchsize_per_gpu,
        shuffle=True,
        num_workers=cfg.device.workers_per_gpu,
        pin_memory=True,
        collate_fn=naive_collate,
        drop_last=True,
    )
    val_dataloader = torch.utils.data.DataLoader(
        val_dataset,
        batch_size=cfg.device.batchsize_per_gpu,
        shuffle=False,
        num_workers=cfg.device.workers_per_gpu,
        pin_memory=True,
        collate_fn=naive_collate,
        drop_last=False,
    )

    logger.info("Creating model...")
    task = TrainingTask(cfg, evaluator)

    if "load_model" in cfg.schedule:
        ckpt = torch.load(cfg.schedule.load_model, map_location=lambda storage, loc: storage)
        if "pytorch-lightning_version" not in ckpt:
            warnings.warn(
                "Warning! Old .pth checkpoint is deprecated. "
                "Convert the checkpoint with scripts/convert_old_checkpoint.py"
            )
            ckpt = convert_old_model(ckpt)
        load_model_weight(task.model, ckpt, logger)
        logger.info(f"Loaded model weight from {cfg.schedule.load_model}")

    model_resume_path = (
        os.path.join(cfg.save_dir, "model_last.ckpt") if "resume" in cfg.schedule else None
    )
    if cfg.device.gpu_ids == -1:
        logger.info("Using CPU training")
        accelerator, devices, strategy, precision = (
            "cpu",
            None,
            None,
            cfg.device.precision,
        )
    else:
        accelerator, devices, strategy, precision = (
            "gpu",
            cfg.device.gpu_ids,
            None,
            cfg.device.precision,
        )

    if devices and len(devices) > 1:
        strategy = "ddp"
        env_utils.set_multi_processing(distributed=True)

    trainer = pl.Trainer(
        default_root_dir=cfg.save_dir,
        max_epochs=cfg.schedule.total_epochs,
        check_val_every_n_epoch=cfg.schedule.val_intervals,
        accelerator=accelerator,
        devices=devices,
        log_every_n_steps=cfg.log.interval,
        num_sanity_val_steps=0,
        callbacks=[TQDMProgressBar(refresh_rate=0)],
        logger=logger,
        benchmark=cfg.get("cudnn_benchmark", True),
        gradient_clip_val=cfg.get("grad_clip", 0.0),
        strategy=strategy,
        precision=precision,
    )

    trainer.fit(task, train_dataloader, val_dataloader, ckpt_path=model_resume_path)


if __name__ == "__main__":
    main(parse_args())
