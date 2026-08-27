#!/usr/bin/env python3
"""Tiny tensorboardX PyTorch graph smoke check.

This script uses CPU tensors only and performs no network access. It verifies
that SummaryWriter.add_graph can trace a small torch.nn.Module and create an
event file in a temporary or user-provided log directory.
"""

from __future__ import annotations

import argparse
import contextlib
import pathlib
import tempfile


def _import_deps():
    try:
        from tensorboardX import SummaryWriter
    except Exception as exc:  # pragma: no cover - environment guard
        print(f"SKIP: tensorboardX SummaryWriter is required for this smoke ({exc})")
        return None, None

    try:
        import torch
    except Exception as exc:  # pragma: no cover - environment guard
        print(f"SKIP: PyTorch is required for add_graph ({exc})")
        return None, None

    try:
        import torch.utils.tensorboard._pytorch_graph  # noqa: F401
    except Exception as exc:  # pragma: no cover - environment guard
        print(f"SKIP: PyTorch TensorBoard graph helper is unavailable ({exc})")
        return None, None
    return SummaryWriter, torch


def _run(logdir: pathlib.Path) -> None:
    SummaryWriter, torch = _import_deps()
    if SummaryWriter is None or torch is None:
        return

    class TinyGraph(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.linear = torch.nn.Linear(3, 2)

        def forward(self, x):
            return torch.relu(self.linear(x))

    model = TinyGraph().eval()
    sample = (torch.zeros(1, 3),)

    with SummaryWriter(str(logdir)) as writer:
        writer.add_graph(model, sample, verbose=False)

    event_files = list(logdir.glob("events.out.tfevents.*"))
    if not event_files:
        raise RuntimeError("add_graph completed but no tensorboardX event file was created")
    print("OK: add_graph wrote a CPU graph event")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a tiny tensorboardX CPU graph smoke check.")
    parser.add_argument("--logdir", type=pathlib.Path, help="Optional output log directory to keep after the run.")
    args = parser.parse_args(argv)

    if args.logdir is not None:
        args.logdir.mkdir(parents=True, exist_ok=True)
        _run(args.logdir)
    else:
        with tempfile.TemporaryDirectory(prefix="tbx-graph-") as tmp:
            _run(pathlib.Path(tmp))
    return 0


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        raise SystemExit(main())
    raise SystemExit(130)
