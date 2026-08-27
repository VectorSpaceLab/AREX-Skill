---
name: data-and-feature-columns
description: "Use this DeepCTR sub-skill for SparseFeat, DenseFeat,
  VarLenSparseFeat, hashing, embedding sharing, input dictionaries, and tabular
  or sequence feature-column validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data and Feature Columns

Use this sub-skill when the task is about preparing DeepCTR inputs before a model is chosen or trained: categorical ids, dense numerical vectors, variable-length sequences, feature hashing, vocabulary files, shared embeddings, and `get_feature_names`.

## When to use this sub-skill

- The user asks how to create `SparseFeat`, `DenseFeat`, or `VarLenSparseFeat` objects.
- The user has a tabular CTR/recommender dataset and needs model input dictionaries.
- The user is debugging missing input keys, bad shapes, string categorical values, sequence padding, `length_name`, `weight_name`, or shared embedding errors.
- The user wants to validate a feature-column plan before routing to Keras, sequence, multitask, or Estimator workflows.

## Route map

- Read [references/feature-columns.md](references/feature-columns.md) for constructor signatures, hashing, vocabulary files, embedding sharing, groups, and `get_feature_names`.
- Read [references/data-formats.md](references/data-formats.md) for tabular CTR, multi-value MovieLens-style features, DIN/BST history fields, and DSIN session fields.
- Read [references/troubleshooting.md](references/troubleshooting.md) when an error mentions `use_hash=True`, missing feature names, shape mismatch, padding id `0`, or incompatible shared embeddings.
- Run [scripts/validate_feature_spec.py](scripts/validate_feature_spec.py) when the user can express the intended features as a small JSON spec and wants preflight validation.

## Minimal workflow

1. List every raw feature and classify it as one categorical id, a dense scalar/vector, or a variable-length list of categorical ids.
2. Encode one-id categorical fields as integers and use `SparseFeat`, or set `use_hash=True` with `dtype="string"` when hashing string values on the fly.
3. Use `DenseFeat(name, dimension)` for dense vectors; make each input array shape match the declared dimension.
4. Use `VarLenSparseFeat(SparseFeat(...), maxlen=...)` for multi-value or sequence ids. Pad every row to `(batch_size, maxlen)`.
5. Keep `0` reserved for padding when a sequence field relies on masking instead of an explicit `length_name`.
6. Use the same `embedding_name` only when fields truly share one embedding table and have the same vocabulary size, embedding dimension, and trainability.
7. Call `get_feature_names(linear_feature_columns + dnn_feature_columns)` and build `model_input = {name: array for name in feature_names}`.
8. Route to:
   - [../keras-model-workflows/SKILL.md](../keras-model-workflows/SKILL.md) for ordinary Keras CTR/regression models.
   - [../sequence-models/SKILL.md](../sequence-models/SKILL.md) for DIN, DIEN, DSIN, or BST history/session fields.
   - [../multitask-models/SKILL.md](../multitask-models/SKILL.md) for multi-output labels.
   - [../estimator-workflows/SKILL.md](../estimator-workflows/SKILL.md) for TensorFlow `tf.feature_column` Estimator workflows.

## JSON validation helper

For a quick preflight, create a JSON file like:

```json
{
  "features": [
    {"type": "SparseFeat", "name": "item_id", "vocabulary_size": 1001, "embedding_dim": 8},
    {"type": "DenseFeat", "name": "score", "dimension": 1},
    {
      "type": "VarLenSparseFeat",
      "name": "hist_item_id",
      "maxlen": 4,
      "length_name": "seq_length",
      "sparsefeat": {"name": "hist_item_id", "vocabulary_size": 1001, "embedding_dim": 8, "embedding_name": "item_id"}
    }
  ]
}
```

Then run:

```bash
python sub-skills/data-and-feature-columns/scripts/validate_feature_spec.py feature_spec.json
```

The helper catches common structural mistakes; it does not replace a real TensorFlow model smoke test.

## Guardrails

- Do not use `dtype="string"` on `SparseFeat` or `VarLenSparseFeat` unless `use_hash=True` or values are pre-encoded.
- Do not set `maxlen` to the vocabulary size; `maxlen` is the number of ids in one row's list.
- Do not use `0` as a real category id for padded sequence features unless using an explicit length convention that still keeps masking consistent.
- Do not tell future agents to run source repository examples. Use this skill's bundled references and scripts, then route to the owning workflow sub-skill.
