---
name: single-task-modeling
description: "Operate DeepCTR-Torch single-output binary classification and
  regression model workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Single-task modeling

Use this sub-skill when the user needs a **single-output** DeepCTR-Torch model for binary CTR-style classification or scalar regression.

## Owns

- Model families: `WDL`, `DeepFM`, `xDeepFM`, `AFM`, `AFN`, `AutoInt`, `DCN`, `DCNMix`, `FiBiNET`, `IFM`, `DIFM`, `MLR`, `NFM`, `ONN`, `PNN`, `CCPM`.
- Choosing a single-task model family and constructor shape.
- `compile`, `fit`, `predict`, `evaluate`, metrics, CPU/GPU `device`, callbacks, checkpointing, and save/load for single-task flows.
- Binary-to-regression workflow conversion.
- A self-contained DeepFM binary smoke helper.

## Route away

- Feature-column construction, feature names, dense/sparse/sequence input arrays, and data validation: use [`../feature-column-inputs/SKILL.md`](../feature-column-inputs/SKILL.md).
- DIN/DIEN sequence-interest models: use [`../sequence-and-interest-models/SKILL.md`](../sequence-and-interest-models/SKILL.md).
- SharedBottom, ESMM, MMOE, and PLE multi-task models: use [`../multitask-modeling/SKILL.md`](../multitask-modeling/SKILL.md).

## Operating sequence

1. Confirm the task is `binary` or `regression` and that the target is a single column.
2. Obtain valid feature columns and `model_input` dictionaries from the feature-column skill.
3. Select a model from the catalog; watch constructor exceptions for `PNN` and `MLR`.
4. Compile with one of the supported strings:
   - optimizers: `sgd`, `adam`, `adagrad`, `rmsprop`
   - losses: `binary_crossentropy`, `mse`, `mae`
   - metrics: `binary_crossentropy`, `logloss`, `auc`, `mse`, `accuracy`, `acc`
5. Train with `fit`, generate predictions with `predict`, and use `evaluate` or external sklearn metrics for final reporting.
6. Add `EarlyStopping` or `ModelCheckpoint` only after the monitored metric is present in logs.

## References

- [Model catalog](references/model-catalog.md)
- [Training and prediction workflows](references/training-and-prediction.md)
- [API reference](references/api-reference.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled helper

- [`scripts/deepfm_binary_smoke.py`](scripts/deepfm_binary_smoke.py): inline tiny DeepFM binary example with `--help`, default one-epoch CPU run, optional CUDA device, prediction shape check, and final LogLoss/AUC reporting.
