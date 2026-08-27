---
name: api-v2-workflows
description: "Guide experimental PyTorch Forecasting API-v2 D1/D2/M/P workflows,
  package wrappers, metadata flow, and beta troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# API-v2 Workflows Sub-skill

Use this sub-skill only when a task explicitly asks for the experimental PyTorch Forecasting API-v2 stack in `pytorch-forecasting` 1.8.0: D1 `TimeSeries`, D2 `EncoderDecoderTimeSeriesDataModule` or `TslibDataModule`, direct M-layer Lightning models, or P-layer package wrappers with `fit()`/`predict()`.

**Stability warning:** API-v2 is active-development/beta. Do not present it as the stable production interface; for production forecasting workflows route to the v1 sub-skills below.

## Route here for

- Building API-v2 `TimeSeries` datasets from pandas DataFrames and checking the metadata that flows into v2 datamodules.
- Choosing between `EncoderDecoderTimeSeriesDataModule` and `TslibDataModule`, creating `datamodule_cfg`, and validating `metadata` before model construction.
- Using direct M-layer models such as `TFT`, `DLinear`, `Samformer`, `TIDE`, `TimeXer`, `DecoderMLP_v2`, and `SOFTS` with PyTorch Lightning.
- Using P-layer wrappers such as `TFT_pkg_v2`, `DLinear_pkg_v2`, `Samformer_pkg_v2`, `TIDE_pkg_v2`, `TimeXer_pkg_v2`, `DecoderMLP_pkg_v2`, and `SOFTS_pkg_v2` with `model_cfg`, `trainer_cfg`, `datamodule_cfg`, `fit()`, `predict()`, `return_info`, and checkpoint metadata.
- Translating a v1-style request into v2 config dictionaries for beta experiments, while warning the user that v1 remains the stable path.

## Route away

- Stable production v1 data construction, `TimeSeriesDataSet`, `from_dataset()`, and `to_dataloader()` belong in `../data-pipeline/SKILL.md`.
- Stable v1 model selection, `.from_dataset()` model construction, Lightning training, checkpointing, interpretation, and prediction belong in `../forecasting-models/SKILL.md`.
- Custom model, datamodule, metric, or package-wrapper implementation belongs in `../custom-components/SKILL.md`.

## Bundled references and scripts

- Use [`references/api-v2-layered-workflows.md`](references/api-v2-layered-workflows.md) when you need the D1/D2/M-layer concepts, `TimeSeries` and datamodule recipes, metadata keys, direct Lightning model construction, and v1-to-v2 translation guidance.
- Use [`references/v2-package-reference.md`](references/v2-package-reference.md) when you need the P-layer config-driven `fit()`/`predict()` workflow, model/package names, compatibility table, checkpoint behavior, and `return_info` usage.
- Use [`references/troubleshooting.md`](references/troubleshooting.md) when beta API behavior fails due to missing metadata, incompatible datamodule/model pairing, config key mistakes, short series, fragile `return_info`, or package-layer lifecycle mistakes.
- Use [`scripts/tiny_v2_data_smoke.py`](scripts/tiny_v2_data_smoke.py) to create a synthetic DataFrame, instantiate API-v2 `TimeSeries`, and optionally build/setup an API-v2 datamodule without training any model.

## Minimal beta workflow choice

1. If the user needs stable forecasting, route away to v1.
2. If the user wants quick API-v2 experimentation, prefer a P-layer package wrapper and three config dictionaries.
3. If the user needs custom Trainer/callbacks or direct batch inspection, use the D1 + D2 + M-layer recipe and pass `metadata=data_module.metadata` into the model.
4. Always validate D1/D2 metadata before model construction; most v2 failures come from missing metadata keys or pairing a model with the wrong datamodule family.
