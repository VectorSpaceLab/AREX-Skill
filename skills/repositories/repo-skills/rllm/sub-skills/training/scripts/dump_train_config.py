#!/usr/bin/env python3
"""Print the OmegaConf training config produced by rLLM's train CLI merger.

This is a safe config-inspection helper adapted from the repository's config-dump
idea. It does not create a trainer, contact providers, or start training.
"""

from __future__ import annotations

import argparse

from omegaconf import OmegaConf
from rllm.cli.train import build_train_config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-name", default="Qwen/Qwen3-8B")
    parser.add_argument("--group-size", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--lora-rank", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--val-freq", type=int, default=5)
    parser.add_argument("--save-freq", type=int, default=20)
    parser.add_argument("--project", default="rllm-train")
    parser.add_argument("--experiment", default="config-probe")
    parser.add_argument("--output", default=None, help="Checkpoint/output directory to inject into the config")
    parser.add_argument("--config", default=None, help="Optional YAML file to merge before CLI overrides")
    args = parser.parse_args()

    cfg = build_train_config(
        model_name=args.model_name,
        group_size=args.group_size,
        batch_size=args.batch_size,
        lr=args.lr,
        lora_rank=args.lora_rank,
        total_epochs=args.epochs,
        total_steps=args.max_steps,
        val_freq=args.val_freq,
        save_freq=args.save_freq,
        project=args.project,
        experiment=args.experiment,
        output_dir=args.output,
        config_file=args.config,
    )
    print(OmegaConf.to_yaml(cfg, resolve=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
