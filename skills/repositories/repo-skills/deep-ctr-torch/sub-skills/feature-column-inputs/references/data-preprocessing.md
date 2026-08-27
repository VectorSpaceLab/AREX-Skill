# Data preprocessing recipes for DeepCTR-Torch inputs

DeepCTR-Torch models expect already-prepared numeric arrays. Do label encoding, dense scaling, padding, and train/serve vocabulary handling before creating the model.

## End-to-end preprocessing checklist

1. Split the dataset if you need leakage-safe evaluation.
2. Fill missing categorical values with a sentinel category such as `"__MISSING__"` or `"-1"`.
3. Fill or impute dense values, then scale/bucket/log-transform them as appropriate.
4. Encode each sparse categorical field to integer ids.
5. Encode sequence tokens and pad/truncate them to each feature's `maxlen`.
6. Declare `SparseFeat`, `DenseFeat`, and `VarLenSparseFeat` columns.
7. Build `feature_names = get_feature_names(linear_feature_columns + dnn_feature_columns)`.
8. Build `model_input = {name: prepared_arrays[name] for name in feature_names}`.
9. Validate the arrays with [`../scripts/validate_feature_input.py`](../scripts/validate_feature_input.py).

## Categorical label encoding

The project examples use scikit-learn `LabelEncoder` for fixed sparse fields:

```python
from sklearn.preprocessing import LabelEncoder

for feat in sparse_features:
    encoder = LabelEncoder()
    data[feat] = encoder.fit_transform(data[feat].fillna("-1"))
```

Production-safe adjustments:

- Fit encoders on the training split, then transform validation/test/serving data with an explicit unknown-id policy.
- Keep ids contiguous and nonnegative.
- Set `vocabulary_size = max_encoded_id + 1` or larger when reserving an unknown id.
- Do not pass raw strings to `SparseFeat` in the torch version unless you pre-hash them into valid integer ids.

Typical field declaration:

```python
feature_columns = [
    SparseFeat(feat, vocabulary_size=int(data[feat].max()) + 1, embedding_dim=4)
    for feat in sparse_features
]
```

`data[feat].nunique()` is also valid when ids are guaranteed to be exactly `0..nunique-1`.

## Dense feature scaling

Dense numeric fields are passed as floating arrays. The examples normalize dense integer fields into `[0, 1]`:

```python
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler(feature_range=(0, 1))
data[dense_features] = scaler.fit_transform(data[dense_features].fillna(0))
```

Guidelines:

- Use `DenseFeat(name, 1)` for one scalar column.
- Use `DenseFeat(name, k)` only when the corresponding array is shaped `(n_samples, k)`.
- If a dense vector is split across multiple table columns, either stack it into one array matching one `DenseFeat(name, k)` or declare one `DenseFeat(col, 1)` per column.
- Scale dense features consistently between training and inference.

## Sequence and multi-value encoding

Sequence/multi-value fields must become a padded 2D integer array.

Rules when `length_name` is omitted:

- Reserve id `0` for padding.
- Encode real tokens from `1` upward.
- Use `vocabulary_size = len(token_to_id) + 1`.
- Pad with `0`, commonly at the end of the sequence (`padding='post'`).

Self-contained padding helper:

```python
import numpy as np

def pad_sequences(sequences, maxlen, value=0, padding="post", truncating="post", dtype="int32"):
    out = np.full((len(sequences), maxlen), value, dtype=dtype)
    for i, seq in enumerate(sequences):
        if truncating == "pre":
            trunc = list(seq)[-maxlen:]
        else:
            trunc = list(seq)[:maxlen]
        trunc = np.asarray(trunc, dtype=dtype)
        if padding == "pre":
            out[i, -len(trunc):] = trunc
        else:
            out[i, :len(trunc)] = trunc
    return out
```

Example:

```python
token_to_id = {}
encoded = []
for raw in data["genres"]:
    ids = []
    for token in str(raw).split("|"):
        if token not in token_to_id:
            token_to_id[token] = len(token_to_id) + 1  # 0 is padding
        ids.append(token_to_id[token])
    encoded.append(ids)

lengths = np.asarray([len(seq) for seq in encoded], dtype="int32")
maxlen = int(lengths.max())
data["genres"] = pad_sequences(encoded, maxlen=maxlen, value=0, padding="post")

varlen_columns = [
    VarLenSparseFeat(
        SparseFeat("genres", vocabulary_size=len(token_to_id) + 1, embedding_dim=4),
        maxlen=maxlen,
        combiner="mean",
    )
]
```

## Explicit length columns

Use `length_name` when a sequence's padding value cannot safely be `0`, when DIN/DIEN behavior-history code requires a shared length feature, or when you want pooling based on an explicit valid-length array.

```python
feature_columns += [
    VarLenSparseFeat(
        SparseFeat("hist_item_id", vocabulary_size=item_vocab_size, embedding_dim=8, embedding_name="item_id"),
        maxlen=50,
        combiner="mean",
        length_name="seq_length",
    )
]

prepared_arrays["hist_item_id"] = padded_hist_item_ids  # (n, 50)
prepared_arrays["seq_length"] = valid_lengths           # (n,)
```

If multiple history features share the same sequence length, they may all use the same `length_name`, as in DIN/DIEN-style item and category histories. The actual `model_input` dictionary contains the length column once.

## Multi-task labels

Inputs are shared across tasks exactly as in single-task workflows. If the target contains multiple labels, build and validate `model_input` here, then route model construction and label matrix handling to `../multitask-modeling/SKILL.md`.

The common label shape for multi-task models is `(n_samples, num_tasks)` in task order; do not mix target concerns into feature-column validation except for checking the first dimension.

## Preprocessing pitfalls to prevent

- Fitting encoders on validation/test data changes ids and breaks learned embeddings.
- Using `nunique()` for `vocabulary_size` is unsafe after reserving unknown/padding ids unless ids remain exactly `0..nunique-1`.
- Encoding valid sequence tokens as `0` with no `length_name` causes those tokens to be masked out.
- Padding sequence arrays to the wrong `maxlen` causes feature-span and tensor-width mismatches.
- Passing object/string arrays into sparse inputs causes downstream tensor conversion or embedding lookup failures.
- Declaring `DenseFeat("vec", 4)` while passing a scalar column produces a dense width mismatch.
