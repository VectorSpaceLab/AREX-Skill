# Troubleshooting feature columns and model inputs

Use this reference when validation fails before model construction, or when DeepCTR-Torch raises an input/key/shape error during `fit`, `predict`, or `evaluate`.

## Quick triage

Run the bundled validator on a minimal spec first:

```bash
python scripts/validate_feature_input.py
python scripts/validate_feature_input.py --spec feature_input_spec.json
```

Then check the exact symptom below.

## Common symptoms and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| `KeyError: '<feature>'` or missing key in `model_input` | `get_feature_names(...)` includes a feature name or `length_name` that is not present in `model_input`. | Build `feature_names = get_feature_names(linear_feature_columns + dnn_feature_columns)` and populate every key. For `VarLenSparseFeat(..., length_name='seq_length')`, include `model_input['seq_length']`. |
| A feature disappears from `feature_names` | Duplicate feature names are silently collapsed by `get_feature_names`. | Keep duplicate names only when reusing the same feature in linear and DNN parts. Rename accidental duplicates such as scalar/vector fields that share a name. |
| `IndexError: index out of range in self` from an embedding lookup | A sparse id or sequence id is `< 0` or `>= vocabulary_size`; or shared `embedding_name` columns use inconsistent vocab sizes. | Recompute `vocabulary_size = max_id + 1` after encoding, reserve unknown/padding ids deliberately, and keep shared embedding columns consistent. |
| Tensor conversion error for sparse inputs | Sparse values are strings, objects, floats with non-integer values, or contain missing values. | Fill missing values, label-encode/pre-hash to nonnegative integer ids, and validate integer arrays before model construction. |
| Dense input has wrong width | `DenseFeat(name, dimension=k)` does not match the array shape. | Pass `(n,)` or `(n, 1)` for `dimension=1`; pass `(n, k)` for `dimension=k>1`. Split or stack source columns to match the declaration. |
| `ValueError: parameter mode should in [sum, mean, max]` | `VarLenSparseFeat.combiner` is not one of the supported pooling modes. | Use `combiner='sum'`, `'mean'`, or `'max'`. |
| Sequence pooling ignores real token id `0` | `length_name` is omitted, so DeepCTR-Torch uses `sequence_values != 0` as the mask. | Reserve `0` only for padding and start real sequence token ids at `1`, or provide an explicit `length_name`. |
| Nonzero padding affects sequence pooling | `length_name` is omitted but padding positions contain nonzero ids. | Pad with `0`, or add `length_name` and a valid length array so pooling uses explicit lengths. |
| VarLen width mismatch | The sequence array width is not equal to `maxlen`. | Pad or truncate every sequence to exactly `maxlen`, and declare `VarLenSparseFeat(..., maxlen=<that width>)`. |
| Missing or invalid sequence length array | `length_name` is declared but `model_input[length_name]` is absent, has the wrong batch size, or contains values outside `0..maxlen`. | Add the length key once; shape it as `(n,)` or `(n, 1)`; clip/check integer lengths. |
| `please add max length column for VarLenSparseFeat of DIN/DIEN input` | DIN/DIEN-specific code needs a max/length column for behavior-history handling. | Add the required `length_name` feature and route behavior-history setup to `../sequence-and-interest-models/SKILL.md`. |
| Constructor prints `Notice! Feature Hashing on the fly currently is not supported in torch version...` | `SparseFeat(use_hash=True)` was used. | Do not rely on torch-side hashing. Pre-hash raw categories outside DeepCTR-Torch into integer ids, set `use_hash=False`, and set `vocabulary_size` to the hash bucket count. |
| Model input arrays have inconsistent first dimension | Some features were sliced, padded, or split differently. | Assert every `model_input` value has the same `n_samples` before calling `fit`/`predict`; align target rows to the same order. |

## Duplicate names: what is safe?

Safe:

```python
linear_feature_columns = feature_columns
dnn_feature_columns = feature_columns
feature_names = get_feature_names(linear_feature_columns + dnn_feature_columns)
```

This produces one input key per feature, even though the feature columns appear in two model parts.

Unsafe:

```python
DenseFeat("profile", 1)
DenseFeat("profile", 8)  # silently ignored by feature-name construction
```

The later duplicate does not create a second input span, so the model and `model_input` no longer describe the same data. Rename the vector field, for example `profile_vec`.

## Shared `embedding_name` mistakes

When sharing embeddings, the feature input key and embedding table key are different concepts:

```python
SparseFeat("item_id", vocabulary_size=item_vocab_size, embedding_dim=8)
VarLenSparseFeat(
    SparseFeat("hist_item_id", vocabulary_size=item_vocab_size, embedding_dim=8, embedding_name="item_id"),
    maxlen=50,
    length_name="seq_length",
)
```

Required keys in `model_input` are `item_id`, `hist_item_id`, and `seq_length`. There is no separate `model_input['embedding_name']` key.

Fixes for shared-embedding errors:

- Match `vocabulary_size` across columns using the same `embedding_name`.
- Match `embedding_dim` across columns using the same `embedding_name`.
- Keep id spaces aligned; `hist_item_id` ids must refer to the same item vocabulary as `item_id`.
- If fields do not share a vocabulary, do not share `embedding_name`.

## Dense vector plus shared embeddings difficult case

If a workflow combines shared sparse embeddings with a dense vector, validate both independently:

```python
feature_columns = [
    SparseFeat("item_id", 1000, embedding_dim=8),
    VarLenSparseFeat(SparseFeat("hist_item_id", 1000, embedding_dim=8, embedding_name="item_id"), maxlen=5),
    DenseFeat("profile_vec", dimension=4),
]
```

Expected inputs:

- `item_id`: `(n,)` integer ids in `0..999`.
- `hist_item_id`: `(n, 5)` integer ids in `0..999`; if `length_name` is absent, padding is `0`.
- `profile_vec`: `(n, 4)` finite numeric array.

If `profile_vec` is supplied as `(n,)`, fix the data shape or change `DenseFeat("profile_vec", 1)`.

## Sequence padding with nonzero mask semantics

Without `length_name`, the mask is exactly `sequence_values != 0`. This means:

- `0` means padding.
- Every nonzero value contributes to `sum`/`mean`/`max` pooling.
- A custom padding id such as `-1`, `999`, or `vocab_size` is invalid or treated as a real token.

Use an explicit length column if your upstream data cannot reserve `0` for padding:

```python
VarLenSparseFeat(
    SparseFeat("hist_item_id", vocabulary_size=item_vocab_size, embedding_dim=8),
    maxlen=5,
    combiner="mean",
    length_name="hist_item_len",
)
model_input["hist_item_len"] = np.asarray([3, 2, 5], dtype="int32")
```

Padding positions still need in-range ids because the embedding lookup runs before pooling.

## When to route elsewhere

- After feature-input validation passes and the question is about DeepFM/WDL/DCN/xDeepFM/PNN/etc., route to `../single-task-modeling/SKILL.md`.
- If `VarLenSparseFeat` columns represent behavior history for DIN/DIEN, route sequence-pair naming and model construction to `../sequence-and-interest-models/SKILL.md`.
- If one `model_input` feeds multiple labels/tasks, route task-specific labels, losses, and prediction interpretation to `../multitask-modeling/SKILL.md`.
