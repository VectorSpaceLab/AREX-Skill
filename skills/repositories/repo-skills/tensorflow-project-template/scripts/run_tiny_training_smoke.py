#!/usr/bin/env python3
"""Run a bounded one-step TensorFlow Project Template smoke test.

This helper imports a target template checkout, constructs the example model,
data generator, logger, and trainer, then runs one training epoch with one
iteration in a temporary work directory. It requires TensorFlow 1.x-compatible
top-level APIs.

Example:
    python scripts/run_tiny_training_smoke.py --repo-root /path/to/template-copy --work-dir /path/to/safe-smoke-workdir
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny TensorFlow 1.x training smoke for TensorFlow Project Template.")
    parser.add_argument("--repo-root", default=".", help="Path to the template checkout or copied project to import.")
    parser.add_argument("--work-dir", default=None, help="Directory for temporary summaries/checkpoints. Created if needed; replaced when --clean is set.")
    parser.add_argument("--clean", action="store_true", help="Delete an existing --work-dir before running.")
    parser.add_argument("--allow-gpu", action="store_true", help="Do not hide CUDA devices before importing TensorFlow.")
    return parser.parse_args()


def require_files(repo_root: Path, rels: Iterable[str]) -> None:
    missing = [rel for rel in rels if not (repo_root / rel).is_file()]
    if missing:
        raise SystemExit(f"Target project is missing expected files: {missing}")


def import_tensorflow_1x():
    try:
        import tensorflow as tf  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on caller env
        raise SystemExit(f"Could not import tensorflow: {exc}")

    required = ["Session", "placeholder", "variable_scope", "assign", "train", "summary"]
    missing = [name for name in required if not hasattr(tf, name)]
    if missing:
        raise SystemExit(
            "TensorFlow import succeeded but required TF1 top-level symbols are missing: "
            f"{missing}. Use TensorFlow 1.x or port the project to tf.compat.v1."
        )
    return tf


def prepare_work_dir(path_arg: Optional[str], clean: bool) -> Path:
    if path_arg is None:
        return Path(tempfile.mkdtemp(prefix="tensorflow-project-template-smoke-"))
    work_dir = Path(path_arg).expanduser().resolve()
    if clean and work_dir.exists():
        shutil.rmtree(str(work_dir))
    work_dir.mkdir(parents=True, exist_ok=True)
    return work_dir


def main() -> int:
    args = parse_args()
    if not args.allow_gpu:
        # Prevent TF1 from reserving visible GPU memory for this tiny CPU smoke.
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.is_dir():
        raise SystemExit(f"--repo-root is not a directory: {repo_root}")
    require_files(
        repo_root,
        [
            "base/base_model.py",
            "base/base_train.py",
            "models/example_model.py",
            "trainers/example_trainer.py",
            "data_loader/data_generator.py",
            "utils/logger.py",
        ],
    )

    sys.path.insert(0, str(repo_root))
    tf = import_tensorflow_1x()

    from data_loader.data_generator import DataGenerator
    from models.example_model import ExampleModel
    from trainers.example_trainer import ExampleTrainer
    from utils.logger import Logger

    work_dir = prepare_work_dir(args.work_dir, args.clean)
    summary_dir = work_dir / "summary"
    checkpoint_prefix = work_dir / "checkpoints" / "model.ckpt"
    summary_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_prefix.parent.mkdir(parents=True, exist_ok=True)

    config = SimpleNamespace(
        exp_name="skill-smoke",
        num_epochs=0,
        num_iter_per_epoch=1,
        learning_rate=0.001,
        batch_size=4,
        state_size=[784],
        max_to_keep=1,
        summary_dir=str(summary_dir),
        checkpoint_dir=str(checkpoint_prefix),
    )

    tf.reset_default_graph()
    sess = tf.Session()
    try:
        data = DataGenerator(config)
        model = ExampleModel(config)
        logger = Logger(sess, config)
        trainer = ExampleTrainer(sess, model, data, config, logger)
        loss, acc = trainer.train_step()
        # Run a one-iteration epoch as well so summary and checkpoint paths are exercised.
        trainer.train_epoch()
        checkpoint_files = sorted(checkpoint_prefix.parent.glob("model.ckpt*"))
        event_files = sorted(summary_dir.glob("**/events.*"))
        if not checkpoint_files:
            raise RuntimeError("training smoke completed but no checkpoint files were created")
        if not event_files:
            raise RuntimeError("training smoke completed but no TensorBoard event files were created")
        print("PASS tiny training smoke")
        print(f"loss={loss!r} acc={acc!r}")
        print(f"checkpoint_files={len(checkpoint_files)} summary_event_files={len(event_files)} work_dir={work_dir}")
    finally:
        sess.close()

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(f"FAIL tiny training smoke: {exc}")
