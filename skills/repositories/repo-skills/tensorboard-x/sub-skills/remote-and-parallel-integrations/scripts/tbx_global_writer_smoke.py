#!/usr/bin/env python3
"""Safe smoke for module-global and multiprocessing writer patterns."""

from __future__ import annotations

import argparse
import multiprocessing as mp
import tempfile
import time
from pathlib import Path

import numpy as np


def load_global_writer():
    """Load tensorboardX lazily so --help works before installation checks."""
    from tensorboardX import GlobalSummaryWriter
    from tensorboardX import global_writer as global_writer_module

    return GlobalSummaryWriter, global_writer_module


def install_global_writer(writer) -> None:
    """Install the writer into the package module singleton for this smoke."""
    _, global_writer_module = load_global_writer()
    global_writer_module._writer = writer


def get_writer():
    """Return the shared process-local global writer."""
    GlobalSummaryWriter, _ = load_global_writer()
    return GlobalSummaryWriter.getSummaryWriter()


def log_module_one() -> None:
    writer = get_writer()
    writer.add_text("global/module_one", "hello from module one")
    for step in range(3):
        writer.add_scalar("global/shared", step)


def log_module_two() -> None:
    writer = get_writer()
    writer.add_text("global/module_two", "hello from module two")
    for step in range(3):
        writer.add_scalar("global/shared", step + 100)


def worker(name: str, steps: int, pause: float) -> None:
    writer = get_writer()
    for step in range(steps):
        writer.add_scalar(f"global/worker/{name}", step)
        writer.add_text(f"global/worker/{name}", f"{name}:{step}")
        if pause:
            time.sleep(pause)


def run_multiprocess(workers: int, steps: int, pause: float) -> None:
    if "fork" not in mp.get_all_start_methods():
        print("fork start method is unavailable; skipping multiprocessing smoke.")
        return

    ctx = mp.get_context("fork")
    processes = []
    for index in range(workers):
        proc = ctx.Process(target=worker, args=(f"w{index}", steps, pause))
        proc.start()
        processes.append(proc)

    for proc in processes:
        proc.join()
        if proc.exitcode != 0:
            raise SystemExit(f"worker exited with code {proc.exitcode}")


def run_smoke(logdir: Path, multiprocess: bool, workers: int, steps: int, pause: float) -> None:
    GlobalSummaryWriter, _ = load_global_writer()
    writer = GlobalSummaryWriter(logdir=str(logdir), coalesce_process=True)
    install_global_writer(writer)
    try:
        log_module_one()
        log_module_two()

        image = np.zeros((3, 8, 8), dtype=np.float32)
        image[0] = np.linspace(0.0, 1.0, 64, dtype=np.float32).reshape(8, 8)
        writer.add_image("global/image", image)

        if multiprocess:
            run_multiprocess(workers=workers, steps=steps, pause=pause)
    finally:
        writer.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke test shared GlobalSummaryWriter usage across helper functions and worker processes."
    )
    parser.add_argument(
        "--logdir",
        type=Path,
        default=None,
        help="Output directory for the smoke run. A temporary directory is created when omitted.",
    )
    parser.add_argument(
        "--multiprocess",
        action="store_true",
        help="Also exercise a fork-based worker pool smoke when available.",
    )
    parser.add_argument("--workers", type=int, default=2, help="Number of worker processes to start.")
    parser.add_argument("--steps", type=int, default=3, help="Scalar/text steps per worker.")
    parser.add_argument("--pause", type=float, default=0.01, help="Sleep time between worker writes.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logdir = args.logdir or Path(tempfile.mkdtemp(prefix="tbx-global-writer-"))
    logdir.mkdir(parents=True, exist_ok=True)
    run_smoke(logdir=logdir, multiprocess=args.multiprocess, workers=args.workers, steps=args.steps, pause=args.pause)
    print(f"GlobalSummaryWriter smoke completed in {logdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
