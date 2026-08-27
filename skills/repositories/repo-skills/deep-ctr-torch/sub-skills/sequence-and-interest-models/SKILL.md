---
name: sequence-and-interest-models
description: "Use DeepCTR-Torch DIN/DIEN and VarLenSparseFeat sequence workflows
  for behavior-history CTR inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Sequence and interest models

Use this sub-skill for DeepCTR-Torch workflows that model behavior histories or multi-value sequence features, especially `DIN`, `DIEN`, and `VarLenSparseFeat` inputs whose rows contain padded item/category histories.

## Route by task

| User task | Load |
| --- | --- |
| Build or debug a DIN/DIEN behavior-history model | [references/din-dien-workflows.md](references/din-dien-workflows.md) |
| Check sequence array shapes, padding, `length_name`, or masks | [references/sequence-feature-shapes.md](references/sequence-feature-shapes.md) |
| Look up DIN/DIEN, sequence-pooling, attention, or feature-column parameters | [references/api-reference.md](references/api-reference.md) |
| Diagnose behavior-list, embedding, sequence length, negative sampling, hash, or short-sequence failures | [references/troubleshooting.md](references/troubleshooting.md) |
| Run a tiny DIN behavior-history smoke | [scripts/din_sequence_smoke.py](scripts/din_sequence_smoke.py) |
| Run a tiny multi-value `VarLenSparseFeat` smoke | [scripts/varlen_feature_smoke.py](scripts/varlen_feature_smoke.py) |

## Core invariants

1. `history_feature_list`/`behavior_feature_list` contains **target sparse feature names** such as `item_id` and `cate_id`, not history column names.
2. For every behavior feature `x`, provide a target `SparseFeat(name=x, ...)` and a history `VarLenSparseFeat` whose feature name is exactly `hist_` + `x`.
3. Share target/history embeddings with `embedding_name=x` on each history `SparseFeat`; do the same for DIEN negative histories.
4. DIN/DIEN behavior histories should be post-padded to the configured `maxlen` and accompanied by a `length_name` such as `seq_length`.
5. For DIEN with `use_negsampling=True`, add `neg_hist_` + `x` feature columns and model-input arrays for every behavior feature `x`.

## Boundary routing

- For general `SparseFeat`, `DenseFeat`, `VarLenSparseFeat` constructor basics and non-sequence data validation, use `feature-column-inputs`.
- For non-sequence single-output model families such as DeepFM, WDL, DCN, AutoInt, or xDeepFM, use `single-task-modeling`.
- For multi-output MTL classes, use `multitask-modeling`.
- This sub-skill does not cover custom sequence architectures beyond the package's DIN/DIEN and standard pooled `VarLenSparseFeat` workflows.
