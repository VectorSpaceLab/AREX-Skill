# LightFM model-training troubleshooting

Use this when model training, scoring, representation export, or serving behaves unexpectedly. Route raw id mapping and feature construction issues to [`../../data-features/SKILL.md`](../../data-features/SKILL.md); route metric/split correctness issues to [`../../evaluation-splitting/SKILL.md`](../../evaluation-splitting/SKILL.md); route build/OpenMP maintenance issues to [`../../repo-development/SKILL.md`](../../repo-development/SKILL.md).

## `ValueError: You must fit the model before trying to obtain predictions.`

Affected calls include `predict`, `predict_rank`, `get_user_representations`, and `get_item_representations`.

Fix:

```python
model.fit(train, epochs=5)
# or, if intentionally resuming:
model.fit_partial(train, epochs=1)
```

Remember: `fit` resets learned state; `fit_partial` initializes on the first call and resumes on later calls.

## Feature or interaction shape mismatch

Typical symptoms:

- `Number of user feature rows does not equal the number of users`
- `Number of item feature rows does not equal the number of items`
- `Incorrect number of features in user_features`
- `Incorrect number of features in item_features`
- prediction errors when using feature matrices that do not match training

Checks:

```python
n_users, n_items = interactions.shape
assert user_features is None or user_features.shape[0] >= n_users
assert item_features is None or item_features.shape[0] >= n_items
```

For resumed training, the number and meaning of feature columns must stay fixed. If adding new users/items through identity features, rebuild the data schema deliberately through [`../../data-features/SKILL.md`](../../data-features/SKILL.md); do not silently append columns to an already trained model and expect old embeddings to align.

## `sample_weight` errors

Common errors:

- `Sample_weight must be a COO matrix.`
- `Sample weight and interactions matrices must be the same shape`
- `Sample weight and interaction matrix entries must be in the same order`
- `k-OS loss with sample weights not implemented.`

Correct pattern:

```python
import scipy.sparse as sp

train_coo = interactions.tocoo()
sample_weight = sp.coo_matrix(
    (weights.astype("float32"), (train_coo.row, train_coo.col)),
    shape=train_coo.shape,
)
model.fit_partial(train_coo, sample_weight=sample_weight, epochs=5)
```

Do not sort, deduplicate, convert, or slice the weight matrix separately from `interactions`; that can change COO row/column order. Do not use `sample_weight` with `loss="warp-kos"`.

## Non-finite inputs, NaNs, or model divergence

LightFM checks finite values in `interactions.data`, feature matrices, and sample weights. It also checks learned parameters after each epoch. Non-finite inputs or divergent parameters raise `ValueError`.

Triage:

```python
import numpy as np

for name, mat in {
    "interactions": interactions,
    "user_features": user_features,
    "item_features": item_features,
    "sample_weight": sample_weight,
}.items():
    if mat is not None:
        data = getattr(mat, "data", mat)
        assert np.isfinite(np.asarray(data)).all(), name
```

Fixes:

- lower `learning_rate`, especially for `adagrad`;
- normalize large continuous features or confidence weights;
- remove or impute NaN/Inf feature values;
- reduce extreme `sample_weight` magnitudes;
- run a one-epoch tiny check before long training.

## All users receive the same popular items

Causes often include popularity bias, weak user personalization signal, too much item bias influence, or metadata that overwhelms identity features.

Actions:

- verify that per-user/per-item identity features were not accidentally dropped when side features were added;
- compare a pure collaborative-filtering baseline against the hybrid model;
- inspect `model.item_biases` and consider zeroing item biases at serving time as a diagnostic:

```python
saved_biases = model.item_biases.copy()
model.item_biases[:] = 0.0
scores_without_item_bias = model.predict(user_id, item_ids)
model.item_biases[:] = saved_biases
```

- use inverse-propensity or confidence weights if exposure/popularity is highly skewed;
- add validation metrics that punish non-personalized recommendation lists.

## WARP epochs get slower or never finish quickly

WARP samples negative items until it finds a rank violation. As the model improves, violations can become harder to find, making later epochs slower. `max_sampled` caps this search.

Actions:

```python
model = LightFM(loss="warp", max_sampled=10, random_state=42)
```

- reduce `max_sampled` and compare validation quality;
- use early stopping based on validation metrics;
- try `bpr` if WARP is too slow for the target latency/budget;
- avoid very large `num_threads` values that exceed physical cores.

## Overfitting or underfitting

Signals:

- train metrics improve while validation metrics decline;
- learned embeddings have very large magnitudes or validation recommendations become unstable;
- embeddings are almost all zero after strong regularization.

Actions:

- reduce `no_components`;
- stop at the epoch with best validation score;
- raise `item_alpha` and `user_alpha` gradually, for example from `1e-6` to `1e-4`;
- if embeddings collapse toward zero or training stalls, lower regularization;
- tune loss/schedule with `fit_partial` loops in [`workflows.md`](workflows.md).

## `predict` scores unexpected pairs

`predict` pairs positions elementwise. It does not compute a Cartesian product.

Wrong expectation:

```python
# Scores only (0, 8) and (1, 9), not all 2 x 2 combinations.
model.predict([0, 1], [8, 9])
```

Correct all-items-for-users pattern:

```python
import numpy as np

users = np.asarray([0, 1], dtype=np.int32)
items = np.arange(n_items, dtype=np.int32)
scores = model.predict(np.repeat(users, len(items)), np.tile(items, len(users)))
scores = scores.reshape(len(users), len(items))
```

Filter already-known training items before selecting top-k recommendations.

## `predict_rank` train/test intersection error

With `check_intersections=True`, overlapping non-zero train and test entries raise `ValueError` because ranking would be optimistic.

Fix the split in [`../../evaluation-splitting/SKILL.md`](../../evaluation-splitting/SKILL.md). Only set `check_intersections=False` when intentionally ranking a matrix that overlaps training data for a non-evaluation diagnostic.

## `num_threads` and OpenMP behavior

- `num_threads < 1` raises `ValueError`.
- LightFM training and prediction are CPU-only; there is no GPU backend.
- Threads should not exceed physical cores.
- If the installed build lacks OpenMP support, increasing `num_threads` may not improve speed.
- For reproducible debugging and smoke checks, use `num_threads=1`.

Build-level OpenMP questions belong to [`../../repo-development/SKILL.md`](../../repo-development/SKILL.md).

## No GPU acceleration

LightFM has no GPU implementation for training or inference. Do not spend time debugging CUDA, ROCm, MPS, or vendor accelerator configuration for this package. Optimize CPU matrix sizes, sampling settings, thread count, feature sparsity, and serving caches instead.

## Optional ANN import failures

Errors such as `ModuleNotFoundError: annoy` or `ModuleNotFoundError: nmslib` are optional-serving issues, not LightFM model failures.

Use lazy imports and fallbacks:

```python
import numpy as np

_, item_embeddings = model.get_item_representations(item_features)

try:
    from annoy import AnnoyIndex
except ImportError:
    AnnoyIndex = None

if AnnoyIndex is None:
    scores = item_embeddings @ item_embeddings[query_item_id]
    nearest = np.argsort(-scores)[:10]
else:
    # build/query ANN index
    ...
```

Benchmark ANN quality against exact `predict` or exact vector search before using it for user-facing recommendations.

## Pickle loads but recommendations are wrong

A pickled model does not by itself preserve raw user/item labels or feature-vocabulary meaning.

Check that the deployment bundle includes:

- the fitted model;
- the same internal id mappings used during training;
- the same feature vocabulary and matrix-construction recipe;
- the same candidate filtering policy;
- any ANN index built from the same model and feature matrix.

If mappings/features are missing, route to [`../../data-features/SKILL.md`](../../data-features/SKILL.md) and rebuild a consistent bundle.
