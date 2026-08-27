# Lightning Package Overview

## Public Package Surfaces

Lightning exposes two primary user-facing surfaces:

- `lightning.pytorch`: high-level PyTorch Lightning APIs such as `Trainer`, `LightningModule`, `LightningDataModule`, callbacks, loggers, profilers, strategies, CLI, and serving utilities.
- `lightning.fabric`: expert-control APIs centered on `Fabric` for wrapping existing PyTorch loops with device, precision, distributed, logging, and checkpoint helpers.

For new code, prefer:

```python
import lightning as L
import lightning.pytorch as pl
from lightning.fabric import Fabric
```

Legacy projects may import `pytorch_lightning`. Treat that namespace as compatibility-oriented; migrate only when the user asks or when a new-code example is being authored.

## Install Variants

Use the smallest install that matches the task:

```bash
pip install lightning
pip install "lightning[pytorch-extra]"        # broad PyTorch extras, includes CLI-adjacent deps
pip install "jsonargparse[signatures]"       # focused LightningCLI support
pip install pytorch-lightning                 # legacy compatibility package
pip install lightning-fabric                  # standalone Fabric-style install when used separately
```

Avoid broad dev/test/docs/example requirements for normal agent tasks. Optional strategy, logger, serving, cloud, and hardware dependencies should be installed only when the selected workflow needs them.

## Major Runtime Objects

- `Trainer`: owns train/validate/test/predict loops, accelerator/strategy/precision, logging, callbacks, checkpointing, and loop limits.
- `LightningModule`: organizes model, step hooks, logging, optimizer/scheduler configuration, and checkpoint loading.
- `LightningDataModule`: organizes data preparation, setup, and dataloaders.
- `Fabric`: wraps manual PyTorch loops with setup/backward/device/precision/distributed/checkpoint helpers.
- `LightningCLI`: constructs model, datamodule, and trainer from command-line, YAML, and environment configuration.
- `ServableModule` and `ServableModuleValidator`: help structure and validate serving-oriented Lightning modules.

## Optional Dependency Patterns

- `LightningCLI` import or signature inspection can require `jsonargparse[signatures]`.
- Serving validation can require `requests` and server-specific packages such as FastAPI/Uvicorn, MLServer, TorchServe, or SageMaker dependencies.
- DeepSpeed, XLA/TPU, bitsandbytes, FP8/Transformer Engine, and distributed launch dependencies are optional and hardware/backend-specific.
- Logger integrations such as WandB, MLflow, Comet, and Neptune require their client packages.

## Inspection Baseline

This skill was generated from current Lightning source version `2.6.2`. Live package inspection verified `lightning`, `lightning.pytorch`, and `lightning.fabric` from the current source. Legacy `pytorch_lightning` compatibility was inspected as a compatibility surface, but public package availability can lag exact source versions.
