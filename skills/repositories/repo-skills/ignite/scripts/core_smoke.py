#!/usr/bin/env python3
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
import warnings

import torch
from torch.utils.data import DataLoader, TensorDataset

import ignite.distributed as idist
from ignite.engine import Engine, Events, create_supervised_evaluator, create_supervised_trainer
from ignite.handlers import Checkpoint, DiskSaver, EarlyStopping, LinearCyclicalScheduler, Timer
from ignite.metrics import Accuracy, ROC_AUC, PrecisionRecallCurve, SSIM
from ignite.utils import manual_seed


def run_training_smoke() -> None:
    manual_seed(0)
    features = torch.randn(48, 4)
    targets = (features.sum(dim=1) > 0).long()
    train_loader = DataLoader(TensorDataset(features[:32], targets[:32]), batch_size=8, shuffle=False)
    val_loader = DataLoader(TensorDataset(features[32:], targets[32:]), batch_size=8, shuffle=False)

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

    scheduler = LinearCyclicalScheduler(optimizer, "lr", start_value=0.2, end_value=0.05, cycle_size=2)
    trainer.add_event_handler(Events.ITERATION_STARTED, scheduler)

    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_dir = Path(tmpdir)
        checkpointer = Checkpoint(
            {"model": model, "optimizer": optimizer},
            DiskSaver(checkpoint_dir, create_dir=True, require_empty=False),
            n_saved=1,
            filename_prefix="ignite-core",
            score_function=lambda engine: float(engine.state.metrics["acc"]),
            score_name="acc",
        )
        stopper = EarlyStopping(
            patience=1,
            score_function=lambda engine: float(engine.state.metrics["acc"]),
            trainer=trainer,
            threshold=1.0,
            mode="max",
        )

        @trainer.on(Events.EPOCH_COMPLETED)
        def _validate(engine: Engine) -> None:
            evaluator.run(val_loader)

        evaluator.add_event_handler(Events.COMPLETED, checkpointer)
        evaluator.add_event_handler(Events.COMPLETED, stopper)

        trainer.run(train_loader, max_epochs=3)
        state = evaluator.run(val_loader)

        print(f"engine_epoch={trainer.state.epoch}")
        print(f"engine_acc={float(state.metrics['acc']):.6f}")
        print(f"lr={optimizer.param_groups[0]['lr']:.6f}")
        print(f"timer={timer.value():.6f}")
        print(f"checkpoints={[p.name for p in sorted(checkpoint_dir.glob('*.pt'))]}")


def run_metric_smoke() -> None:
    class_eval = Engine(lambda engine, batch: batch)
    y_pred = torch.tensor([
        [0.90, 0.10],
        [0.20, 0.80],
        [0.75, 0.25],
        [0.05, 0.95],
    ])
    y_true = torch.tensor([0, 1, 0, 1])
    Accuracy().attach(class_eval, "accuracy")
    class_state = class_eval.run([(y_pred, y_true)])
    print(f"metrics_accuracy={float(class_state.metrics['accuracy']):.6f}")

    binary_eval = Engine(lambda engine, batch: batch)
    y_score = torch.tensor([0.10, 0.20, 0.80, 0.95])
    y_binary = torch.tensor([0, 0, 1, 1])
    pr_curve = PrecisionRecallCurve()
    roc_auc = ROC_AUC()
    pr_curve.attach(binary_eval, "pr_curve")
    roc_auc.attach(binary_eval, "roc_auc")
    binary_state = binary_eval.run([(y_score, y_binary)])
    print(f"metrics_roc_auc={float(binary_state.metrics['roc_auc']):.6f}")
    print(f"metrics_pr_points={len(binary_state.metrics['pr_curve'][0])}")

    image_eval = Engine(lambda engine, batch: batch)
    ssim = SSIM(data_range=1.0)
    ssim.attach(image_eval, "ssim")
    image = torch.rand(2, 3, 8, 8)
    image_state = image_eval.run([(image, image * 0.9)])
    print(f"metrics_ssim={float(image_state.metrics['ssim']):.6f}")


def run_distributed_smoke() -> None:
    print(f"distributed_backends={idist.available_backends()}")

    def _report(local_rank: int) -> None:
        print(
            f"distributed_serial rank={idist.get_rank()} local_rank={local_rank} "
            f"world_size={idist.get_world_size()} backend={idist.backend()} device={idist.device()}"
        )

    with idist.Parallel(backend=None) as parallel:
        parallel.run(_report)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a compact Ignite smoke check across core workflows.")
    parser.add_argument(
        "--mode",
        choices=("all", "engine", "metrics", "distributed"),
        default="all",
        help="Which smoke section to run.",
    )
    args = parser.parse_args()

    warnings.filterwarnings("ignore", category=DeprecationWarning)

    if args.mode in ("all", "engine"):
        run_training_smoke()
    if args.mode in ("all", "metrics"):
        run_metric_smoke()
    if args.mode in ("all", "distributed"):
        run_distributed_smoke()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
