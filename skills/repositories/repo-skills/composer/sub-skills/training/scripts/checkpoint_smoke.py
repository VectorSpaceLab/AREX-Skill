#!/usr/bin/env python3
"""CPU-safe Composer checkpoint save/load smoke test.

The script trains a tiny model on synthetic data, saves a local checkpoint in a
temporary directory, verifies manual `load_path` resume, and optionally verifies
`autoresume=True`. It performs no downloads.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

try:
    from composer import Trainer
    from composer.models import ComposerClassifier
except ModuleNotFoundError as exc:
    if exc.name == "composer":
        raise SystemExit("Unable to import composer. Install the public package with: pip install mosaicml") from exc
    raise

SAVE_FILENAME = "ep{epoch}-ba{batch}-rank{rank}.pt"
LATEST_FILENAME = "latest-rank{rank}.pt"


def build_loader(samples: int, features: int, classes: int, batch_size: int, seed: int) -> DataLoader:
    generator = torch.Generator().manual_seed(seed)
    inputs = torch.randn(samples, features, generator=generator)
    targets = torch.randint(low=0, high=classes, size=(samples,), generator=generator)
    return DataLoader(TensorDataset(inputs, targets), batch_size=batch_size, shuffle=False)


def build_model(features: int, hidden: int, classes: int, seed: int) -> ComposerClassifier:
    torch.manual_seed(seed)
    module = nn.Sequential(
        nn.Linear(features, hidden),
        nn.ReLU(),
        nn.Linear(hidden, classes),
    )
    return ComposerClassifier(module=module, num_classes=classes)


def model_checksum(model: torch.nn.Module) -> float:
    with torch.no_grad():
        return float(sum(param.detach().cpu().float().sum().item() for param in model.parameters()))


def make_trainer(
    *,
    model: ComposerClassifier,
    loader: DataLoader,
    lr: float,
    max_batches: int,
    run_name: str,
    save_folder: str | None = None,
    load_path: str | None = None,
    autoresume: bool = False,
) -> Trainer:
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)
    return Trainer(
        model=model,
        train_dataloader=loader,
        optimizers=optimizer,
        max_duration=f"{max_batches}ba",
        train_subset_num_batches=max_batches,
        device="cpu",
        precision="fp32",
        run_name=run_name,
        save_folder=save_folder,
        save_filename=SAVE_FILENAME,
        save_latest_filename=LATEST_FILENAME,
        save_interval="1ba",
        save_overwrite=True,
        load_path=load_path,
        autoresume=autoresume,
        progress_bar=False,
        log_to_console=False,
    )


def initial_training(args: argparse.Namespace, work_dir: str) -> dict[str, Any]:
    save_folder = str(Path(work_dir) / "checkpoints")
    loader = build_loader(args.samples, args.features, args.classes, args.batch_size, args.seed)
    model = build_model(args.features, args.hidden, args.classes, args.seed)
    trainer = make_trainer(
        model=model,
        loader=loader,
        lr=args.lr,
        max_batches=args.first_batches,
        run_name=args.run_name,
        save_folder=save_folder,
    )
    trainer.fit()

    if not trainer.saved_checkpoints:
        raise RuntimeError("Composer did not report any saved checkpoints.")
    latest_checkpoint = trainer.saved_checkpoints[-1]
    if not os.path.exists(latest_checkpoint):
        raise RuntimeError(f"Reported checkpoint does not exist: {latest_checkpoint}")

    latest_marker = Path(save_folder) / LATEST_FILENAME.format(rank=0)
    if not latest_marker.exists() and not latest_marker.is_symlink():
        raise RuntimeError(f"Latest checkpoint marker was not created: {latest_marker}")

    return {
        "save_folder": save_folder,
        "latest_checkpoint": latest_checkpoint,
        "latest_marker": str(latest_marker),
        "saved_count": len(trainer.saved_checkpoints),
        "saved_batch": int(trainer.state.timestamp.batch),
        "checksum": model_checksum(trainer.state.model),
    }


def manual_resume(args: argparse.Namespace, checkpoint_info: dict[str, Any]) -> dict[str, Any]:
    loader = build_loader(args.samples, args.features, args.classes, args.batch_size, args.seed)
    model = build_model(args.features, args.hidden, args.classes, args.seed + 100)
    trainer = make_trainer(
        model=model,
        loader=loader,
        lr=args.lr,
        max_batches=args.resume_batches,
        run_name=args.run_name,
        load_path=checkpoint_info["latest_checkpoint"],
    )
    loaded_batch = int(trainer.state.timestamp.batch)
    loaded_checksum = model_checksum(trainer.state.model)
    if loaded_batch != checkpoint_info["saved_batch"]:
        raise RuntimeError(f"Manual resume loaded batch {loaded_batch}, expected {checkpoint_info['saved_batch']}.")
    if abs(loaded_checksum - checkpoint_info["checksum"]) > 1e-5:
        raise RuntimeError("Manual resume model checksum did not match saved model checksum.")
    trainer.fit()
    return {
        "loaded_batch": loaded_batch,
        "final_batch": int(trainer.state.timestamp.batch),
        "loaded_checksum": loaded_checksum,
    }


def autoresume(args: argparse.Namespace, checkpoint_info: dict[str, Any]) -> dict[str, Any]:
    loader = build_loader(args.samples, args.features, args.classes, args.batch_size, args.seed)
    model = build_model(args.features, args.hidden, args.classes, args.seed + 200)
    trainer = make_trainer(
        model=model,
        loader=loader,
        lr=args.lr,
        max_batches=args.resume_batches,
        run_name=args.run_name,
        save_folder=checkpoint_info["save_folder"],
        autoresume=True,
    )
    loaded_batch = int(trainer.state.timestamp.batch)
    loaded_checksum = model_checksum(trainer.state.model)
    if loaded_batch != checkpoint_info["saved_batch"]:
        raise RuntimeError(f"Autoresume loaded batch {loaded_batch}, expected {checkpoint_info['saved_batch']}.")
    if abs(loaded_checksum - checkpoint_info["checksum"]) > 1e-5:
        raise RuntimeError("Autoresume model checksum did not match saved model checksum.")
    trainer.fit()
    return {
        "loaded_batch": loaded_batch,
        "final_batch": int(trainer.state.timestamp.batch),
        "loaded_checksum": loaded_checksum,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=32, help="Number of synthetic samples.")
    parser.add_argument("--features", type=int, default=8, help="Input feature dimension.")
    parser.add_argument("--hidden", type=int, default=16, help="Hidden layer width.")
    parser.add_argument("--classes", type=int, default=3, help="Number of classification classes.")
    parser.add_argument("--batch-size", type=int, default=8, help="Dataloader batch size.")
    parser.add_argument("--first-batches", type=int, default=1, help="Batches before the checkpoint is saved.")
    parser.add_argument("--resume-batches", type=int, default=2, help="Total target batches after resuming.")
    parser.add_argument("--lr", type=float, default=0.05, help="SGD learning rate.")
    parser.add_argument("--seed", type=int, default=23, help="Random seed.")
    parser.add_argument("--run-name", default="composer-checkpoint-smoke", help="Stable run name for autoresume.")
    parser.add_argument("--mode", choices=("manual", "autoresume", "both"), default="both", help="Resume path to verify.")
    parser.add_argument("--keep-dir", default=None, help="Optional directory to keep checkpoints instead of using a temporary directory.")
    return parser.parse_args()


def run(args: argparse.Namespace, work_dir: str) -> dict[str, Any]:
    if args.resume_batches <= args.first_batches:
        raise ValueError("--resume-batches must be greater than --first-batches.")
    if args.samples < args.batch_size * args.resume_batches:
        raise ValueError("--samples must be at least --batch-size * --resume-batches.")

    checkpoint_info = initial_training(args, work_dir)
    result: dict[str, Any] = {
        "work_dir": work_dir if args.keep_dir else "temporary directory removed after success",
        "save_folder": checkpoint_info["save_folder"] if args.keep_dir else "temporary checkpoint folder",
        "latest_checkpoint_name": Path(checkpoint_info["latest_checkpoint"]).name,
        "latest_marker_name": Path(checkpoint_info["latest_marker"]).name,
        "saved_count": checkpoint_info["saved_count"],
        "saved_batch": checkpoint_info["saved_batch"],
    }

    if args.mode in ("manual", "both"):
        manual = manual_resume(args, checkpoint_info)
        if manual["final_batch"] != args.resume_batches:
            raise RuntimeError(f"Manual resume final batch {manual['final_batch']} != {args.resume_batches}.")
        result["manual_resume"] = manual

    if args.mode in ("autoresume", "both"):
        auto = autoresume(args, checkpoint_info)
        if auto["final_batch"] != args.resume_batches:
            raise RuntimeError(f"Autoresume final batch {auto['final_batch']} != {args.resume_batches}.")
        result["autoresume"] = auto

    return result


def main() -> None:
    args = parse_args()
    if args.keep_dir:
        Path(args.keep_dir).mkdir(parents=True, exist_ok=True)
        result = run(args, args.keep_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="composer-checkpoint-smoke-") as work_dir:
            result = run(args, work_dir)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
