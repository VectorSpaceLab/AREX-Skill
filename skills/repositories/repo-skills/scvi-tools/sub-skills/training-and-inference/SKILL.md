---
name: training-and-inference
description: "Configure scvi-tools training, Trainer options, CPU/GPU devices,
  validation splits, dataloaders, callbacks, custom datamodules, and inference
  dataloader execution patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# training-and-inference

Use this sub-skill when a task is about running, configuring, or debugging `model.train(...)`, Lightning `Trainer` options, accelerators/devices, validation splits, minibatch loading, callbacks, custom datamodules, or passing dataloaders into inference methods.

Do not use this sub-skill for choosing the model family, setting up AnnData/MuData registries, saving/loading models, or interpreting downstream statistics. Route those to the `core-models`, `data-setup`, `model-io-and-hub`, or `downstream-analysis` sub-skills.

## Fast Routing

- Need the common `train()` arguments, `TrainerConfig`, `TrainingPlanConfig`, early stopping, checkpointing, or CPU/GPU/DDP choices: read [references/training-reference.md](references/training-reference.md).
- Need `DataSplitter`, `AnnDataLoader`, `load_sparse_tensor`, custom datamodules, or inference dataloader patterns: read [references/dataloaders.md](references/dataloaders.md).
- Need to debug CUDA absence, DDP caveats, validation split errors, tiny last batches, callback monitor failures, or custom dataloader batch-key mismatches: read [references/troubleshooting.md](references/troubleshooting.md).
- Need a portable smoke-test scaffold for a small CPU training run: run `python scripts/train_smoke_template.py --help` from this sub-skill directory.

## Minimal Training Pattern

```python
import scvi

scvi.model.SCVI.setup_anndata(adata, layer="counts", batch_key="batch")
model = scvi.model.SCVI(adata, n_latent=10)
model.train(
    max_epochs=20,
    accelerator="auto",
    devices="auto",
    train_size=0.9,
    validation_size=0.1,
    batch_size=128,
)
latent = model.get_latent_representation()
```

Keep `setup_anndata` and model construction aligned with the selected model class, then use this sub-skill to control how training and inference are executed.

## Common Decisions

- Prefer `accelerator="auto", devices="auto"` for portable code; use `accelerator="cpu", devices=1` when a machine has no compatible GPU.
- Use `plan_config`/`plan_kwargs` for optimizer and training-plan options such as `lr`, `weight_decay`, or `compile`.
- Use `trainer_config` or trainer kwargs for Lightning behavior such as `early_stopping`, `callbacks`, `logger`, `check_val_every_n_epoch`, `enable_checkpointing`, and DDP `strategy`.
- Use `datamodule=...` only for supported custom dataloaders or model classes initialized with `registry=datamodule.registry`; otherwise let `model.train()` build its default `DataSplitter`.
- For inference on custom datamodules, build the datamodule inference loader and pass it as `dataloader=...` to methods such as `get_latent_representation`, `get_elbo`, `get_marginal_ll`, or `get_normalized_expression`.
