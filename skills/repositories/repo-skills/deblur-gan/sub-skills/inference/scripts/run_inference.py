#!/usr/bin/env python3
"""Portable DeblurGAN inference wrapper.

This wrapper keeps the repository's single-image inference flow but removes the
brittle external `ssim` import path and makes headless CPU-friendly execution
straightforward.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def parse_wrapper_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Portable DeblurGAN inference wrapper. Remaining arguments are passed to the repository TestOptions parser."
    )
    parser.add_argument("--repo-root", required=True, help="Path to the DeblurGAN checkout")
    parser.add_argument("--headless", action="store_true", help="Default display_id to 0 unless overridden")
    wrapper_args, remaining = parser.parse_known_args()
    return wrapper_args, remaining


def maybe_prepend_default_display_id(args: list[str]) -> list[str]:
    if any(flag in args for flag in ("--display_id", "--display-id")):
        return args
    return ["--display_id", "0", *args]


def main() -> int:
    wrapper_args, remaining = parse_wrapper_args()
    repo_root = Path(wrapper_args.repo_root).expanduser().resolve()
    if not repo_root.is_dir():
        raise SystemExit(f"repo root is not a directory: {repo_root}")

    sys.path.insert(0, str(repo_root))

    if wrapper_args.headless:
        remaining = maybe_prepend_default_display_id(remaining)

    sys.argv = [sys.argv[0], *remaining]

    from options.test_options import TestOptions
    from data.data_loader import CreateDataLoader
    from models.models import create_model
    from util.visualizer import Visualizer
    from util import html

    opt = TestOptions().parse()
    opt.nThreads = 1
    opt.batchSize = 1
    opt.serial_batches = True
    opt.no_flip = True
    if wrapper_args.headless:
        opt.display_id = 0

    # The visualizer expects its checkpoint log directory to exist.
    Path(opt.checkpoints_dir, opt.name).mkdir(parents=True, exist_ok=True)

    data_loader = CreateDataLoader(opt)
    dataset = data_loader.load_data()
    model = create_model(opt)
    visualizer = Visualizer(opt)

    web_dir = os.path.join(opt.results_dir, opt.name, f"{opt.phase}_{opt.which_epoch}")
    webpage = html.HTML(web_dir, f"Experiment = {opt.name}, Phase = {opt.phase}, Epoch = {opt.which_epoch}")

    for i, data in enumerate(dataset):
        if i >= opt.how_many:
            break
        model.set_input(data)
        model.test()
        visuals = model.get_current_visuals()
        img_path = model.get_image_paths()
        print(f"process image... {img_path}")
        visualizer.save_images(webpage, visuals, img_path)

    webpage.save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
