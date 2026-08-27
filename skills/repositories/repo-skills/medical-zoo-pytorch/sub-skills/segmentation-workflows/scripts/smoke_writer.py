#!/usr/bin/env python3
"""Smoke test for the TensorBoard writer used by segmentation workflows.

The script writes only to a sandbox directory. By default that sandbox is a
fresh temporary directory.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import numpy as np


SEGMENTATION_DATASETS = {
    "iseg2017": 4,
    "iseg2019": 4,
    "mrbrains4": 4,
    "mrbrains9": 9,
    "brats2018": 4,
    "brats2019": 5,
    "brats2020": 4,
    "miccai2019": 7,
}


@contextmanager
def added_sys_path(path: str | None):
    if not path:
        yield
        return
    sys.path.insert(0, path)
    try:
        yield
    finally:
        if sys.path and sys.path[0] == path:
            sys.path.pop(0)


@contextmanager
def temporary_cwd(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke the MedicalZooPytorch TensorBoard writer in a sandbox directory.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--package-root",
        default=None,
        help="Optional local directory to prepend to sys.path before importing the writer.",
    )
    parser.add_argument(
        "--work-dir",
        default=None,
        help="Optional directory to use instead of a fresh temporary sandbox.",
    )
    parser.add_argument(
        "--dataset-name",
        choices=sorted(SEGMENTATION_DATASETS),
        default="iseg2017",
        help="Segmentation label set to exercise.",
    )
    parser.add_argument("--model", default="UNET3D", help="Model name used in the writer path.")
    parser.add_argument("--classes", type=int, default=None, help="Optional class-count override; must match the dataset label count.")
    parser.add_argument("--epochs", type=int, default=2, help="Number of synthetic epochs to log.")
    parser.add_argument("--train-steps", type=int, default=3, help="Synthetic train steps per epoch.")
    parser.add_argument("--val-steps", type=int, default=2, help="Synthetic validation steps per epoch.")
    parser.add_argument("--seed", type=int, default=7, help="Seed for the synthetic scores.")
    return parser.parse_args()


def detect_repo_root() -> str | None:
    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        if (parent / "lib" / "visual3D_temp" / "__init__.py").is_file():
            return str(parent)
    return None


def load_writer(package_root: str | None):
    candidate_roots = [package_root, detect_repo_root()]
    last_error: Exception | None = None
    for root in candidate_roots:
        if root is None:
            continue
        with added_sys_path(root):
            try:
                from lib.visual3D_temp import TensorboardWriter  # type: ignore
                return TensorboardWriter
            except Exception as exc:  # pragma: no cover - user-facing import diagnostic
                last_error = exc
    raise SystemExit(
        "Unable to import the TensorBoard writer. Make the MedicalZooPytorch package importable and ensure tensorboard is installed."
    ) from last_error


def build_args(model: str, dataset_name: str, classes: int) -> SimpleNamespace:
    return SimpleNamespace(
        log_dir="",
        save="checkpoints",
        model=model,
        dataset_name=dataset_name,
        classes=classes,
    )


def find_event_files(root: Path) -> list[Path]:
    return sorted(root.rglob("events.out.tfevents*"))


def main() -> None:
    args = parse_args()
    np.random.seed(args.seed)
    expected_classes = SEGMENTATION_DATASETS[args.dataset_name]
    classes = args.classes if args.classes is not None else expected_classes
    if classes != expected_classes:
        raise SystemExit(f"classes={classes} does not match the dataset label count {expected_classes} for {args.dataset_name}")

    if args.work_dir is None:
        sandbox_cm = tempfile.TemporaryDirectory(prefix="medical-zoo-writer-")
        sandbox_path = Path(sandbox_cm.name)
    else:
        sandbox_path = Path(args.work_dir).expanduser().resolve()
        sandbox_path.mkdir(parents=True, exist_ok=True)
        sandbox_cm = None

    try:
        with temporary_cwd(sandbox_path):
            TensorboardWriter = load_writer(args.package_root)
            writer_args = build_args(args.model, args.dataset_name, classes)
            writer = TensorboardWriter(writer_args)
            rng = np.random.default_rng(args.seed)

            for epoch in range(args.epochs):
                for step in range(args.train_steps):
                    loss = float(rng.random())
                    scores = rng.random(classes)
                    writer.update_scores(step, loss, scores, "train", epoch * 100 + step)
                writer.display_terminal(args.train_steps - 1, epoch, mode="train", summary=True)

                for step in range(args.val_steps):
                    loss = float(rng.random())
                    scores = rng.random(classes)
                    writer.update_scores(step, loss, scores, "val", epoch * 100 + step)
                writer.display_terminal(args.val_steps - 1, epoch, mode="val", summary=True)
                writer.write_end_of_epoch(epoch)
                writer.reset("train")
                writer.reset("val")

            writer.writer.flush()
            writer.writer.close()
            writer.csv_train.close()
            writer.csv_val.close()

            checkpoint_dir = sandbox_path / writer_args.save
            if not (checkpoint_dir / "train.csv").exists():
                raise AssertionError("train.csv was not created")
            if not (checkpoint_dir / "val.csv").exists():
                raise AssertionError("val.csv was not created")
            if not find_event_files(sandbox_path):
                raise AssertionError("no TensorBoard event file was created")

            print(f"writer smoke complete: {checkpoint_dir}")
    finally:
        if sandbox_cm is not None:
            sandbox_cm.cleanup()


if __name__ == "__main__":
    main()
