#!/usr/bin/env python3
"""Tiny deterministic CPU smoke for bitsandbytes optimizers.

This helper is adapted from the repository's CPU training example, but it
intentionally avoids datasets, model downloads, Trainer integration, checkpoint
writes, and long training. It validates that bitsandbytes imports, the selected
optimizer can run a few PyTorch training steps, and optimizer state is populated.

Examples:
    python cpu-optimizer-smoke.py --optimizer adam8bit --steps 3
    python cpu-optimizer-smoke.py --optimizer adam32bit --steps 3
    python cpu-optimizer-smoke.py --optimizer adam8bit --force-8bit-small-tensors
"""

from __future__ import annotations

import argparse
from collections import Counter
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny CPU bitsandbytes optimizer smoke test.")
    parser.add_argument("--optimizer", choices=("adam8bit", "adam32bit"), default="adam8bit")
    parser.add_argument("--steps", type=int, default=3, help="Number of tiny training steps to run.")
    parser.add_argument("--lr", type=float, default=0.01, help="Learning rate for the selected optimizer.")
    parser.add_argument(
        "--force-8bit-small-tensors",
        action="store_true",
        help="Set min_8bit_size=1 for diagnostics; defaults keep small tensors in 32-bit.",
    )
    return parser.parse_args()


def import_training_modules():
    try:
        import torch
    except Exception as exc:  # pragma: no cover - user-facing diagnostic path
        print(f"ERROR: could not import torch: {exc}", file=sys.stderr)
        print("Install PyTorch before running this optimizer smoke.", file=sys.stderr)
        raise SystemExit(2) from exc

    try:
        import bitsandbytes as bnb
    except Exception as exc:  # pragma: no cover - user-facing diagnostic path
        print(f"ERROR: could not import bitsandbytes: {exc}", file=sys.stderr)
        print("Install or repair bitsandbytes before running this optimizer smoke.", file=sys.stderr)
        raise SystemExit(2) from exc

    return torch, bnb


def build_model(torch_module):
    class TinyRegressor(torch_module.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.net = torch_module.nn.Sequential(
                torch_module.nn.Linear(8, 32),
                torch_module.nn.LayerNorm(32),
                torch_module.nn.ReLU(),
                torch_module.nn.Linear(32, 4),
            )

        def forward(self, inputs):
            return self.net(inputs)

    return TinyRegressor()


def make_optimizer(model, args: argparse.Namespace, bnb_module):
    min_8bit_size = 1 if args.force_8bit_small_tensors else 4096
    if args.optimizer == "adam8bit":
        return bnb_module.optim.Adam8bit(model.parameters(), lr=args.lr, min_8bit_size=min_8bit_size)
    if args.optimizer == "adam32bit":
        return bnb_module.optim.Adam32bit(model.parameters(), lr=args.lr)
    raise AssertionError(f"Unhandled optimizer: {args.optimizer}")


def summarize_state(optimizer) -> tuple[int, Counter[str], Counter[str]]:
    tensor_count = 0
    dtype_counts: Counter[str] = Counter()
    device_counts: Counter[str] = Counter()
    for state in optimizer.state.values():
        for value in state.values():
            if hasattr(value, "dtype") and hasattr(value, "device"):
                tensor_count += 1
                dtype_counts[str(value.dtype)] += 1
                device_counts[str(value.device)] += 1
    return tensor_count, dtype_counts, device_counts


def main() -> int:
    args = parse_args()
    if args.steps < 1:
        print("ERROR: --steps must be >= 1", file=sys.stderr)
        return 2

    torch, bnb = import_training_modules()
    torch.manual_seed(0)
    model = build_model(torch)
    optimizer = make_optimizer(model, args, bnb)

    inputs = torch.linspace(-1.0, 1.0, steps=32, dtype=torch.float32).reshape(4, 8)
    target = torch.stack(
        [
            inputs[:, 0] + inputs[:, 1],
            inputs[:, 2] - inputs[:, 3],
            inputs[:, 4] * 0.5,
            -inputs[:, 5],
        ],
        dim=1,
    )

    losses: list[float] = []
    for _ in range(args.steps):
        prediction = model(inputs)
        loss = torch.nn.functional.mse_loss(prediction, target)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        losses.append(float(loss.detach()))

    tensor_count, dtype_counts, device_counts = summarize_state(optimizer)
    print(f"bitsandbytes version: {getattr(bnb, '__version__', 'unknown')}")
    print(f"optimizer: bnb.optim.{optimizer.__class__.__name__}")
    print(f"steps: {args.steps}")
    print(f"loss_start: {losses[0]:.6f}")
    print(f"loss_end: {losses[-1]:.6f}")
    print(f"state_tensor_count: {tensor_count}")
    print("state_dtypes: " + ", ".join(f"{key}={value}" for key, value in sorted(dtype_counts.items())))
    print("state_devices: " + ", ".join(f"{key}={value}" for key, value in sorted(device_counts.items())))

    if tensor_count == 0:
        print("ERROR: optimizer state was not populated after training steps", file=sys.stderr)
        return 1
    if not torch.isfinite(torch.tensor(losses)).all():
        print("ERROR: non-finite loss observed", file=sys.stderr)
        return 1
    print("OK: tiny CPU optimizer smoke completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
