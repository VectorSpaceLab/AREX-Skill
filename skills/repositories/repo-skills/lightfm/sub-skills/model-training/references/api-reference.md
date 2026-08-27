# LightFM model-training API reference

This reference covers model-operation APIs only. For data construction and feature matrices, route to [`../../data-features/SKILL.md`](../../data-features/SKILL.md). For metrics and split design, route to [`../../evaluation-splitting/SKILL.md`](../../evaluation-splitting/SKILL.md).

## Import surface

```python
from lightfm import LightFM
```

LightFM is a CPU-only package. Model methods accept SciPy sparse matrices and NumPy arrays; sparse inputs are converted internally to the formats and `np.float32` dtype used by the compiled training routines.

## Constructor

```python
LightFM(
    no_components=10,
    k=5,
    n=10,
    learning_schedule="adagrad",
    loss="logistic",
    learning_rate=0.05,
    rho=0.95,
    epsilon=1e-06,
    item_alpha=0.0,
    user_alpha=0.0,
    max_sampled=10,
    random_state=None,
)
```

| Parameter | Meaning | Gotchas |
| --- | --- | --- |
| `no_components` | Latent embedding dimension. | Must be positive. More components can overfit and increase memory/time. |
| `loss` | One of `"logistic"`, `"warp"`, `"bpr"`, `"warp-kos"`. | `logistic` is for explicit positive/negative labels; ranking losses are for implicit positives. |
| `learning_schedule` | `"adagrad"` or `"adadelta"`. | `adagrad` uses `learning_rate`; `adadelta` uses `rho`/`epsilon`. Neither is universally best. |
| `learning_rate` | Initial step size for `adagrad`. | Too high can produce non-finite parameters or divergence. |
| `rho`, `epsilon` | `adadelta` moving-average and conditioning parameters. | Constructor asserts `0 < rho < 1` and `epsilon >= 0`. |
| `item_alpha`, `user_alpha` | L2 penalties on item/user feature embeddings. | Must be non-negative. Too high can drive embeddings close to zero and slow training. |
| `max_sampled` | Max negative samples while fitting WARP. | Must be positive. Higher can improve hard-negative search but often increases WARP time. |
| `k`, `n` | k-order statistic settings for `warp-kos`. | Both must be positive; `sample_weight` is not implemented for `warp-kos`. |
| `random_state` | `None`, integer seed, or `numpy.random.RandomState`. | Use an integer seed for repeatable initialization/shuffling. Multi-threaded numeric order may still vary by platform. |

Constructor assertions reject invalid losses/schedules and negative regularization. `max_sampled < 1` raises `ValueError`.

## Training APIs

```python
LightFM.fit(
    self,
    interactions,
    user_features=None,
    item_features=None,
    sample_weight=None,
    epochs=1,
    num_threads=1,
    verbose=False,
)

LightFM.fit_partial(
    self,
    interactions,
    user_features=None,
    item_features=None,
    sample_weight=None,
    epochs=1,
    num_threads=1,
    verbose=False,
)
```

| Argument | Required shape/type | Notes |
| --- | --- | --- |
| `interactions` | SciPy sparse user-item matrix, shape `[n_users, n_items]`. | Converted to COO and `np.float32`. Non-finite values raise `ValueError`. |
| `user_features` | Optional sparse matrix, shape `[n_users, n_user_features]`. | If omitted, an identity feature matrix is used. Rows must cover every user. Feature columns define learned user-feature embeddings. |
| `item_features` | Optional sparse matrix, shape `[n_items, n_item_features]`. | If omitted, an identity feature matrix is used. Rows must cover every item. Feature columns define learned item-feature embeddings. |
| `sample_weight` | Optional `scipy.sparse.coo_matrix`, same shape and row/column order as `interactions`. | Defaults to weight `1.0` per interaction. Must be COO and aligned entry-for-entry with `interactions`; not available with `warp-kos`. |
| `epochs` | Integer epoch count. | `epochs=0` initializes model state without training updates. |
| `num_threads` | Integer `>= 1`. | CPU threads only; keep no higher than physical cores. |
| `verbose` | Boolean. | Uses a progress bar if available, otherwise prints epoch progress. |

`fit` discards any existing learned state, then calls `fit_partial`. `fit_partial` initializes state on its first call, then resumes from the current embeddings on later calls. Keep the same feature-column schema between `fit_partial` calls; changing the number of user/item feature columns raises `ValueError`.

### Loss selection

| Loss | Use when | Training behavior |
| --- | --- | --- |
| `logistic` | You have positive and negative labels, usually `1` and `-1`, in `interactions.data`. | Pointwise objective; supports `sample_weight`. |
| `bpr` | Implicit feedback and AUC-like pairwise ranking. | Samples random negative items; supports `sample_weight`. |
| `warp` | Implicit feedback and top-of-list precision. | Samples negatives until a rank violation is found; can slow down as the model improves; supports `sample_weight`. |
| `warp-kos` | Experimental k-order statistic WARP. | Uses `k`/`n`; `sample_weight` raises `NotImplementedError`. |

## Prediction APIs

```python
LightFM.predict(
    self,
    user_ids,
    item_ids,
    item_features=None,
    user_features=None,
    num_threads=1,
)
```

Returns an `np.float32` array of shape `[n_pairs]` with one score per input pair. `predict([0, 1], [8, 9])` scores `(0, 8)` and `(1, 9)`; it does **not** score the Cartesian product. To rank all items for one user:

```python
import numpy as np

n_items = interactions.shape[1]
scores = model.predict(0, np.arange(n_items), num_threads=1)
top_items = np.argsort(-scores)[:10]
```

To score all items for many users, repeat and tile the ids:

```python
users = np.array([0, 1, 2], dtype=np.int32)
items = np.arange(n_items, dtype=np.int32)
user_ids = np.repeat(users, len(items))
item_ids = np.tile(items, len(users))
scores = model.predict(user_ids, item_ids).reshape(len(users), len(items))
```

Calling `predict` before fitting raises `ValueError`.

## Rank prediction API

```python
LightFM.predict_rank(
    self,
    test_interactions,
    train_interactions=None,
    item_features=None,
    user_features=None,
    num_threads=1,
    check_intersections=True,
)
```

Returns a CSR sparse matrix with the same shape as `test_interactions`; each non-zero test pair receives its rank among all items for that user, where `0` means top-ranked. `train_interactions` excludes known training pairs from ranking. With `check_intersections=True`, overlapping train/test entries raise `ValueError` to prevent optimistic evaluation.

Use `predict_rank` for sparse rank inspection or as the internal route used by evaluation utilities. For full evaluation metric workflows, use [`../../evaluation-splitting/SKILL.md`](../../evaluation-splitting/SKILL.md).

## Representation APIs

```python
LightFM.get_item_representations(self, features=None)
LightFM.get_user_representations(self, features=None)
```

Returns `(biases, embeddings)`:

| Method | `features=None` return | With feature matrix |
| --- | --- | --- |
| `get_item_representations` | Raw item-feature biases and embeddings. With identity item features, rows correspond to item ids. | Returns `features * item_biases` and `features * item_embeddings`, producing one row per supplied item. |
| `get_user_representations` | Raw user-feature biases and embeddings. With identity user features, rows correspond to user ids. | Returns `features * user_biases` and `features * user_embeddings`, producing one row per supplied user. |

The prediction equation is:

```python
score = (user_embeddings[user_id] * item_embeddings[item_id]).sum()
score += user_biases[user_id] + item_biases[item_id]
```

Use representation exports for diagnostics, model serving caches, or optional ANN indexes. Calling either representation method before fitting raises `ValueError`.

## Sklearn-style API and serialization

```python
params = model.get_params()
model.set_params(loss="warp", no_components=32)
```

`get_params` returns constructor-style parameters: `loss`, `learning_schedule`, `no_components`, `learning_rate`, `k`, `n`, `rho`, `epsilon`, `max_sampled`, `item_alpha`, `user_alpha`, and `random_state`. `set_params` rejects unknown parameter names with `ValueError`.

Fitted `LightFM` instances are pickle-compatible in normal Python use:

```python
import pickle

blob = pickle.dumps(model)
restored = pickle.loads(blob)
```

Persist the id mappings and feature schema beside the model; those are data concerns routed to [`../../data-features/SKILL.md`](../../data-features/SKILL.md).

## Routed APIs

These verified APIs are commonly used with model training but belong to other sub-skills:

| API | Signature | Route |
| --- | --- | --- |
| `Dataset` | `Dataset(user_identity_features=True, item_identity_features=True)` | [`../../data-features/SKILL.md`](../../data-features/SKILL.md) |
| `precision_at_k` | `precision_at_k(model, test_interactions, train_interactions=None, k=10, user_features=None, item_features=None, preserve_rows=False, num_threads=1, check_intersections=True)` | [`../../evaluation-splitting/SKILL.md`](../../evaluation-splitting/SKILL.md) |
| `auc_score` | `auc_score(model, test_interactions, train_interactions=None, user_features=None, item_features=None, preserve_rows=False, num_threads=1, check_intersections=True)` | [`../../evaluation-splitting/SKILL.md`](../../evaluation-splitting/SKILL.md) |
| `random_train_test_split` | `random_train_test_split(interactions, test_percentage=0.2, random_state=None)` | [`../../evaluation-splitting/SKILL.md`](../../evaluation-splitting/SKILL.md) |
