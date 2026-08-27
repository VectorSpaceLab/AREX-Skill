#!/usr/bin/env python
"""Tiny Lightning ServableModule smoke checks.

Default behavior avoids starting a long-lived service. Use --run-validator only when
FastAPI, Uvicorn, Requests, and a free localhost port are available.
"""

from __future__ import annotations

import argparse
from typing import Any, Callable


def build_tiny_servable_class():
    import torch
    from torch import Tensor
    from torch.utils.data import DataLoader, TensorDataset

    from lightning.pytorch import LightningModule
    from lightning.pytorch.serve import ServableModule

    class TinyServable(LightningModule, ServableModule):
        def __init__(self) -> None:
            super().__init__()
            self.layer = torch.nn.Linear(2, 2, bias=False)
            with torch.no_grad():
                self.layer.weight.copy_(torch.eye(2))

        def forward(self, x: Tensor) -> Tensor:
            return self.layer(x)

        def training_step(self, batch: tuple[Tensor, Tensor], batch_idx: int) -> Tensor:
            x, y = batch
            return torch.nn.functional.mse_loss(self(x), y)

        def configure_optimizers(self) -> torch.optim.Optimizer:
            return torch.optim.SGD(self.parameters(), lr=0.01)

        def train_dataloader(self) -> DataLoader:
            x = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
            return DataLoader(TensorDataset(x, x), batch_size=1)

        def configure_payload(self) -> dict[str, Any]:
            return {"body": {"x": [1.0, 2.0]}}

        def configure_serialization(self) -> tuple[dict[str, Callable], dict[str, Callable]]:
            def deserialize(value: list[float]) -> Tensor:
                return torch.tensor(value, dtype=torch.float32)

            def serialize(value: Tensor) -> list[float]:
                return value.detach().cpu().tolist()

            return {"x": deserialize}, {"output": serialize}

        def serve_step(self, x: Tensor) -> dict[str, Tensor]:
            return {"output": self(x)}

        def configure_response(self) -> dict[str, Any]:
            return {"output": [1.0, 2.0]}

    return TinyServable


def check_shape() -> None:
    import torch

    TinyServable = build_tiny_servable_class()
    model = TinyServable()
    payload = model.configure_payload()
    if "body" not in payload:
        raise AssertionError("configure_payload() must include a top-level 'body' key")

    deserializers, serializers = model.configure_serialization()
    body = dict(payload["body"])
    inputs = {name: deserialize(body[name]) for name, deserialize in deserializers.items()}

    with torch.inference_mode():
        output = model.serve_step(**inputs)

    serialized = {name: serializers[name](value) for name, value in output.items()}
    expected = model.configure_response()
    if serialized != expected:
        raise AssertionError(f"Expected {expected}, got {serialized}")

    print("SERVABLE_SMOKE_OK shape_check output={'output': [1.0, 2.0]}")


def run_validator(port: int, timeout: int) -> None:
    from lightning.pytorch import Trainer
    from lightning.pytorch.serve import ServableModuleValidator

    TinyServable = build_tiny_servable_class()
    callback = ServableModuleValidator(port=port, timeout=timeout)
    trainer = Trainer(
        accelerator="cpu",
        max_epochs=1,
        limit_train_batches=1,
        limit_val_batches=0,
        logger=False,
        enable_checkpointing=False,
        enable_model_summary=False,
        callbacks=[callback],
    )
    trainer.fit(TinyServable())
    if callback.successful is not True:
        raise AssertionError(f"Validator did not report success: {callback.state_dict()}")
    print(f"SERVABLE_SMOKE_OK validator port={port} response={callback.resp.json()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a tiny Lightning ServableModule without external data.")
    parser.add_argument("--check-shape", action="store_true", help="Run local payload/serialization/serve_step assertions.")
    parser.add_argument(
        "--run-validator",
        action="store_true",
        help="Start the Lightning ServableModuleValidator FastAPI smoke. Requires optional server dependencies.",
    )
    parser.add_argument("--port", type=int, default=8099, help="Localhost port for --run-validator.")
    parser.add_argument("--timeout", type=int, default=20, help="Seconds to wait for validator server startup.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.check_shape and not args.run_validator:
        print("No check selected; use --check-shape or --run-validator. Try --help for details.")
        return
    if args.check_shape:
        check_shape()
    if args.run_validator:
        run_validator(port=args.port, timeout=args.timeout)


if __name__ == "__main__":
    main()
