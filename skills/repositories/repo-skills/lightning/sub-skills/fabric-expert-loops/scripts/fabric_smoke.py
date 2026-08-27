#!/usr/bin/env python
"""Tiny Lightning Fabric smoke test with synthetic tensors.

The script is intentionally self-contained: it downloads no data and does not
read from a source checkout. It can run with plain Python on CPU or through
`fabric run --accelerator=cpu --devices=1`.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CPU-safe Lightning Fabric smoke loop with synthetic tensors.")
    parser.add_argument("--max-steps", type=int, default=3, help="Number of optimizer steps to run.")
    parser.add_argument("--batch-size", type=int, default=8, help="Synthetic batch size.")
    parser.add_argument("--input-dim", type=int, default=4, help="Number of synthetic input features.")
    parser.add_argument("--hidden-dim", type=int, default=8, help="Hidden layer width.")
    parser.add_argument("--lr", type=float, default=0.05, help="Learning rate.")
    parser.add_argument("--seed", type=int, default=123, help="Random seed for reproducible synthetic data.")
    parser.add_argument(
        "--checkpoint-path",
        type=Path,
        default=None,
        help="Optional path for a Fabric save/load checkpoint round-trip.",
    )
    parser.add_argument(
        "--no-launch",
        action="store_true",
        help="Skip fabric.launch(); useful when this script is invoked with `fabric run`.",
    )
    return parser.parse_args()


def load_runtime_dependencies():
    try:
        import torch
        from torch import nn
        from torch.utils.data import DataLoader, TensorDataset
        import lightning as L
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised only in missing installs
        missing = exc.name or "a runtime dependency"
        raise SystemExit(
            f"Missing {missing!r}. Install the public `lightning` package with a compatible PyTorch install "
            "and retry, or verify the environment with `python -c \"import torch, lightning; "
            "print(torch.__version__, lightning.__version__)\"`."
        ) from exc
    return torch, nn, DataLoader, TensorDataset, L


def make_dataset(num_samples: int, input_dim: int, seed: int):
    generator = torch.Generator().manual_seed(seed)
    inputs = torch.randn(num_samples, input_dim, generator=generator)
    weights = torch.arange(1, input_dim + 1, dtype=torch.float32).unsqueeze(1) / input_dim
    targets = inputs @ weights + 0.1
    return TensorDataset(inputs, targets)


def make_model(input_dim: int, hidden_dim: int):
    return nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, 1))


def maybe_launch(fabric, no_launch: bool) -> None:
    if no_launch:
        return
    try:
        fabric.launch()
    except RuntimeError as exc:
        if "launched through the CLI" not in str(exc):
            raise


def run(args: argparse.Namespace) -> dict[str, object]:
    if args.max_steps < 1:
        raise ValueError("--max-steps must be at least 1")
    if args.batch_size < 1:
        raise ValueError("--batch-size must be at least 1")

    global torch, nn, DataLoader, TensorDataset, L
    torch, nn, DataLoader, TensorDataset, L = load_runtime_dependencies()

    L.seed_everything(args.seed, workers=True)
    fabric = L.Fabric(accelerator="cpu", devices=1, precision="32-true")
    maybe_launch(fabric, args.no_launch)

    dataset = make_dataset(num_samples=max(args.batch_size * args.max_steps, args.batch_size), input_dim=args.input_dim, seed=args.seed)
    train_loader = DataLoader(dataset, batch_size=args.batch_size)
    train_loader = fabric.setup_dataloaders(train_loader)

    model = make_model(args.input_dim, args.hidden_dim)
    optimizer = torch.optim.SGD(model.parameters(), lr=args.lr)
    loss_fn = nn.MSELoss()
    model, optimizer = fabric.setup(model, optimizer)

    last_loss: Optional[float] = None
    global_step = 0
    model.train()
    for inputs, targets in train_loader:
        optimizer.zero_grad(set_to_none=True)
        predictions = model(inputs)
        loss = loss_fn(predictions, targets)
        fabric.backward(loss)
        optimizer.step()
        global_step += 1
        last_loss = float(loss.detach().cpu())
        if global_step >= args.max_steps:
            break

    checkpoint_exists = False
    if args.checkpoint_path is not None:
        args.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        state = {"model": model, "optimizer": optimizer, "global_step": global_step}
        fabric.save(args.checkpoint_path, state)
        remainder = fabric.load(args.checkpoint_path, {"model": model, "optimizer": optimizer}, weights_only=True)
        global_step = int(remainder.get("global_step", global_step))
        checkpoint_exists = args.checkpoint_path.exists()

    result = {"global_step": global_step, "last_loss": last_loss, "checkpoint_exists": checkpoint_exists}
    fabric.print(
        "fabric_smoke: ok "
        f"global_step={global_step} "
        f"last_loss={last_loss:.6f} "
        f"checkpoint_exists={checkpoint_exists}"
    )
    return result


def main() -> None:
    args = parse_args()
    run(args)


if __name__ == "__main__":
    main()
