#!/usr/bin/env python3
"""Tiny CPU/no-network smoke for Composer Profiler + JSONTraceHandler.

Runs a two-batch training loop with one warmup batch and one active/save batch.
Use --output-dir to keep traces; otherwise a temporary directory is used.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny Composer profiler smoke test.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for generated traces. Defaults to a temporary directory.",
    )
    parser.add_argument("--run-name", default="profiler-smoke", help="Composer run_name for this smoke.")
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
    from composer.loggers import Logger
    from composer.models.tasks import ComposerClassifier
    from composer.profiler import JSONTraceHandler, Profiler, cyclic_schedule

    class ProfiledPulse(Callback):
        def batch_end(self, state: State, logger: Logger) -> None:
            del logger
            if state.profiler is not None:
                marker = state.profiler.marker("smoke/batch_end", categories=["smoke"])
                with marker:
                    _ = sum(range(8))

    module = nn.Sequential(nn.Linear(4, 8), nn.ReLU(), nn.Linear(8, 2))
    model = ComposerClassifier(module=module, num_classes=2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

    profiler = Profiler(
        schedule=cyclic_schedule(skip_first=0, wait=0, warmup=1, active=1, repeat=1),
        trace_handlers=[
            JSONTraceHandler(
                folder=str(output_dir / "{run_name}" / "traces"),
                filename="ep{epoch}-ba{batch}-rank{rank}.json",
                remote_file_name=None,
                merged_trace_filename=None,
                merged_trace_remote_file_name=None,
                overwrite=True,
            ),
        ],
        sys_prof_cpu=False,
        sys_prof_memory=False,
        sys_prof_disk=False,
        sys_prof_net=False,
        torch_prof_profile_memory=False,
        torch_prof_with_flops=False,
        torch_prof_memory_filename=None,
    )

    trainer = Trainer(
        model=model,
        train_dataloader=_build_loader(),
        max_duration="2ba",
        optimizers=optimizer,
        device="cpu",
        run_name=run_name,
        profiler=profiler,
        callbacks=[ProfiledPulse()],
        progress_bar=False,
        log_to_console=False,
        train_subset_num_batches=2,
    )
    try:
        trainer.fit()
    finally:
        trainer.close()

    trace_dir = output_dir / run_name / "traces"
    traces = sorted(trace_dir.glob("*.json"))
    if not traces:
        raise AssertionError(f"Expected JSON trace output under {trace_dir}")

    print(f"OK profiler smoke: {len(traces)} trace file(s); first trace: {traces[0]}")


def main() -> int:
    args = _parse_args()
    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        _run(args.output_dir, args.run_name)
        return 0

    with tempfile.TemporaryDirectory(prefix="composer-profiler-smoke-") as tmpdir:
        _run(Path(tmpdir), args.run_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
