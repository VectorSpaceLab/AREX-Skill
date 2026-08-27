---
name: multimodal-physics
description: "Repository operating skill for Flow Forecast catchment embeddings,
  multimodal fusion, NeuralODE/GR4 hydrology, and related physics-aware
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Multimodal Physics

Use this sub-skill when a Flow Forecast task involves catchment embeddings, contrastive pretraining, CrossViViT, meta-data fusion, NeuralODE, GR4 hydrology, or hybrid physics-aware forecasting.

Start with:

- [../../references/model-overview.md](../../references/model-overview.md) for the package-wide registry when you need the exact multimodal or hydrology model name.
- [references/api-reference.md](references/api-reference.md) for the multimodal and hydrology class/function map.
- [references/workflows.md](references/workflows.md) for the catchment-embedding, pretraining, and hybrid-forecast recipes.
- [references/troubleshooting.md](references/troubleshooting.md) for the common shape, dependency, and solver failures.
- [scripts/synthetic_catchment_smoke.py](scripts/synthetic_catchment_smoke.py) for a tiny CPU-safe smoke that builds synthetic `.npz` records and runs the core multimodal pipeline.

## What This Sub-skill Covers

- `CatchmentEmbeddingDataset`, `CatchmentEncoder`, `pretrain_catchment_encoder`, and `extract_embeddings`.
- `MergingModel`, `GatedFusion`, and other meta-data fusion helpers.
- `RoCrossViViT` and the vision/time-series multimodal transformer path.
- `NeuralODE`, `ODEForecast`, `GR4Dynamics`, `GR4ParameterHead`, `EffectiveForcingGenerator`, and `HybridGR4Model`.
- `InfoNCELoss`, `NSELoss`, and `MaskedMSELoss` where they matter for contrastive, hydrology, or sparse-supervision workflows.

## What Belongs Elsewhere

- Plain tabular data preparation belongs in [data-preparation](../data-preparation/SKILL.md).
- Generic model training and checkpoints belong in [training](../training/SKILL.md).
- Saved-model rollout and plots belong in [inference](../inference/SKILL.md).

## Typical Workflow

1. Build the catchment `.npz` records or another multimodal fixture.
2. Validate the feature dimensions and patch sizes.
3. Pretrain the catchment encoder with `InfoNCELoss` if you need a context representation.
4. Extract embeddings and feed them into the hydrology or fusion model.
5. For hybrid hydrology, validate the forcing shape and ODE time grid before launch.

## Operating Notes

1. `CatchmentEmbeddingDataset` returns `image`, `static`, `history`, and `site_index` tensors; the history channel includes standardized log-flow and an observed mask.
2. `CatchmentEncoder` supports `fusion="concat"` and `fusion="cross_attention"` only.
3. `HybridGR4Model` uses `context_dim` to match the catchment embedding dimension and `encoder_type="transformer"` or `"crossformer"` for the forcing generator backbone.
4. `GR4Dynamics` expects forcing tensors with two channels: precipitation and potential evapotranspiration.
5. `torchdiffeq`, `einops`, and `jaxtyping` are required for the selected multimodal and hydrology paths.

## Shared References And Scripts

- [references/api-reference.md](references/api-reference.md): class/function map and key input/output shapes.
- [references/workflows.md](references/workflows.md): dataset construction, pretraining, embedding extraction, and hybrid hydrology recipes.
- [references/troubleshooting.md](references/troubleshooting.md): missing dependencies, invalid patch sizes, forcing/solver errors, and shape mismatches.
- [scripts/synthetic_catchment_smoke.py](scripts/synthetic_catchment_smoke.py): tiny synthetic `.npz` smoke check.

## Non-goals

- Do not require access to external geospatial datasets by default.
- Do not assume GPU availability for the smoke path.
- Do not depend on the original repository checkout for runtime instructions.
