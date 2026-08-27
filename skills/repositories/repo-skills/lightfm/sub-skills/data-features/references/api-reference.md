# LightFM data and feature API reference

This reference covers the data-building surface used before model training, prediction, and evaluation. LightFM 1.17 is a CPU-only package; these data helpers build SciPy sparse matrices and do not provide a GPU-specific path.

## `lightfm.data.Dataset`

### Constructor

```python
Dataset(user_identity_features=True, item_identity_features=True)
```

| Argument | Default | Effect |
| --- | --- | --- |
| `user_identity_features` | `True` | Adds one user feature column for every fitted user id. This lets the model learn a per-user embedding in addition to any metadata features. |
| `item_identity_features` | `True` | Adds one item feature column for every fitted item id. This lets the model learn a per-item embedding in addition to any metadata features. |

With both defaults enabled, feature columns include identity columns plus any explicit metadata feature names passed to `fit` or `fit_partial`.

### Mapping and matrix methods

| Method | Signature | Returns / behavior |
| --- | --- | --- |
| `fit` | `fit(users, items, user_features=None, item_features=None)` | Clears any previous mappings, then adds user ids, item ids, and optional feature vocabularies. |
| `fit_partial` | `fit_partial(users=None, items=None, user_features=None, item_features=None)` | Adds only new ids/features to existing mappings, preserving already assigned indices. Use before model initialization or retrain when new feature columns are added. |
| `interactions_shape` | `interactions_shape()` | `(num_users, num_items)`, based on fitted user/item id mappings. |
| `build_interactions` | `build_interactions(data)` | Returns `(interactions, weights)`. Both are COO matrices with shape `(num_users, num_items)`. `interactions` has dtype `int32` and stores `1` for each supplied event; `weights` has dtype `float32` and stores the supplied weight or `1.0`. |
| `user_features_shape` | `user_features_shape()` | `(num_users, num_user_features)`. Includes identity feature columns when enabled. |
| `build_user_features` | `build_user_features(data, normalize=True)` | Returns a CSR `float32` matrix with shape `user_features_shape()`. List features receive weight `1.0`; dict features use supplied weights. With `normalize=True`, rows are L1-normalized and rows with no stored features raise a `ValueError`. |
| `item_features_shape` | `item_features_shape()` | `(num_items, num_item_features)`. Includes identity feature columns when enabled. |
| `build_item_features` | `build_item_features(data, normalize=True)` | Returns a CSR `float32` matrix with shape `item_features_shape()`. Semantics match `build_user_features`. |
| `model_dimensions` | `model_dimensions()` | `(num_user_features, num_item_features)`, the feature-column counts that the LightFM model must allocate embeddings for. |
| `mapping` | `mapping()` | `(user_id_map, user_feature_map, item_id_map, item_feature_map)`. Each map is a dictionary from external id/feature label to internal zero-based index. |

### Interaction records

`build_interactions` accepts an iterable whose elements are:

- `(user_id, item_id)` for unit-weight events.
- `(user_id, item_id, weight)` for weighted events.

The user and item ids must already be in the mappings created by `fit` or `fit_partial`. Repeated pairs are stored as repeated COO entries; aggregate or call sparse duplicate-coalescing logic upstream if duplicate semantics matter.

### Feature records

`build_user_features` and `build_item_features` accept an iterable whose elements are:

- `(entity_id, [feature_name, ...])`; every listed feature gets weight `1.0`.
- `(entity_id, {feature_name: weight, ...})`; supplied weights are stored as `float32` values.

The entity id and every feature name must already be fitted. A single string is iterable in Python, so wrap a single feature as `['feature:name']`, not `'feature:name'`.

### Mapping semantics

- Indices are assigned in first-seen order from the iterables passed to `fit` and later `fit_partial` calls.
- `fit` resets all mappings. `fit_partial` extends them without renumbering old entries.
- `mapping()` exposes the internal dictionaries; treat them as read-only and persist copies if needed.
- Invert `user_id_map` and `item_id_map` when converting model row/column indices back to external ids.
- Identity features use the raw id object as the feature label. If metadata feature names can equal raw ids, namespace metadata labels to prevent accidental column collisions.

## Matrix expectations for downstream model calls

| Matrix | Typical source | Format and dtype | Required alignment |
| --- | --- | --- | --- |
| `interactions` | `Dataset.build_interactions(...)[0]` | COO `int32`, shape `(num_users, num_items)` | Rows and columns use `user_id_map` and `item_id_map`. |
| `sample_weight` / `weights` | `Dataset.build_interactions(...)[1]` | COO `float32`, same shape as `interactions` | Nonzero entries should correspond to interaction events. Route loss/weighting decisions to [model-training](../../model-training/SKILL.md). |
| `user_features` | `Dataset.build_user_features(...)` | CSR `float32`, shape `(num_users, num_user_features)` | Row count must cover all user rows used by interactions/prediction; column count must match the model's user feature embeddings. |
| `item_features` | `Dataset.build_item_features(...)` or built-in fetchers | CSR `float32`, shape `(num_items, num_item_features)` | Row count must cover all item columns used by interactions/prediction; column count must match the model's item feature embeddings. |

If explicit feature matrices are passed during training, pass compatible matrices again during `predict`, `predict_rank`, and evaluation. If no feature matrix is passed, LightFM constructs an identity matrix internally for that side.

## Built-in dataset fetchers

Built-in fetchers may download data into a user cache when data is missing. Use `download_if_missing=False` in offline workflows and provide `data_home` when the cache location must be controlled.

### `fetch_movielens`

```python
fetch_movielens(
    data_home=None,
    indicator_features=True,
    genre_features=False,
    min_rating=0.0,
    download_if_missing=True,
)
```

| Key | Type / shape | Notes |
| --- | --- | --- |
| `train` | COO sparse matrix, shape `(943, 1682)` for MovieLens 100k | Values are ratings that satisfy `rating >= min_rating`; default includes all ratings. |
| `test` | COO sparse matrix, same shape as `train` | Aligned with `train`. |
| `item_features` | CSR `float32`, shape depends on feature flags | Identity-only: `(1682, 1682)`. Genre-only: `(1682, n_genres)`. Both: `(1682, 1682 + n_genres)`. |
| `item_feature_labels` | NumPy string array, length equals `item_features.shape[1]` | Identity-only labels are the item titles; genre labels are prefixed as genre labels. |
| `item_labels` | NumPy string array, length `1682` | Movie titles indexed by item column. In identity-only mode this is the same object as `item_feature_labels`; with genres included it is separate. |

At least one of `indicator_features` or `genre_features` must be true.

### `fetch_stackexchange`

```python
fetch_stackexchange(
    dataset,
    test_set_fraction=0.2,
    min_training_interactions=1,
    data_home=None,
    indicator_features=True,
    tag_features=False,
    download_if_missing=True,
)
```

| Argument / key | Type / shape | Notes |
| --- | --- | --- |
| `dataset` | `'crossvalidated'` or `'stackoverflow'` | Other values raise `ValueError`. |
| `test_set_fraction` | float strictly between `0.0` and `1.0` | The split is chronological: later interactions form the test set. |
| `min_training_interactions` | int | Users are filtered after splitting; with value `m`, users must have more than `m` training interactions. |
| `train` | COO sparse matrix | Data values are `1.0`. With no filtering in the source tests, CrossValidated is `(9431, 72360)` and StackOverflow is very large. |
| `test` | COO sparse matrix, same shape as `train` | Data values are `1.0`. |
| `item_features` | CSR `float32` | Indicator-only: `(n_items, n_items)`. Tag-only: `(n_items, n_tags)`. Both: `(n_items, n_items + n_tags)`. |
| `item_feature_labels` | NumPy string array, length equals `item_features.shape[1]` | Indicator labels are `question_id:<index>`; tag labels come from the dataset. |

At least one of `indicator_features` or `tag_features` must be true. The StackOverflow dataset is extremely large; use small synthetic or CrossValidated-like data for quick local usability checks.
