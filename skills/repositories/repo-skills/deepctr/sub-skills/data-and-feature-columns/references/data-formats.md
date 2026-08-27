# DeepCTR Data Formats

This reference turns common DeepCTR feature-column patterns into concrete input schemas. It is focused on preparing one training row per prediction target.

## One Row Means One Target

DeepCTR models expect each sample row to describe one target instance:

- one candidate item/ad/movie/session target to score
- zero or more user/context features
- zero or more history/session fields that describe the context for that same target
- one label for that row

If the same user appears with multiple candidates, build multiple rows. Repeat or update the history fields for each candidate row.

## Tabular CTR: Criteo-Style Inputs

Criteo-style tasks usually mix many sparse categorical fields with some dense numeric fields.

Typical columns:

- sparse: `C1` ... `C26`
- dense: `I1` ... `I13`
- label: `label`

Example row layout:

| label | C1 | C2 | ... | I1 | I2 | ... |
|---|---|---|---|---|---|---|
| 1 | `a1` | `b7` | ... | 0.12 | 0.84 | ... |

Recommended preprocessing:

- fill missing sparse values before encoding
- label-encode sparse ids to integers starting at `0`, or use on-the-fly hashing for raw strings
- scale dense features to a small numeric range, such as `[0, 1]`

Feature-column sketch:

```python
feature_columns = [
    SparseFeat("C1", vocabulary_size=c1_max_id + 1, embedding_dim=4),
    SparseFeat("C2", vocabulary_size=c2_max_id + 1, embedding_dim=4),
    DenseFeat("I1", 1),
    DenseFeat("I2", 1),
]
```

Input contract:

```python
feature_names = get_feature_names(feature_columns)
model_input = {name: data[name].values for name in feature_names}
```

For list mode, use the same order as `feature_names`.

## MovieLens Multi-Value Fields

MovieLens-style tasks often have a pipe-delimited multi-value field such as `genres`.

Raw field example:

```text
genres = "Action|Sci-Fi|Thriller"
```

Convert each token to a 1-based id and reserve `0` for padding:

```python
key2index = {}

def encode_multi_value(text):
    ids = []
    for token in str(text).split("|"):
        if token not in key2index:
            key2index[token] = len(key2index) + 1
        ids.append(key2index[token])
    return ids
```

Then pad to a fixed width:

```python
from tensorflow.keras.preprocessing.sequence import pad_sequences

seqs = [encode_multi_value(x) for x in data["genres"]]
maxlen = max(len(x) for x in seqs)
genres = pad_sequences(seqs, maxlen=maxlen, padding="post", value=0)
```

Feature-column sketch:

```python
VarLenSparseFeat(
    SparseFeat("genres", vocabulary_size=len(key2index) + 1, embedding_dim=4),
    maxlen=maxlen,
    combiner="mean",
)
```

Use `VarLenSparseFeat` when you want embedding lookup plus pooling. Use `DenseFeat("genres_multihot", num_genres)` when you already have a dense multi-hot vector and do not need sequence pooling.

## DIN and BST History Fields

DIN/BST-style models use a candidate item plus one or more history sequences.

History names must be `hist_` + the behavior feature name used by the model.

Example behavior list:

```python
behavior_feature_list = ["item_id", "cate_id"]
```

Required history feature names:

- `hist_item_id`
- `hist_cate_id`

Typical row layout:

| item_id | cate_id | hist_item_id | hist_cate_id | seq_length | label |
|---|---|---|---|---|---|
| 1 | 1 | `[1, 2, 4, 0]` | `[1, 2, 2, 0]` | 3 | 1 |

DeepCTR uses the candidate row's label, not a label per history element.

Recommended schema:

```python
feature_columns = [
    SparseFeat("item_id", item_count + 1, embedding_dim=8),
    SparseFeat("cate_id", cate_count + 1, embedding_dim=4),
    VarLenSparseFeat(
        SparseFeat("hist_item_id", item_count + 1, embedding_dim=8, embedding_name="item_id"),
        maxlen=50,
        length_name="seq_length",
    ),
    VarLenSparseFeat(
        SparseFeat("hist_cate_id", cate_count + 1, embedding_dim=4, embedding_name="cate_id"),
        maxlen=50,
        length_name="seq_length",
    ),
]
```

Padding rule:

- use `0` as padding
- start valid ids from `1` when the sequence field shares a vocabulary with padding
- if `length_name` is absent, `0` is still treated as the padding value by the pooling mask

## DSIN Session Fields

DSIN expects sessions to be prepared before model input. DeepCTR does not split raw event streams into sessions for you.

Typical session schema for `sess_max_count=2`:

| item | cate_id | sess_0_item | sess_0_cate_id | sess_1_item | sess_1_cate_id | sess_length | label |
|---|---|---|---|---|---|---|---|
| 1 | 1 | `[4, 5, 0, 0]` | `[2, 2, 0, 0]` | `[2, 3, 0, 0]` | `[1, 1, 0, 0]` | 2 | 1 |

Session rules:

- keep only the most recent `sess_max_count` sessions
- pad each session to the same `maxlen`
- add `sess_length` for the number of valid sessions in the row
- each session field is still a `VarLenSparseFeat`

A DSIN feature sketch looks like:

```python
feature_columns = [
    SparseFeat("item", item_count + 1, embedding_dim=4),
    SparseFeat("cate_id", cate_count + 1, embedding_dim=4),
    VarLenSparseFeat(SparseFeat("sess_0_item", item_count + 1, embedding_dim=4, embedding_name="item"), maxlen=4),
    VarLenSparseFeat(SparseFeat("sess_0_cate_id", cate_count + 1, embedding_dim=4, embedding_name="cate_id"), maxlen=4),
    VarLenSparseFeat(SparseFeat("sess_1_item", item_count + 1, embedding_dim=4, embedding_name="item"), maxlen=4),
    VarLenSparseFeat(SparseFeat("sess_1_cate_id", cate_count + 1, embedding_dim=4, embedding_name="cate_id"), maxlen=4),
]
```

## Dense Vectors

Use `DenseFeat` for scalar numeric values or precomputed dense vectors.

Examples:

```python
DenseFeat("pay_score", 1)
DenseFeat("article_vector", 128)
DenseFeat("pic_vec", 5)
```

Shape guidance:

- scalar dense values: `(batch_size,)` or `(batch_size, 1)`
- dense vectors: `(batch_size, dimension)`
- use `dimension` to match the last axis of the tensor

## Input Dictionary and List Contracts

DeepCTR Keras workflows usually build inputs from `get_feature_names`.

Dictionary mode:

```python
feature_names = get_feature_names(feature_columns)
model_input = {name: data[name].values for name in feature_names}
```

List mode:

```python
feature_names = get_feature_names(feature_columns)
model_input = [data[name].values for name in feature_names]
```

Required keys from feature columns:

| Column | Required model-input keys |
|---|---|
| `SparseFeat("user_id", ...)` | `user_id` |
| `DenseFeat("pic_vec", 5)` | `pic_vec` |
| `VarLenSparseFeat(..., name="genres")` | `genres` |
| `VarLenSparseFeat(..., weight_name="genres_weight")` | `genres`, `genres_weight` |
| `VarLenSparseFeat(..., length_name="seq_length")` | `hist_item_id`, `seq_length` |

The label column must stay outside the feature list.

## Practical Shape Checklist

- `SparseFeat`: one id per row
- `DenseFeat`: scalar or fixed-width vector per row
- `VarLenSparseFeat`: fixed padded id list per row
- `weight_name`: per-position weights with trailing axis `1`
- `length_name`: sequence length per row
- `0` padding for variable-length fields
- valid ids start at `1` when padding is used

## Good Bundling Targets

This sub-skill bundles a validator for static feature specs. It should be enough to plan or review a DeepCTR input schema without opening the original repository again.
