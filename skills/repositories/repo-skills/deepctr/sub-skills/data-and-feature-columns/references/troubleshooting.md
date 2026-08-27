# DeepCTR Feature-Column Troubleshooting

Use this when a planned feature spec looks valid on paper but DeepCTR rejects it or builds an unexpected input graph.

## `SparseFeat(dtype="string")` without `use_hash=True`

### Symptom

DeepCTR raises a `ValueError` similar to:

```text
SparseFeat(name='x', dtype='string') requires use_hash=True
```

### Why it happens

The feature pipeline only hashes or table-lookups string ids after you enable `use_hash=True`. Without hashing, the embedding lookup expects integer ids.

### Fix

Choose one:

- set `use_hash=True` and keep `dtype="string"`
- or label-encode the values to integers before model input and keep `dtype` integer-like

Example fix:

```python
SparseFeat("user_id", vocabulary_size=100000, embedding_dim=8, use_hash=True, dtype="string")
```

## `0` Used as a Real Id in Padded Sequences

### Symptom

A sequence feature silently masks real values, or the history sequence looks shorter than expected.

### Why it happens

`VarLenSparseFeat` uses `0` as the default padding value. If `0` is also a real category id, DeepCTR cannot tell padding from a valid token.

### Fix

- reserve `0` for padding
- start valid ids from `1`
- if you already have zero-based ids, shift them by `+1` before padding

Good pattern:

```python
key2index[token] = len(key2index) + 1
```

## Shared `embedding_name` Has Mismatched Settings

### Symptom

DeepCTR raises a `ValueError` like:

```text
Feature columns with the same embedding_name must share the same vocabulary_size
```

### Why it happens

One shared embedding table is keyed by `embedding_name`. All features that share the name must agree on:

- `vocabulary_size`
- `embedding_dim`
- `trainable`

### Fix

Either:

- make the shared columns identical on those three settings, or
- give the field a different `embedding_name`

Common fix for candidate/history item features:

```python
SparseFeat("item_id", item_count + 1, embedding_dim=8)
VarLenSparseFeat(
    SparseFeat("hist_item_id", item_count + 1, embedding_dim=8, embedding_name="item_id"),
    maxlen=50,
)
```

If `hist_item_id` uses a larger vocabulary than `item_id`, do **not** share the table until the vocabularies are aligned.

## Missing `weight_name` or `length_name` Inputs

### Symptom

Model construction succeeds, but fitting fails with a missing-key or shape error for a sequence auxiliary field.

### Why it happens

A `VarLenSparseFeat` with `weight_name` or `length_name` adds extra required inputs.

### Fix

Add every derived input key to the model input dictionary or list:

- sequence ids: `(batch_size, maxlen)`
- `weight_name`: `(batch_size, maxlen, 1)`
- `length_name`: `(batch_size, 1)` or a length vector with one value per row

Example:

```python
model_input = {
    "hist_item_id": hist_item_id,
    "hist_weight": hist_weight,
    "seq_length": seq_length,
}
```

## Incorrect `DenseFeat.dimension`

### Symptom

The model input shape does not match the declared dense feature width.

### Why it happens

`DenseFeat("pic_vec", 5)` expects five values per sample. If the actual tensor has width 4 or 6, the input graph cannot line up.

### Fix

- set `dimension` to the true last-axis width
- reshape the data to match the declared width
- do not confuse a scalar dense field with a vector field

Good examples:

```python
DenseFeat("pay_score", 1)
DenseFeat("article_vector", 128)
```

## Confusing `maxlen` With `vocabulary_size`

### Symptom

A sequence feature builds, but the embedding table or padding width looks wrong.

### Why it happens

`maxlen` and `vocabulary_size` are different concepts:

- `maxlen` = padded sequence width
- `vocabulary_size` = embedding row count or hash bucket space

### Fix

Use `maxlen` for the input sequence length and `vocabulary_size` for the id space.

For example, a field with 18 possible genres and at most 5 genres per movie should use something like:

```python
VarLenSparseFeat(
    SparseFeat("genres", vocabulary_size=19, embedding_dim=4),
    maxlen=5,
)
```

## Missing Feature Names or Wrong Input Keys

### Symptom

`model.fit()` complains about missing input keys or the input list order is wrong.

### Why it happens

The model expects the keys returned by `get_feature_names(...)`. If you build the dictionary manually, it is easy to omit a `length_name`, `weight_name`, or shared history field.

### Fix

- always derive inputs from `get_feature_names(...)`
- include every required auxiliary key
- if you pass a list, keep the exact order from `get_feature_names(...)`

## `vocabulary_path` Lookup Looks Broken

### Symptom

A vocabulary-table feature returns unexpected `0` ids or cannot find keys.

### Why it happens

Common causes:

- the CSV key/value order is wrong
- the file path is not reachable from the current run
- the table was not initialized in a TensorFlow 1.x-style session
- the vocabulary ids do not start at `1` when `0` is reserved for padding

### Fix

- ensure the CSV uses the expected key/value columns
- run the validator with `--check-paths`
- reserve `0` for missing/padding behavior
- initialize tables when using older graph-session workflows

## Quick Recovery Checklist

1. Confirm the feature type: sparse, dense, or varlen sparse.
2. Check `dtype` against the intended encoding.
3. Verify `vocabulary_size`, `embedding_dim`, and `trainable` for shared embeddings.
4. Check `maxlen`, `length_name`, and `weight_name` shapes.
5. Regenerate `feature_names` and rebuild the input dict/list.
6. Run `scripts/validate_feature_spec.py` on the JSON feature spec before model build.
