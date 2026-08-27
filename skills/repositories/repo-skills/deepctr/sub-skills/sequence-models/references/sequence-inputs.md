# Sequence Input Conventions

This reference distills the input contracts for DeepCTR's sequence/session models: DIN, BST, DIEN, and DSIN.

## Shared rules

- Use `SparseFeat` for one categorical id per row, `DenseFeat` for scalar or dense numeric features, and `VarLenSparseFeat` for padded id sequences.
- Use `0` only as padding in sequence/session id arrays. Start valid ids from `1`.
- Share candidate/history embeddings by setting the same `embedding_name` on the paired fields.
- Keep candidate and history/session vocabulary size, embedding dimension, and trainability compatible when sharing embeddings.
- For sequence inputs, pad to a fixed `maxlen` before feeding the model.
- When a sequence feature uses `length_name`, include the corresponding length tensor in the model input.

A useful pattern is:

```python
from tensorflow.keras.preprocessing.sequence import pad_sequences
from deepctr.feature_column import SparseFeat, VarLenSparseFeat, DenseFeat, get_feature_names

# history rows are padded to the same maxlen, and 0 means padding
hist_item_id = pad_sequences([[1, 2, 3], [3, 2, 1], [1, 2]], maxlen=4, padding="post", value=0)
```

## DIN and BST

DIN and BST expect `history_feature_list` to contain the **base behavior names**, not the `hist_` names.

If the behavior list is:

```python
behavior_feature_list = ["item_id", "cate_id"]
```

then the history fields must be named:

- `hist_item_id`
- `hist_cate_id`

Example feature columns:

```python
feature_columns = [
    SparseFeat("user", user_count + 1, embedding_dim=10),
    SparseFeat("gender", gender_count + 1, embedding_dim=4),
    SparseFeat("item_id", item_count + 1, embedding_dim=8),
    SparseFeat("cate_id", cate_count + 1, embedding_dim=4),
    DenseFeat("pay_score", 1),
    VarLenSparseFeat(
        SparseFeat("hist_item_id", item_count + 1, embedding_dim=8, embedding_name="item_id"),
        maxlen=4,
        length_name="seq_length",
    ),
    VarLenSparseFeat(
        SparseFeat("hist_cate_id", cate_count + 1, embedding_dim=4, embedding_name="cate_id"),
        maxlen=4,
        length_name="seq_length",
    ),
]
```

Example input dict:

```python
x = {
    "user": np.array([0, 1, 2]),
    "gender": np.array([0, 1, 0]),
    "item_id": np.array([1, 2, 3]),
    "cate_id": np.array([1, 2, 2]),
    "hist_item_id": hist_item_id,
    "hist_cate_id": hist_cate_id,
    "pay_score": np.array([0.1, 0.2, 0.3]),
    "seq_length": np.array([3, 3, 2]),
}
```

Notes:

- DIN uses `hist_` history embeddings as attention keys and the candidate behavior features as queries.
- BST uses the same `hist_` naming, but it passes the history through a Transformer stack before attention.
- If you define `length_name="seq_length"` on the history `VarLenSparseFeat`s, keep `seq_length` in `x` even for DIN so the feature list matches the shipped recipes.

## DIEN

DIEN uses the same `hist_` naming rule as DIN/BST and also reads `seq_length` from the model inputs.

Example feature columns:

```python
feature_columns = [
    SparseFeat("user", 3, embedding_dim=10),
    SparseFeat("gender", 2, embedding_dim=4),
    SparseFeat("item", 4, embedding_dim=8, embedding_name="item"),
    SparseFeat("item_gender", 3, embedding_dim=4, embedding_name="item_gender"),
    DenseFeat("score", 1),
    VarLenSparseFeat(SparseFeat("hist_item", 4, embedding_dim=8, embedding_name="item"), maxlen=4, length_name="seq_length"),
    VarLenSparseFeat(SparseFeat("hist_item_gender", 3, embedding_dim=4, embedding_name="item_gender"), maxlen=4, length_name="seq_length"),
]
```

With negative sampling enabled, add matching negative-history fields:

```python
feature_columns += [
    VarLenSparseFeat(SparseFeat("neg_hist_item", 4, embedding_dim=8, embedding_name="item"), maxlen=4, length_name="seq_length"),
    VarLenSparseFeat(SparseFeat("neg_hist_item_gender", 3, embedding_dim=4, embedding_name="item_gender"), maxlen=4, length_name="seq_length"),
]
```

Example input additions:

```python
x["seq_length"] = np.array([3, 3, 2])
x["neg_hist_item"] = neg_hist_item
x["neg_hist_item_gender"] = neg_hist_item_gender
```

Notes:

- `use_negsampling=True` expects the `neg_hist_` tensors to line up with the positive history tensors.
- Keep the negative-history arrays padded to the same `maxlen` as the positive history.
- DIEN's heavy `AUGRU` + negative-sampling branch is best treated as reference-only unless you specifically need it.

## DSIN

DSIN does **not** split raw events into sessions inside the model. Split sessions offline, keep the most recent `sess_max_count` sessions, and pad each session to its own `maxlen`.

For `sess_feature_list = ["item", "cate_id"]` and `sess_max_count = 2`, prepare fields like:

```python
feature_columns = [
    SparseFeat("user", 3, embedding_dim=10),
    SparseFeat("gender", 2, embedding_dim=4),
    SparseFeat("item", 4, embedding_dim=4),
    SparseFeat("cate_id", 3, embedding_dim=4),
    DenseFeat("pay_score", 1),
    VarLenSparseFeat(SparseFeat("sess_0_item", 4, embedding_dim=4, embedding_name="item"), maxlen=4),
    VarLenSparseFeat(SparseFeat("sess_0_cate_id", 3, embedding_dim=4, embedding_name="cate_id"), maxlen=4),
    VarLenSparseFeat(SparseFeat("sess_1_item", 4, embedding_dim=4, embedding_name="item"), maxlen=4),
    VarLenSparseFeat(SparseFeat("sess_1_cate_id", 3, embedding_dim=4, embedding_name="cate_id"), maxlen=4),
]
```

Example input dict:

```python
x = {
    "user": np.array([0, 1, 2]),
    "gender": np.array([0, 1, 0]),
    "item": np.array([1, 2, 3]),
    "cate_id": np.array([1, 2, 2]),
    "sess_0_item": sess_0_item,
    "sess_0_cate_id": sess_0_cate_id,
    "sess_1_item": sess_1_item,
    "sess_1_cate_id": sess_1_cate_id,
    "pay_score": np.array([0.1, 0.2, 0.3]),
    "sess_length": np.array([2, 1, 0]),
}
```

Notes:

- `sess_length` is required input for DSIN.
- Session names must be `sess_<index>_<feature>` with zero-based indices.
- Share each session feature with its candidate feature using the same `embedding_name`.
- If you use `get_feature_names(feature_columns)` to build `x`, add `sess_length` manually afterward because it is not part of the feature-column list.

## Smoke-friendly shape checklist

- Candidate sparse feature: `(batch,)` or `(batch, 1)`
- History/session sequence: `(batch, maxlen)`
- Length tensor: `(batch,)` or `(batch, 1)`
- Padding value: `0`
- Valid ids: `>= 1`
