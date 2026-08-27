---
name: sequence-models
description: "Operate DeepCTR DIN, DIEN, DSIN, and BST sequence/session
  recommendation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DeepCTR Sequence Models

Use this sub-skill when a task involves DeepCTR's sequence/session recommender models: DIN, BST, DIEN, or DSIN. It is specialized for input naming, sequence/session feature construction, attention/GRU caveats, and tiny synthetic smoke checks.

DeepCTR facts to preserve in downstream work: DeepCTR is a TensorFlow/Keras CTR/recommender package imported as `deepctr`; this skill targets DeepCTR 0.9.4. TensorFlow is a separate dependency. Use public `tensorflow.keras` APIs in new code.

## Start Here

1. Read [references/sequence-inputs.md](references/sequence-inputs.md) for exact input dictionaries, `hist_`/`sess_` field names, padding, `seq_length`/`sess_length`, and embedding sharing examples.
2. Read [references/api-reference.md](references/api-reference.md) for model constructor signatures and version-sensitive parameters.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when a sequence model builds with wrong history behavior, has missing length inputs, fails on Dice/GRU/session shapes, or produces masking surprises.
4. Use [scripts/sequence_tiny_smoke.py](scripts/sequence_tiny_smoke.py) for a bundled synthetic DIN/BST/DSIN build-fit-predict smoke check that does not require external data.

## Model Selection Router

- Use **DIN** when each row has a candidate item/category and one flat padded history sequence; attention matches candidate behavior features to `hist_` history fields.
- Use **BST** when the same DIN-style `hist_` history should be processed through Transformer layers before attention; include `seq_length`.
- Use **DIEN** when the task is interest evolution over a history sequence, especially GRU variants or auxiliary negative-sampling loss; treat full DIEN training as legacy/version-sensitive.
- Use **DSIN** when history is already split into multiple sessions; the model does not split raw event streams and requires `sess_<index>_<feature>` fields plus `sess_length`.

## Boundary Routes

- For generic `SparseFeat`, `DenseFeat`, `VarLenSparseFeat`, hashing, weighted sequences, or feature validation unrelated to DIN/BST/DIEN/DSIN naming, route to `data-and-feature-columns`.
- For model `compile`, `fit`, callbacks, save/load, custom objects, prediction, and TensorFlow environment management, route to `keras-model-workflows`.
- For multitask learning and TensorFlow Estimator workflows, route to their separate DeepCTR skill areas.

## Critical Checks Before Building

- DIN/BST/DIEN: every behavior feature name in `history_feature_list` must have a matching history field named exactly `hist_` + feature name, for example `item_id` -> `hist_item_id`.
- BST and DIEN require a `seq_length` input; set `length_name="seq_length"` on history `VarLenSparseFeat` columns and include `x["seq_length"]`.
- DSIN: for every session index `0..sess_max_count-1` and every behavior feature, include `sess_<index>_<feature>` and include `x["sess_length"]`.
- Use `0` only for padding in behavior sequence/session id arrays; encode valid behavior ids from `1` upward and set `vocabulary_size >= max_id + 1`.
- Share candidate/history embeddings with `embedding_name`, for example `SparseFeat("hist_item_id", ..., embedding_name="item_id")`, and keep shared vocabulary size, embedding dimension, and trainability compatible.
- On newer TensorFlow versions, prefer `att_activation="sigmoid"` for DIN/DIEN smoke/debug runs; `dice` is the DeepCTR default but more version-sensitive.
