#!/usr/bin/env python3
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import torch
from torch.utils.data import DataLoader, TensorDataset

from ignite.engine import Events, create_supervised_evaluator, create_supervised_trainer
from ignite.handlers import (
    BasicTimeProfiler,
    Checkpoint,
    DiskSaver,
    EarlyStopping,
    LinearCyclicalScheduler,
    ProgressBar,
    Timer,
)
from ignite.handlers.logger_utils import setup_tb_logging
from ignite.metrics import Accuracy
from ignite.utils import manual_seed


def build_loaders() -> tuple[DataLoader, DataLoader]:
    manual_seed(0)
    features = torch.randn(48, 4)
    targets = (features.sum(dim=1) > 0).long()
    train = DataLoader(TensorDataset(features[:32], targets[:32]), batch_size=8, shuffle=False)
    val = DataLoader(TensorDataset(features[32:], targets[32:]), batch_size=8, shuffle=False)
    return train, val


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a compact Ignite handlers smoke check.")
    parser.add_argument("--epochs", type=int, default=10, help="Maximum epochs to request before early stopping.")
    parser.add_argument("--patience", type=int, default=1, help="Patience used by the early stopping handler.")
    args = parser.parse_args()

    train_loader, val_loader = build_loaders()

    model = torch.nn.Linear(4, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.2)
    loss_fn = torch.nn.CrossEntropyLoss()

    trainer = create_supervised_trainer(model, optimizer, loss_fn)
    evaluator = create_supervised_evaluator(model, metrics={"acc": Accuracy()})

    timer = Timer(average=True)
    timer.attach(
        trainer,
        start=Events.STARTED,
        resume=Events.ITERATION_STARTED,
        pause=Events.ITERATION_COMPLETED,
        step=Events.ITERATION_COMPLETED,
    )

    profiler = BasicTimeProfiler()
    profiler.attach(trainer)

    scheduler = LinearCyclicalScheduler(optimizer, "lr", start_value=0.2, end_value=0.05, cycle_size=2)
    trainer.add_event_handler(Events.ITERATION_STARTED, scheduler)

    ProgressBar(persist=False).attach(trainer, metric_names="all")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        tb_dir = tmp_path / "tensorboard"
        ckpt_dir = tmp_path / "checkpoints"

        tb_logger = setup_tb_logging(
            output_path=str(tb_dir),
            trainer=trainer,
            optimizers=optimizer,
            evaluators={"validation": evaluator},
            log_every_iters=1,
        )

        checkpointer = Checkpoint(
            {"model": model, "optimizer": optimizer},
            DiskSaver(ckpt_dir, create_dir=True, require_empty=False),
            n_saved=1,
            filename_prefix="ignite-handlers",
            score_function=lambda engine: float(engine.state.metrics["acc"]),
            score_name="acc",
        )
        stopper = EarlyStopping(
            patience=args.patience,
            score_function=lambda engine: 0.0,
            trainer=trainer,
        )

        @trainer.on(Events.EPOCH_COMPLETED)
        def _validate(engine: torch.nn.Module) -> None:
            evaluator.run(val_loader)

        evaluator.add_event_handler(Events.COMPLETED, checkpointer)
        evaluator.add_event_handler(Events.COMPLETED, stopper)

        trainer.run(train_loader, max_epochs=args.epochs)
        tb_logger.close()

        profile_csv = tmp_path / "profile.csv"
        profiler.write_results(str(profile_csv))
        results = profiler.get_results()

        print(f"handlers_epoch={trainer.state.epoch}")
        print(f"handlers_acc={float(evaluator.state.metrics['acc']):.6f}")
        print(f"handlers_lr={optimizer.param_groups[0]['lr']:.6f}")
        print(f"handlers_timer={timer.value():.6f}")
        print(f"handlers_checkpoints={[p.name for p in sorted(ckpt_dir.glob('*.pt'))]}")
        print(f"handlers_profile_rows={len(results)}")
        print(f"handlers_profile_csv={profile_csv.exists()}")
        print(f"handlers_tb_files={sum(1 for p in tb_dir.rglob('*') if p.is_file())}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
