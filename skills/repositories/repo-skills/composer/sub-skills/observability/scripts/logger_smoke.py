#!/usr/bin/env python3
"""Tiny no-network smoke for Composer local loggers.

Runs a two-batch CPU classification loop with InMemoryLogger and FileLogger.
Use --output-dir to keep artifacts; otherwise a temporary directory is used.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from typing import Optional


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny Composer logger smoke test.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for generated logs. Defaults to a temporary directory.",
    )
    parser.add_argument("--run-name", default="logger-smoke", help="Composer run_name for this smoke.")
    return parser.parse_args()


def _build_loader():
    import torch
    from torch.utils.data import DataLoader, TensorDataset

    features = torch.tensor(
        [
            [0.0, 0.0, 1.0, 1.0],
            [1.0, 0.0, 0.0, 1.0],
            [0.0, 1.0, 1.0, 0.0],
            [1.0, 1.0, 0.0, 0.0],
        ],
        dtype=torch.float32,
    )
    labels = torch.tensor([0, 1, 0, 1], dtype=torch.long)
    return DataLoader(TensorDataset(features, labels), batch_size=2, shuffle=False, num_workers=0)


def _run(output_dir: Path, run_name: str) -> None:
    import torch
    from torch import nn

    from composer import Callback, State, Trainer
    from composer.loggers import FileLogger, InMemoryLogger, Logger
    from composer.models.tasks import ComposerClassifier

    class MetricPulse(Callback):
        def batch_end(self, state: State, logger: Logger) -> None:
            logger.log_metrics({"smoke/batch": float(state.timestamp.batch.value)})

    module = nn.Sequential(nn.Linear(4, 8), nn.ReLU(), nn.Linear(8, 2))
    model = ComposerClassifier(module=module, num_classes=2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

    in_memory = InMemoryLogger()
    file_logger = FileLogger(
        filename=str(output_dir / "{run_name}" / "logs-rank{rank}.txt"),
        remote_file_name="{run_name}/logs-rank{rank}.txt",
        capture_stdout=False,
        capture_stderr=False,
        flush_interval=1,
        overwrite=True,
    )

    trainer = Trainer(
        model=model,
        train_dataloader=_build_loader(),
        max_duration="2ba",
        optimizers=optimizer,
        device="cpu",
        run_name=run_name,
        loggers=[in_memory, file_logger],
        callbacks=[MetricPulse()],
        progress_bar=False,
        log_to_console=False,
        train_subset_num_batches=2,
    )
    try:
        trainer.fit()
    finally:
        trainer.close()

    expected_log = output_dir / run_name / "logs-rank0.txt"
    if not expected_log.exists():
        raise AssertionError(f"Expected FileLogger output not found: {expected_log}")
    if "smoke/batch" not in in_memory.data:
        raise AssertionError("Expected custom smoke metric in InMemoryLogger.data")

    print(f"OK logger smoke: {len(in_memory.data)} metric keys; log file: {expected_log}")


def main() -> int:
    args = _parse_args()
    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        _run(args.output_dir, args.run_name)
        return 0

    with tempfile.TemporaryDirectory(prefix="composer-logger-smoke-") as tmpdir:
        _run(Path(tmpdir), args.run_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
