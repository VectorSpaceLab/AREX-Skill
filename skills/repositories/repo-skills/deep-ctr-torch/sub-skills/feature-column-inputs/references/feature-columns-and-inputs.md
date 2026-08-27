# Feature columns and model inputs

This reference gives the DeepCTR-Torch input contract that future agents should use without reopening examples or source files.

## Constructors and helper

| API | Exact signature | Use |
|---|---|---|
| `SparseFeat` | `SparseFeat(name, vocabulary_size, embedding_dim=4, use_hash=False, dtype='int32', embedding_name=None, group_name='default_group')` | A fixed-length categorical id field backed by an embedding table. |
| `DenseFeat` | `DenseFeat(name, dimension=1, dtype='float32')` | A fixed-length dense numeric scalar/vector concatenated into DNN inputs. |
| `VarLenSparseFeat` | `VarLenSparseFeat(sparsefeat, maxlen, combiner='mean', length_name=None)` | A padded sequence/multi-value categorical field, pooled with `sum`, `mean`, or `max`. |
| `get_feature_names` | `get_feature_names(feature_columns)` | Returns the ordered unique input names required in `model_input`; includes `length_name` columns when present. |

Important behavior:

- `SparseFeat.embedding_name` defaults to `name`.
- `SparseFeat.embedding_dim='auto'` is accepted and converted to `6 * int(vocabulary_size ** 0.25)`.
- `SparseFeat(use_hash=True)` prints a notice; on-the-fly hashing is not implemented in the torch version. Pre-hash or label-encode outside DeepCTR-Torch instead.
- `get_feature_names(linear_feature_columns + dnn_feature_columns)` collapses duplicate feature names by keeping the first occurrence. This is normal when the same feature list is used for both linear and DNN parts, but dangerous when different fields accidentally share one name.

## Minimal fixed-length pattern

```python
from deepctr_torch.inputs import SparseFeat, DenseFeat, get_feature_names

sparse_features = ["user_id", "item_id"]
dense_features = ["price_norm", "profile_vec"]

feature_columns = [
    SparseFeat("user_id", vocabulary_size=10000, embedding_dim=8),
    SparseFeat("item_id", vocabulary_size=50000, embedding_dim=16),
    DenseFeat("price_norm", dimension=1),
    DenseFeat("profile_vec", dimension=3),
]

linear_feature_columns = feature_columns
dnn_feature_columns = feature_columns
feature_names = get_feature_names(linear_feature_columns + dnn_feature_columns)
model_input = {name: data[name] for name in feature_names}
```

Route `feature_columns`, `linear_feature_columns`, `dnn_feature_columns`, `model_input`, and targets to the appropriate modeling sub-skill after validating input arrays.

## `model_input` shape contract

Every `model_input` value must be batch-major, with the same first dimension.

| Feature type | Expected array shape | Value constraints |
|---|---|---|
| `SparseFeat(name, vocabulary_size, ...)` | `(n_samples,)` or `(n_samples, 1)` | Integer ids `0 <= id < vocabulary_size`. For ordinary sparse fields, `0` may be a valid category id. |
| `DenseFeat(name, dimension=1)` | `(n_samples,)` or `(n_samples, 1)` | Numeric finite scalar values, usually scaled or bucketed. |
| `DenseFeat(name, dimension=k)` where `k > 1` | `(n_samples, k)` | Numeric finite vectors. A flat `(n_samples,)` array is a width mismatch. |
| `VarLenSparseFeat(SparseFeat(name, vocabulary_size, ...), maxlen=m, length_name=None)` | `(n_samples, m)` | Integer ids `0 <= id < vocabulary_size`; `0` is padding and valid tokens should start at `1` when mask semantics matter. |
| `VarLenSparseFeat(..., maxlen=m, length_name='seq_length')` | sequence: `(n_samples, m)` plus `seq_length`: `(n_samples,)` or `(n_samples, 1)` | Sequence ids remain in range; length values must be integers in `0..m` (use positive lengths for standard training unless intentionally representing an empty sequence). |

DeepCTR-Torch internally builds one wide input tensor by ordered feature spans:

- `SparseFeat` reserves one position.
- `DenseFeat(dimension=k)` reserves `k` positions.
- `VarLenSparseFeat(maxlen=m)` reserves `m` positions, then reserves one additional position for `length_name` if provided and not already present.

## Sparse categorical feature design

Use label encoding or controlled offline hashing before passing data to DeepCTR-Torch.

Rules:

1. Convert each categorical field to integer ids.
2. Set `vocabulary_size` to at least `max_id + 1` for that field.
3. Keep negative ids out of input arrays.
4. Reserve an unknown id when serving data can contain categories unseen during training.
5. For sequence fields without `length_name`, reserve id `0` for padding and encode real tokens from `1` upward.

Example:

```python
user_fc = SparseFeat("user_id", vocabulary_size=max_user_id + 1, embedding_dim=8)
```

## Dense feature design

Use `DenseFeat` for numeric scalars or fixed-width vectors.

- Scalar dense feature: `DenseFeat("duration_norm", 1)` with values shaped `(n,)` or `(n, 1)`.
- Vector dense feature: `DenseFeat("profile_vec", 4)` with values shaped `(n, 4)`.
- Scale or bucket dense values before training; the project examples use min-max scaling for continuous integer fields.
- If a dense vector is stored as multiple DataFrame columns, assemble it into one `(n, dimension)` array before using a single `DenseFeat`, or declare each column as a separate `DenseFeat(..., 1)`.

## Sequence and multi-value feature design

General sequence/multi-value columns use `VarLenSparseFeat`:

```python
hist_item_fc = VarLenSparseFeat(
    SparseFeat("hist_item_id", vocabulary_size=item_vocab_size, embedding_dim=8),
    maxlen=50,
    combiner="mean",
)
```

When `length_name` is omitted:

- `0` is padding.
- DeepCTR-Torch builds a mask with `sequence_values != 0`.
- Nonzero padding is treated as a valid token, not padding.
- Valid sequence token ids should start at `1` if `0` is reserved for padding.

When `length_name` is supplied:

```python
hist_item_fc = VarLenSparseFeat(
    SparseFeat("hist_item_id", vocabulary_size=item_vocab_size, embedding_dim=8),
    maxlen=50,
    combiner="mean",
    length_name="hist_item_len",
)
model_input["hist_item_id"] = padded_hist_item_ids       # shape (n, 50)
model_input["hist_item_len"] = valid_lengths             # shape (n,) or (n, 1)
```

- Pooling uses the explicit length instead of `values != 0` masking.
- Padding positions still must contain in-range ids because the embedding lookup runs before pooling.
- DIN/DIEN behavior-history workflows use the same `VarLenSparseFeat` input contract but also require a behavior feature list and candidate/history naming conventions; route those workflows to `../sequence-and-interest-models/SKILL.md`.

## Shared embeddings and groups

`embedding_name` controls the embedding table key. Use it deliberately when multiple feature columns should share one embedding table, such as candidate item ids and item history ids:

```python
SparseFeat("item_id", vocabulary_size=item_vocab_size, embedding_dim=8)
VarLenSparseFeat(
    SparseFeat("hist_item_id", vocabulary_size=item_vocab_size, embedding_dim=8, embedding_name="item_id"),
    maxlen=50,
    length_name="seq_length",
)
```

Safety rules:

- All columns sharing an `embedding_name` should use the same `vocabulary_size` and `embedding_dim`.
- Do not use `embedding_name` to merge unrelated categorical fields.
- `group_name` defaults to `default_group`; change it only when the target model or interaction layer uses separate feature groups.
- `embedding_name` does not change the `model_input` key. The input key remains the feature `name` (`hist_item_id` in the example).

## Duplicate names and `get_feature_names`

`get_feature_names` calls the feature-span builder and returns ordered unique names. If a name appears twice, the later duplicate is skipped.

Safe duplicate case:

```python
feature_names = get_feature_names(linear_feature_columns + dnn_feature_columns)
```

This intentionally deduplicates the same feature list reused by both model parts.

Unsafe duplicate cases:

- A scalar `DenseFeat("age", 1)` and a vector `DenseFeat("age", 4)` in the same effective feature set.
- A `SparseFeat("item_id", ...)` and `VarLenSparseFeat(SparseFeat("item_id", ...), ...)` that are meant to be different inputs.
- Two different categorical fields accidentally renamed to the same string.

Fix unsafe duplicates by renaming one feature and rebuilding both feature columns and `model_input`.

## Validation before model construction

Before constructing a model, assert:

1. `feature_names = get_feature_names(linear_feature_columns + dnn_feature_columns)` is the exact set of keys in `model_input`, except for deliberately ignored extras.
2. No accidental duplicate feature names exist in the effective feature set.
3. Every value has the same batch size.
4. Sparse ids are integer and in vocabulary range.
5. Dense arrays have the declared `dimension`.
6. VarLen arrays have width `maxlen` and valid padding or valid `length_name` arrays.
7. Shared `embedding_name` groups use consistent vocabulary sizes and embedding dims.

Use [`../scripts/validate_feature_input.py`](../scripts/validate_feature_input.py) as a self-contained check for these conditions.
