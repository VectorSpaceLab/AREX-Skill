#!/usr/bin/env python3
"""Portable DeblurGAN training wrapper.

This wrapper removes the source script's hardcoded local overrides, keeps the
user's chosen command-line flags, and adds a small smoke-friendly step cap.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from multiprocessing import freeze_support
from pathlib import Path


def parse_wrapper_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Portable DeblurGAN training wrapper. Remaining arguments are passed to the repository TrainOptions parser."
    )
    parser.add_argument("--repo-root", required=True, help="Path to the DeblurGAN checkout")
    parser.add_argument("--max-steps", type=int, default=0, help="Stop after this many optimization steps")
    parser.add_argument("--headless", action="store_true", help="Default display_id to 0 unless the caller overrides it")
    wrapper_args, remaining = parser.parse_known_args()
    return wrapper_args, remaining


def maybe_prepend_default_display_id(args: list[str]) -> list[str]:
    if any(flag in args for flag in ("--display_id", "--display-id")):
        return args
    return ["--display_id", "0", *args]


def main() -> int:
    freeze_support()
    wrapper_args, remaining = parse_wrapper_args()
    repo_root = Path(wrapper_args.repo_root).expanduser().resolve()
    if not repo_root.is_dir():
        raise SystemExit(f"repo root is not a directory: {repo_root}")

    sys.path.insert(0, str(repo_root))

    if wrapper_args.headless:
        remaining = maybe_prepend_default_display_id(remaining)

    sys.argv = [sys.argv[0], *remaining]

    from options.train_options import TrainOptions
    from data.data_loader import CreateDataLoader
    from models.models import create_model
    from util.visualizer import Visualizer
    from util.metrics import PSNR

    opt = TrainOptions().parse()

    # Ensure output directories exist before the visualizer writes its log.
    Path(opt.checkpoints_dir, opt.name).mkdir(parents=True, exist_ok=True)

    data_loader = CreateDataLoader(opt)
    model = create_model(opt)
    visualizer = Visualizer(opt)

    dataset = data_loader.load_data()
    dataset_size = len(data_loader)
    print(f"#training images = {dataset_size}")

    total_steps = 0
    for epoch in range(opt.epoch_count, opt.niter + opt.niter_decay + 1):
        epoch_start_time = time.time()
        epoch_iter = 0
        for i, data in enumerate(dataset):
            iter_start_time = time.time()
            total_steps += opt.batchSize
            epoch_iter += opt.batchSize
            model.set_input(data)
            model.optimize_parameters()

            if total_steps % opt.display_freq == 0:
                results = model.get_current_visuals()
                psnr_metric = PSNR(results["Restored_Train"], results["Sharp_Train"])
                print(f"PSNR on Train = {psnr_metric:f}")
                visualizer.display_current_results(results, epoch)

            if total_steps % opt.print_freq == 0:
                errors = model.get_current_errors()
                elapsed = (time.time() - iter_start_time) / max(opt.batchSize, 1)
                visualizer.print_current_errors(epoch, epoch_iter, errors, elapsed)
                if opt.display_id > 0:
                    visualizer.plot_current_errors(epoch, float(epoch_iter) / max(dataset_size, 1), opt, errors)

            if total_steps % opt.save_latest_freq == 0:
                print(f"saving the latest model (epoch {epoch}, total_steps {total_steps})")
                model.save("latest")

            if wrapper_args.max_steps and total_steps >= wrapper_args.max_steps:
                print(f"stopping after max_steps={wrapper_args.max_steps}")
                break

        if epoch % opt.save_epoch_freq == 0:
            print(f"saving the model at the end of epoch {epoch}, iters {total_steps}")
            model.save("latest")
            model.save(epoch)

        print(
            f"End of epoch {epoch} / {opt.niter + opt.niter_decay}\t"
            f"Time Taken: {int(time.time() - epoch_start_time)} sec"
        )

        if epoch > opt.niter:
            model.update_learning_rate()

        if wrapper_args.max_steps and total_steps >= wrapper_args.max_steps:
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
