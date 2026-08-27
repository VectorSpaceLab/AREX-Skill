# DeepCTR Feature Columns

This reference covers the Keras-style feature-column API in DeepCTR 0.9.4. It is self-contained and uses public `tensorflow.keras` APIs in examples.

## Imports

```python
from deepctr.feature_column import (
    SparseFeat,
    DenseFeat,
    VarLenSparseFeat,
    get_feature_names,
)
```

DeepCTR's package/import name is `deepctr`. TensorFlow/Keras must already be installed separately.

## API Signatures

### `SparseFeat`

```python
SparseFeat(
    name,
    vocabulary_size,
    embedding_dim=4,
    use_hash=False,
    vocabulary_path=None,
    dtype="int32",
    embeddings_initializer=None,
    embedding_name=None,
    group_name="default_group",
    trainable=True,
)
```

Use `SparseFeat` for one categorical id per row: user id, item id, country, ad slot, device, zip code, occupation, etc.

| Parameter | Meaning and constraints |
|---|---|
| `name` | Input feature key and Keras input name. Must be present in `model_input` unless using an ordered list input. |
| `vocabulary_size` | Number of embedding rows. For label-encoded integer ids, set at least `max_id + 1`. For hash features, this is the hash bucket space. |
| `embedding_dim` | Embedding vector size. Default `4`. Value `"auto"` becomes `6 * int(vocabulary_size ** 0.25)`. |
| `use_hash` | If `True`, DeepCTR applies its hash/lookup layer before embedding lookup. Required when `dtype="string"`. |
| `vocabulary_path` | Optional CSV vocabulary table for lookup mode. It is only applied when `use_hash=True`; otherwise input values are used directly as integer ids. |
| `dtype` | Keras input dtype. Use integer dtype for label-encoded ids; use `"string"` only with `use_hash=True`. |
| `embeddings_initializer` | Keras initializer for the embedding matrix. Default is a small random normal initializer. |
| `embedding_name` | Shared embedding-table name. Defaults to `name`. Features with the same `embedding_name` share one table. |
| `group_name` | Interaction group used by models that expose group-wise FM/interaction arguments. Defaults to `default_group`. |
| `trainable` | Whether the embedding table is trainable. Shared embeddings must agree on this value. |

#### Label-encoded sparse ids

```python
sparse_features = ["user_id", "item_id", "city"]
feature_columns = [
    SparseFeat("user_id", vocabulary_size=user_count + 1, embedding_dim=8),
    SparseFeat("item_id", vocabulary_size=item_count + 1, embedding_dim=8),
    SparseFeat("city", vocabulary_size=city_count + 1, embedding_dim=4),
]
```

Encode categorical values to non-negative integer ids before model input. For fixed-length `SparseFeat`, `0` can be a valid id, but if the same vocabulary is also used by a padded `VarLenSparseFeat`, reserve `0` for padding and start valid ids at `1`.

#### On-the-fly hash encoding

```python
feature_columns = [
    SparseFeat("C1", vocabulary_size=100_000, embedding_dim=8, use_hash=True, dtype="string"),
    SparseFeat("C2", vocabulary_size=100_000, embedding_dim=8, use_hash=True, dtype="string"),
]
```

Use this when raw categorical values are strings and you do not have a stable label encoder. Hashing trades exact ids for a fixed-size bucket space; collisions are possible, so choose a bucket count large enough for the field.

#### Vocabulary-table lookup

```python
age = SparseFeat(
    "age",
    vocabulary_size=8,
    embedding_dim=4,
    use_hash=True,
    dtype="string",
    vocabulary_path="/path/to/age_vocabulary.csv",
)
```

Vocabulary CSV rows use `id,key` order, for example:

```text
1,18-24
2,25-34
3,35-44
```

The second CSV column is matched against string input and the first column is the integer id returned to the embedding lookup. Missing keys return `0`, so reserve id `0` for unknown or padding-like behavior and start explicit vocabulary ids at `1`. In TensorFlow 1.x-style sessions, lookup tables may need explicit table initialization before training. In TensorFlow 2.x eager/standard Keras workflows, the table is normally initialized as part of layer execution.

### `DenseFeat`

```python
DenseFeat(
    name,
    dimension=1,
    dtype="float32",
    transform_fn=None,
)
```

Use `DenseFeat` for numerical values or already-computed dense vectors.

| Parameter | Meaning and constraints |
|---|---|
| `name` | Input key. |
| `dimension` | Number of numeric values per row. Use `1` for scalar features and the vector width for embeddings or precomputed features. |
| `dtype` | Usually `"float32"`. |
| `transform_fn` | Optional tensor-to-tensor callable wrapped in a Keras `Lambda`, such as `lambda x: (x - 3.0) / 4.2`. |

Examples:

```python
DenseFeat("hour", 1)
DenseFeat("price_norm", 1)
DenseFeat("article_vector", 128)
DenseFeat("pic_vec", 5, transform_fn=lambda x: x / 255.0)
```

Dense input arrays must match the declared dimension. Use shape `(batch_size, dimension)` for vectors. A one-dimensional array or pandas Series is commonly accepted for scalar `dimension=1`, but `(batch_size, 1)` is the safest explicit shape.

### `VarLenSparseFeat`

```python
VarLenSparseFeat(
    SparseFeat(...),
    maxlen,
    combiner="mean",
    length_name=None,
    weight_name=None,
    weight_norm=True,
)
```

Use `VarLenSparseFeat` for a list of categorical ids per row: genres, tags, clicked item history, category history, or per-session behavior sequences.

| Parameter | Meaning and constraints |
|---|---|
| `sparsefeat` | A `SparseFeat` that defines the sequence element vocabulary and embedding table. |
| `maxlen` | Fixed padded sequence length. This is not the vocabulary size. Input shape is `(batch_size, maxlen)`. |
| `combiner` | Pooling mode for non-attention use: `"mean"`, `"sum"`, or `"max"`. |
| `length_name` | Optional input key containing actual sequence lengths, shape `(batch_size,)` or `(batch_size, 1)`. |
| `weight_name` | Optional input key containing per-position weights, shape `(batch_size, maxlen, 1)`, dtype float32. |
| `weight_norm` | Whether DeepCTR normalizes sequence weights before applying them. Default `True`. |

Basic multi-value field:

```python
genres = VarLenSparseFeat(
    SparseFeat("genres", vocabulary_size=genre_count + 1, embedding_dim=4),
    maxlen=max_genres_per_movie,
    combiner="mean",
)
```

History field with an explicit length:

```python
hist_item = VarLenSparseFeat(
    SparseFeat(
        "hist_item_id",
        vocabulary_size=item_count + 1,
        embedding_dim=8,
        embedding_name="item_id",
    ),
    maxlen=50,
    combiner="mean",
    length_name="seq_length",
)
```

Weighted sequence field:

```python
weighted_tags = VarLenSparseFeat(
    SparseFeat("tag_id", vocabulary_size=tag_count + 1, embedding_dim=8),
    maxlen=20,
    combiner="mean",
    weight_name="tag_weight",
    weight_norm=True,
)
```

When `weight_name` is set, include an input named `tag_weight` with shape `(batch_size, 20, 1)`.

## `get_feature_names`

```python
feature_names = get_feature_names(linear_feature_columns + dnn_feature_columns)
model_input = {name: data[name].values for name in feature_names}
```

`get_feature_names` builds the Keras input keys that the model expects. It de-duplicates repeated columns by name, which is why the common pattern `linear_feature_columns = dnn_feature_columns = feature_columns` still produces one key per input.

For each column type it contributes:

| Column type | Keys added |
|---|---|
| `SparseFeat("user_id", ...)` | `user_id` |
| `DenseFeat("pic_vec", 5)` | `pic_vec` |
| `VarLenSparseFeat(... name="genres", weight_name=None, length_name=None)` | `genres` |
| `VarLenSparseFeat(... name="hist_item_id", length_name="seq_length")` | `hist_item_id`, `seq_length` |
| `VarLenSparseFeat(... name="genres", weight_name="genres_weight")` | `genres`, `genres_weight` |
| Both `length_name` and `weight_name` | sequence name, weight name, length name |

Labels are not feature columns. Do not put `label`, `rating`, or multitask targets in a feature column list just to make them appear in `feature_names`.

## Embedding Sharing With `embedding_name`

Use the same `embedding_name` only when two fields draw ids from the same dictionary and should share one Keras embedding layer.

```python
feature_columns = [
    SparseFeat("item_id", item_count + 1, embedding_dim=8),
    VarLenSparseFeat(
        SparseFeat(
            "hist_item_id",
            item_count + 1,
            embedding_dim=8,
            embedding_name="item_id",
        ),
        maxlen=50,
        length_name="seq_length",
    ),
]
```

DeepCTR reuses one embedding table keyed by `embedding_name`. All feature columns with the same `embedding_name` must have the same:

- `vocabulary_size`
- `embedding_dim`
- `trainable`

If any of these differ, embedding-matrix creation raises an error. For example, `hist_item_id` cannot share `embedding_name="item_id"` if it uses `vocabulary_size=item_count + 2` while `item_id` uses `item_count + 1`. Fix by using the exact same vocabulary size, or use a different `embedding_name` when the vocabularies are not identical.

Sharing candidate and history item embeddings is common for DIN/BST-style inputs. Do not share embeddings between semantically different fields just because their id ranges happen to be the same.

## `group_name`

`group_name` separates embedding groups for models that expose group-wise interaction parameters, such as FM-family models with an `fm_group` argument. The default group is `default_group`.

```python
from deepctr.feature_column import DEFAULT_GROUP_NAME

feature_columns = [
    SparseFeat("user_id", user_count + 1, embedding_dim=8, group_name="user"),
    SparseFeat("item_id", item_count + 1, embedding_dim=8, group_name="item"),
    SparseFeat("slot", slot_count + 1, embedding_dim=4, group_name=DEFAULT_GROUP_NAME),
]
```

If a model does not expose a group argument, `group_name` usually has no visible effect. If a model does expose one, only the selected groups participate in that interaction path; dense features are not grouped through `group_name`.

## Common Construction Patterns

### Criteo-style tabular CTR with label encoding

```python
sparse_features = ["C" + str(i) for i in range(1, 27)]
dense_features = ["I" + str(i) for i in range(1, 14)]

feature_columns = [
    SparseFeat(feat, vocabulary_size=int(data[feat].max()) + 1, embedding_dim=4)
    for feat in sparse_features
] + [
    DenseFeat(feat, 1)
    for feat in dense_features
]

feature_names = get_feature_names(feature_columns)
model_input = {name: data[name].values for name in feature_names}
```

Fill categorical nulls before encoding and fill dense nulls before scaling. Keep `label` outside the feature list.

### Criteo-style tabular CTR with hashing

```python
feature_columns = [
    SparseFeat(feat, vocabulary_size=1_000_000, embedding_dim=4, use_hash=True, dtype="string")
    for feat in sparse_features
] + [DenseFeat(feat, 1) for feat in dense_features]
```

Use string arrays for hashed sparse fields. Dense fields remain numeric.

### MovieLens multi-value genres

```python
from tensorflow.keras.preprocessing.sequence import pad_sequences

key2index = {}

def encode_genres(text):
    ids = []
    for token in str(text).split("|"):
        if token not in key2index:
            key2index[token] = len(key2index) + 1  # reserve 0 for padding
        ids.append(key2index[token])
    return ids

genre_lists = [encode_genres(x) for x in data["genres"]]
max_len = max(len(x) for x in genre_lists)
genre_array = pad_sequences(genre_lists, maxlen=max_len, padding="post", value=0)

feature_columns = fixed_sparse_columns + [
    VarLenSparseFeat(
        SparseFeat("genres", vocabulary_size=len(key2index) + 1, embedding_dim=4),
        maxlen=max_len,
        combiner="mean",
    )
]

feature_names = get_feature_names(feature_columns)
model_input = {name: data[name].values for name in feature_names if name != "genres"}
model_input["genres"] = genre_array
```

If you already have a multi-hot vector of shape `(batch_size, num_genres)`, represent it as `DenseFeat("genres_multihot", num_genres)` instead. Use `VarLenSparseFeat` when you want DeepCTR to learn and pool embeddings for the present category ids.

## Validate Before Model Build

Use the bundled validator to catch schema mistakes before constructing a model:

```bash
python scripts/validate_feature_spec.py --emit-example din-history > din_spec.json
python scripts/validate_feature_spec.py din_spec.json
```

The validator is static and does not import TensorFlow or DeepCTR. It checks names, dimensions, dtypes, `maxlen`, supplemental sequence inputs, shared embedding compatibility, padding conventions, and optional user-provided input keys/shapes.
