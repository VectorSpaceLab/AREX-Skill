#!/usr/bin/env python3
"""Train or smoke-test LPIPS on BAPPS-style 2AFC data.

This helper avoids the old HTML/visdom stack and creates checkpoint
subdirectories automatically. It uses the stock `lpips.Trainer` internals for
training so the loss and checkpoint naming match the package behavior.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SKILL_ROOT = Path(__file__).resolve().parents[3]
ROOT_SCRIPTS = SKILL_ROOT / "scripts"
if str(ROOT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ROOT_SCRIPTS))

import torch
from tqdm import tqdm

from bapps_common import load_bapps_dataset, make_loader
from lpips import Trainer


DEFAULT_TRAIN_SPLITS = ["train/traditional", "train/cnn", "train/mix"]
DEFAULT_VAL_SPLITS = ["val/traditional", "val/cnn"]


def build_trainer(args):
    use_gpu = bool(args.use_gpu and torch.cuda.is_available())
    if args.use_gpu and not use_gpu:
        print("[lpips] CUDA requested but unavailable; using CPU instead.")

    trainer = Trainer()
    trainer.initialize(
        model=args.model,
        net=args.net,
        colorspace=args.colorspace,
        pnet_rand=args.from_scratch,
        pnet_tune=args.train_trunk,
        model_path=str(args.model_path) if args.model_path else None,
        use_gpu=use_gpu,
        printNet=False,
        spatial=False,
        is_train=True,
        lr=args.lr,
        beta1=args.beta1,
        version=args.version,
        gpu_ids=args.gpu_ids,
    )
    return trainer, use_gpu


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--dataset_root", type=Path, default=Path("dataset"), help="Root containing the BAPPS branches.")
    parser.add_argument("--datasets", nargs="+", default=None, help="Train splits such as train/traditional train/cnn train/mix or a tiny smoke split.")
    parser.add_argument("--model", choices=["lpips", "baseline", "l2", "ssim"], default="lpips", help="Metric family to train.")
    parser.add_argument("--net", choices=["squeeze", "alex", "vgg"], default="alex", help="Backbone used by the learned metric.")
    parser.add_argument("--colorspace", choices=["Lab", "RGB"], default="Lab", help="Colorspace used by L2 and SSIM-style variants.")
    parser.add_argument("--batch_size", type=int, default=1, help="Training batch size.")
    parser.add_argument("--num_workers", type=int, default=0, help="Data-loader worker count.")
    parser.add_argument("--load_size", type=int, default=64, help="Resize shorter side to this value before training.")
    parser.add_argument("--epochs", type=int, default=1, help="Number of epochs to iterate over the provided splits.")
    parser.add_argument("--max_steps", type=int, default=1, help="Maximum optimizer steps to run; set to 0 for no step limit.")
    parser.add_argument("--save_every", type=int, default=1, help="Save a latest checkpoint every N optimizer steps; 0 disables step-based saves.")
    parser.add_argument("--print_every", type=int, default=1, help="Print training metrics every N optimizer steps; 0 disables step-based prints.")
    parser.add_argument("--checkpoints_dir", type=Path, default=Path("checkpoints"), help="Checkpoint parent directory.")
    parser.add_argument("--name", default="tmp", help="Checkpoint subdirectory name.")
    parser.add_argument("--use_gpu", action="store_true", help="Use CUDA when available.")
    parser.add_argument("--gpu_ids", type=int, nargs="+", default=[0], help="CUDA device ids used by the trainer.")
    parser.add_argument("--version", default="0.1", help="LPIPS weight version.")
    parser.add_argument("--model_path", type=Path, default=None, help="Optional custom LPIPS weight file.")
    parser.add_argument("--from_scratch", action="store_true", help="Use random trunk weights.")
    parser.add_argument("--train_trunk", action="store_true", help="Allow trunk tuning.")
    parser.add_argument("--lr", type=float, default=1e-4, help="Adam learning rate.")
    parser.add_argument("--beta1", type=float, default=0.5, help="Adam beta1 parameter.")
    args = parser.parse_args(argv)

    if args.datasets is None:
        args.datasets = DEFAULT_TRAIN_SPLITS

    trainer, use_gpu = build_trainer(args)
    dataset = load_bapps_dataset(args.dataset_root, "2afc", args.datasets, load_size=args.load_size)
    loader = make_loader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers)

    out_dir = args.checkpoints_dir / args.name
    out_dir.mkdir(parents=True, exist_ok=True)
    log_file = out_dir / "train_log.txt"
    log_file.write_text("", encoding="utf-8")

    step = 0
    for epoch in range(1, args.epochs + 1):
        epoch_steps = 0
        for batch in tqdm(loader, desc=f"epoch {epoch}"):
            trainer.set_input(batch)
            trainer.optimize_parameters()
            step += 1
            epoch_steps += 1

            if args.print_every > 0 and step % args.print_every == 0:
                errors = trainer.get_current_errors()
                message = f"epoch={epoch} step={step} loss_total={errors['loss_total']:.6f} acc_r={errors['acc_r']:.6f}"
                print(message)
                with log_file.open("a", encoding="utf-8") as handle:
                    handle.write(message + "\n")

            if args.save_every > 0 and step % args.save_every == 0:
                trainer.save(str(out_dir), "latest")

            if args.max_steps > 0 and step >= args.max_steps:
                break

        trainer.save(str(out_dir), "latest")
        trainer.save(str(out_dir), epoch)
        print(f"finished epoch {epoch} with {epoch_steps} step(s)")

        if args.max_steps > 0 and step >= args.max_steps:
            break

    print(f"saved checkpoints under {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
