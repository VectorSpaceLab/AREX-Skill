---
name: feature-column-inputs
description: "Build and validate DeepCTR-Torch feature columns and model_input
  dictionaries from tabular CTR, recommender, dense, sparse, and sequence data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# feature-column-inputs

Use this sub-skill when an agent must turn raw tabular CTR/recommender data into DeepCTR-Torch feature-column lists and the `model_input` dictionary consumed by model constructors, `fit`, `predict`, and `evaluate`.

## What this sub-skill owns

- Choosing and declaring `SparseFeat`, `DenseFeat`, and `VarLenSparseFeat` columns.
- Building `linear_feature_columns`, `dnn_feature_columns`, and `feature_names = get_feature_names(...)`.
- Preparing sparse categorical ids, dense numeric arrays, sequence/multi-value arrays, and optional sequence length columns.
- Validating names, batch sizes, sparse id ranges, dense vector widths, sequence max lengths, padding, `length_name`, shared `embedding_name`, and `group_name` usage before model construction.
- Explaining common input/feature-column errors and safe fixes.

## Route away

- Model-family choice, compile/fit/predict loops, metrics, callbacks, save/load, and single-output training belong in `../single-task-modeling/SKILL.md`.
- DIN/DIEN behavior histories, `behavior_feature_list`, attention, GRU options, and negative sampling belong in `../sequence-and-interest-models/SKILL.md`; use this sub-skill only for the underlying `VarLenSparseFeat` input contract.
- Shared inputs for multi-output labels can be built here, but MTL constructors, task names/types, target matrix shape, losses, and prediction interpretation belong in `../multitask-modeling/SKILL.md`.

## Operating sequence

1. Inventory columns by semantic type: categorical sparse ids, dense numeric/scaled vectors, sequence or multi-value categorical histories, and labels.
2. Preprocess categorical data into integer ids; reserve id `0` for padding when a sequence uses mask-based pooling without `length_name`.
3. Declare feature columns using the exact constructor signatures and shape rules in [feature-columns-and-inputs](references/feature-columns-and-inputs.md).
4. Build `feature_names = get_feature_names(linear_feature_columns + dnn_feature_columns)` and then `model_input = {name: data[name] for name in feature_names}`.
5. Run the bundled validator before constructing the model:

   ```bash
   python scripts/validate_feature_input.py
   python scripts/validate_feature_input.py --spec feature_input_spec.json
   ```

6. If validation fails, resolve the matching symptom in [troubleshooting](references/troubleshooting.md) before routing to a modeling sub-skill.

## References and helper

- [Feature columns and model inputs](references/feature-columns-and-inputs.md)
- [Data preprocessing recipes](references/data-preprocessing.md)
- [Troubleshooting feature inputs](references/troubleshooting.md)
- [Self-contained feature-input validator](scripts/validate_feature_input.py)
