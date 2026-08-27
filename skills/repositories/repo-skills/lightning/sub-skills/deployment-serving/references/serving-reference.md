# Serving Reference

This reference covers Lightning prediction, checkpoint inference, and `lightning.pytorch.serve` validation. Keep training-loop and checkpoint-creation details in `../training-core/SKILL.md`; use this file once a model is ready to run predictions or be packaged for production.

## Prediction Routes

### Direct checkpoint inference

Use direct inference when the input is already in memory and the production script can import the model class.

```python
import torch

model = LitModel.load_from_checkpoint("best_model.ckpt")
model.eval()

with torch.inference_mode():
    prediction = model(x)
```

Checklist:

- The class definition and constructor arguments must match the checkpoint.
- Prefer `torch.inference_mode()` for inference-only code; `torch.no_grad()` is also valid.
- Keep deployment behavior in `forward` if it should work without a Lightning `Trainer`.
- If the model uses dropout/batch norm, call `model.eval()` unless the task deliberately needs stochastic prediction.

### `Trainer.predict`

Use `Trainer.predict` when Lightning should own batching, device transfer, accelerators, callbacks, or prediction writers.

```python
from lightning.pytorch import Trainer

class LitModel(LightningModule):
    def predict_step(self, batch, batch_idx, dataloader_idx=0):
        return self(batch)

model = LitModel.load_from_checkpoint("best_model.ckpt")
trainer = Trainer(accelerator="auto", devices="auto")
predictions = trainer.predict(model, dataloaders=predict_loader)
```

Operational details:

- `predict_step(self, batch, batch_idx, dataloader_idx=0)` is the safe signature when multiple dataloaders may be used.
- With one dataloader, `predict_step(self, batch)` or `predict_step(self, batch, batch_idx)` can work, but the explicit form is easier to maintain.
- With multiple dataloaders, include `dataloader_idx`; Lightning raises a runtime error if the hook signature cannot accept it.
- Use `return_predictions=False` with a `BasePredictionWriter` when predictions are large or distributed, so each rank writes its own shard.
- Prediction callbacks such as `on_predict_batch_start` and `on_predict_batch_end` follow the same `dataloader_idx` signature rule as `predict_step`.

### Prediction writers

For distributed or large-output inference, use `BasePredictionWriter` instead of returning every tensor to the main process.

```python
import os
import torch
from lightning.pytorch.callbacks import BasePredictionWriter

class ShardedPredictionWriter(BasePredictionWriter):
    def __init__(self, output_dir):
        super().__init__(write_interval="epoch")
        self.output_dir = output_dir

    def write_on_epoch_end(self, trainer, pl_module, predictions, batch_indices):
        torch.save(predictions, os.path.join(self.output_dir, f"predictions_{trainer.global_rank}.pt"))
        torch.save(batch_indices, os.path.join(self.output_dir, f"batch_indices_{trainer.global_rank}.pt"))
```

Then call:

```python
trainer = Trainer(callbacks=[ShardedPredictionWriter("predictions")])
trainer.predict(model, dataloaders=predict_loader, return_predictions=False)
```

Route strategy, device count, and distributed launch debugging to `../distributed-accelerators/SKILL.md`.

## Pure PyTorch Runtime From a Lightning Checkpoint

Use pure PyTorch when production should not import Lightning. The production module must reproduce the serving-time `nn.Module` structure and remap checkpoint keys if the LightningModule wrapped the production module under a prefix.

```python
import torch
from torch import nn

class Encoder(nn.Module):
    ...

class AutoEncoderProd(nn.Module):
    def __init__(self, **hparams):
        super().__init__()
        self.encoder = Encoder(**hparams)

    def forward(self, x):
        return self.encoder(x)

checkpoint = torch.load("best_model.ckpt", map_location="cpu")
hparams = checkpoint.get("hyper_parameters", {})
model = AutoEncoderProd(**hparams)
state_dict = checkpoint["state_dict"]

for key in list(state_dict):
    if key.startswith("auto_encoder."):
        state_dict[key.removeprefix("auto_encoder.")] = state_dict.pop(key)

model.load_state_dict(state_dict)
model.eval()
```

Checklist:

- Inspect `checkpoint["state_dict"].keys()` before remapping.
- Use `map_location="cpu"` for portable checkpoint loading unless the deployment target requires a specific device.
- Load only tensors needed for inference; omit training-only modules, losses, metrics, and optimizer state from the production module.
- If key remapping is complex, create a small assertion test comparing Lightning and pure PyTorch outputs on a fixed input.

## `ServableModule` API

`ServableModule` is an experimental serving-validation surface under `lightning.pytorch.serve`. A model must subclass both `LightningModule` and `ServableModule` (or otherwise be a `LightningModule` that is also a `ServableModule`) and implement the abstract serving hooks.

```python
from typing import Any, Callable
import torch
from lightning.pytorch.serve import ServableModule

class TinyServable(LightningModule, ServableModule):
    def configure_payload(self) -> dict[str, Any]:
        return {"body": {"x": [1.0, 2.0]}}

    def configure_serialization(self) -> tuple[dict[str, Callable], dict[str, Callable]]:
        return {"x": lambda value: torch.tensor(value)}, {"output": lambda tensor: tensor.tolist()}

    def serve_step(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        return {"output": self(x)}

    def configure_response(self) -> dict[str, Any]:
        return {"output": [2.0, 4.0]}
```

Hook contract:

- `configure_payload()` must return a dict with a top-level `"body"` field.
- `configure_serialization()` returns two dictionaries: input deserializers keyed by `serve_step` argument name, and output serializers keyed by output name.
- `serve_step(*args, **kwargs)` must return a dictionary of tensors or serializable outputs after serializer processing.
- `configure_response()` is used by the validator to compare the actual server response with an expected response.

## `ServableModuleValidator`

Signature verified from the public package surface:

```python
from lightning.pytorch.serve import ServableModuleValidator

callback = ServableModuleValidator(
    optimization=None,
    server="fastapi",
    host="127.0.0.1",
    port=8080,
    timeout=20,
    exit_on_failure=True,
)
```

Current behavior to respect:

- The constructor accepts `optimization` values `"trace"`, `"script"`, `"onnx"`, and `"tensorrt"`, but current source raises `NotImplementedError` for any non-`None` optimization.
- The constructor accepts server names `"fastapi"`, `"ml_server"`, `"torchserve"`, and `"sagemaker"`, but current source raises `NotImplementedError` unless `server="fastapi"`.
- Import/constructor checks require `fastapi` and `uvicorn`; validator execution also uses `requests` to poll `/ping` and call `/serve`.
- The validator starts a local server process during `on_train_start`, validates `/ping`, posts the configured payload to `/serve`, then kills the process.
- The validator is not supported with `DeepSpeedStrategy` or `FSDPStrategy` sanity serving.

Safe usage patterns:

```python
from lightning.pytorch import Trainer
from lightning.pytorch.serve import ServableModuleValidator

serve_validator = ServableModuleValidator(port=8080, timeout=20)
trainer = Trainer(
    accelerator="cpu",
    max_epochs=1,
    limit_train_batches=2,
    limit_val_batches=0,
    callbacks=[serve_validator],
)
trainer.fit(model)
assert serve_validator.successful is True
```

For a smoke check that does not enter a full training loop, see `../scripts/servable_smoke.py --check-shape`. Use `--run-validator` only when local server dependencies are installed and a localhost port is free.

## Serving Implementation Checklist

- Keep payload shape and dtype explicit; convert JSON lists/strings to tensors in deserializers.
- Keep response shape explicit; serialize tensors to JSON-compatible values such as `list`, `float`, or `int`.
- Use `serve_step` for request-time inference and `forward` for tensor computation.
- Assert a deterministic `configure_response()` for smoke tests; avoid random weights or random input unless seeded.
- Avoid downloads, remote model registries, and long-lived service startup in bundled smoke scripts.
- For production web services beyond the validator, treat Lightning as the model implementation layer and write the actual service in the deployment framework chosen by the project.
