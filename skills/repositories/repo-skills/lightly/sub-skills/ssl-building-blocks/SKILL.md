---
name: ssl-building-blocks
description: "Assemble Lightly low-level SSL data, transform, loss, head, and
  memory-bank components."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SSL Building Blocks

Use this sub-skill when a task asks how to compose LightlySSL's low-level pieces without committing to a full CLI or training recipe. It is the right route for API signatures, transform/loss/head selection, tensor shapes, optional component availability, and no-download component smoke tests.

## Use this sub-skill for

- `lightly.data.LightlyDataset`, `LightlyDataset.from_torch_dataset`, image/video dataset behavior, and collate functions.
- Method transforms such as SimCLR, BYOL, SimSiam, MoCo, DINO, SwaV, VICReg, MAE, MSN, iBOT, CAPI, LeJEPA, Pixio, and related families.
- SSL losses, projection/prediction heads, prototypes, and memory banks.
- Deprecated high-level model wrappers only as compatibility references; prefer low-level modules for new workflows.
- Optional `lightly[timm]` and `lightly[video]` branches when a task explicitly needs TIMM/ViT modules or direct video-file datasets.
- Tensor-only smoke checks that should not download datasets, run notebooks, or start long training.

## Route elsewhere for

- Full training loops, PyTorch Lightning recipes, local-folder training plans, or distributed training decisions: use `training-workflows`.
- CLI/Hydra/data-folder/crop/embedding commands: use `cli-data-embedding`.
- KNN/linear evaluation, benchmark utilities, repository tests, docs, notebooks, or maintainer checks: use `evaluation-maintenance`.

## First actions

1. Identify the method family and output arity: two-view, multi-crop/multi-view, masked-image, dense/local, or clustering/prototype.
2. Read [Method map](references/method-map.md) to choose compatible transforms, collates, heads, losses, and optional dependencies.
3. Confirm signatures and tensor contracts in [API reference](references/api-reference.md), especially `input_dim`, output feature width, `gather_distributed`, memory-bank shape, and optional TIMM/video availability.
4. Run [Smoke script](scripts/smoke_ssl_components.py) on CPU before moving to real data or a full training loop.
5. If the smoke fails, read [Troubleshooting](references/troubleshooting.md) and fix shape/arity/optional-extra issues before routing to `training-workflows`.

## Common decisions

- Prefer `SimCLRTransform` + `SimCLRProjectionHead` + `NTXentLoss` for simple contrastive smoke checks.
- Use DINO/SwaV/MSN/iBOT transforms or collates only when the downstream code expects a list of global/local crops.
- Set projection-head `input_dim` to the actual backbone feature width; do not force the loss to compensate for mismatched dimensions.
- Set `gather_distributed=True` only inside an initialized distributed process group.
- Install `lightly[timm]` or `lightly[video]` only for workflows that need those optional branches; base `pip install lightly` is enough for most CPU component checks.

## Install reminder

- Base package: `pip install lightly`
- Optional TIMM/ViT modules: `pip install "lightly[timm]"`
- Optional direct video support: `pip install "lightly[video]"`
