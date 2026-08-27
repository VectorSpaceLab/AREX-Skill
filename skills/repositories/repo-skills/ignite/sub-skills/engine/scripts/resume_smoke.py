#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch.utils.data import DataLoader, TensorDataset

from ignite.engine import Events, create_supervised_evaluator, create_supervised_trainer
from ignite.metrics import Accuracy
from ignite.utils import manual_seed


def build_loader() -> DataLoader:
    torch.manual_seed(0)
    features = torch.randn(32, 4)
    targets = torch.randint(0, 2, (32,))
    return DataLoader(TensorDataset(features, targets), batch_size=8, shuffle=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny Ignite engine resume smoke check.")
    parser.add_argument("--epochs", type=int, default=2, help="Total epochs to reach after the resumed run.")
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Create the trainer with deterministic=True to exercise DeterministicEngine.",
    )
    args = parser.parse_args()

    manual_seed(0)
    loader = build_loader()
    model = torch.nn.Linear(4, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    loss_fn = torch.nn.CrossEntropyLoss()

    trainer = create_supervised_trainer(model, optimizer, loss_fn, deterministic=args.deterministic)
    evaluator = create_supervised_evaluator(model, metrics={"acc": Accuracy()})

    @trainer.on(Events.EPOCH_COMPLETED)
    def _log_epoch(engine: torch.nn.Module) -> None:
        print(f"first_pass_epoch={engine.state.epoch} loss={float(engine.state.output):.6f}")

    trainer.run(loader, max_epochs=1)
    saved_state = trainer.state_dict()

    resumed = create_supervised_trainer(model, optimizer, loss_fn, deterministic=args.deterministic)
    resumed.load_state_dict(saved_state)
    resumed.run(loader, max_epochs=args.epochs)

    eval_state = evaluator.run(loader)
    print(f"resumed_epoch={resumed.state.epoch}")
    print(f"accuracy={float(eval_state.metrics['acc']):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
