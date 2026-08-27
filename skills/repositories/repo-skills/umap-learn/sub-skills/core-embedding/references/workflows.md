# Core UMAP Workflows

These recipes use the base `umap.UMAP` estimator and require only the core runtime dependencies (`numpy`, `scipy`, `scikit-learn`, `numba`, `pynndescent`, `tqdm`). They avoid plotting, TensorFlow/Keras, downloads, and large training.

## Quick environment probe

Use the bundled inspector when you need exact installed signatures or to diagnose a fitted estimator:

```bash
python ../scripts/inspect_umap_estimator.py --json
python ../scripts/inspect_umap_estimator.py --pickle mapper.pkl --json
```

Use the smoke script before relying on transform/inverse/sparse/precomputed behavior in a new environment:

```bash
python ../scripts/umap_core_smoke.py --dataset iris --all --json
```

The script paths above are relative to this `references/` directory. From the sub-skill root, use `python scripts/...`.

## Basic embedding

```python
import numpy as np
import umap

mapper = umap.UMAP(
    n_neighbors=15,
    n_components=2,
    min_dist=0.1,
    metric="euclidean",
    random_state=42,
)
embedding = mapper.fit_transform(X)

assert embedding.shape == (X.shape[0], 2)
assert np.allclose(embedding, mapper.embedding_, equal_nan=True)
```

Use `fit_transform` when you only need the training embedding immediately. Use `fit` when you also need the trained object for `transform`, `inverse_transform`, `update`, diagnostics, or serialization.

```python
mapper = umap.UMAP(random_state=42).fit(X)
training_embedding = mapper.embedding_
```

## Fit once, transform held-out data

```python
from sklearn.model_selection import train_test_split
import umap

X_train, X_test = train_test_split(X, test_size=0.25, random_state=0)
mapper = umap.UMAP(n_neighbors=10, min_dist=0.05, random_state=42).fit(X_train)

X_train_embedding = mapper.embedding_
X_test_embedding = mapper.transform(X_test)

assert X_test_embedding.shape == (X_test.shape[0], mapper.n_components)
```

Operational notes:

- Fit on the training set only when evaluating downstream models; do not fit UMAP separately on train and test.
- `mapper.transform(X_train)` short-circuits to `mapper.embedding_` when `X_train` is identical to the fitted data.
- The first transform call can be slower because numba may JIT compile transform kernels.
- `transform_seed` controls stochastic transform details. Keep it fixed when you need repeatable transform results for a fixed fitted mapper.
- `densmap=True` does not support transforming new data; route density-preserving tasks to `../../supervised-density/SKILL.md`.

## Use UMAP features in sklearn workflows

UMAP follows the sklearn transformer API, so it can appear in a preprocessing pipeline:

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import umap

embedder = Pipeline([
    ("scale", StandardScaler()),
    ("umap", umap.UMAP(n_components=10, random_state=42)),
])
Z_train = embedder.fit_transform(X_train)
Z_test = embedder.transform(X_test)
```

Important classifier-pipeline caveat: sklearn passes `y` to transformer `fit`/`fit_transform` during `Pipeline.fit(X, y)`. Because `UMAP.fit(X, y)` performs supervised UMAP, a pipeline such as `Pipeline([("umap", UMAP()), ("clf", clf)])` is no longer an unsupervised embedding step when fitted with labels. If supervised UMAP is intended, use `../../supervised-density/SKILL.md`. If unsupervised UMAP is required before a classifier, fit the UMAP preprocessing pipeline separately without labels, then train the classifier on the embedding, or wrap UMAP in a transformer whose `fit` ignores `y`.

## Approximate inverse transform

```python
mapper = umap.UMAP(n_components=2, random_state=42).fit(X_train)
low_dim_points = mapper.embedding_[:5]
X_approx = mapper.inverse_transform(low_dim_points)

assert X_approx.shape == (5, X_train.shape[1])
```

Use inverse transform only as an approximation. It is most meaningful for low-dimensional coordinates inside or near the convex hull of the learned embedding. It is unavailable when the original fit used sparse input, `metric="precomputed"`, a metric without gradients, `densmap=True`, or `transform_mode="graph"`.

If robust neural inverse mappings are the main task, route to `../../parametric-umap/SKILL.md`.

## Append data with `update`

```python
mapper = umap.UMAP(n_neighbors=10, random_state=42, n_epochs=100).fit(X_initial)
old_n = mapper.embedding_.shape[0]

result = mapper.update(X_new)
assert result is None
assert mapper.embedding_.shape[0] == old_n + X_new.shape[0]
```

Use `update` for incremental appends to an unsupervised, non-precomputed model. It mutates the existing estimator. Prefer refitting when the new data distribution differs substantially, when you need a clean comparison, or when you must preserve the original mapper.

`update` is not supported for `metric="precomputed"` and not supported for supervised models.

## Sparse input workflow

UMAP can fit and transform `scipy.sparse` matrices directly.

```python
from scipy import sparse
import umap

X_train_csr = sparse.csr_matrix(X_train)
X_test_csr = sparse.csr_matrix(X_test)

mapper = umap.UMAP(metric="cosine", random_state=42, low_memory=True).fit(X_train_csr)
Z_test = mapper.transform(X_test_csr)
```

Notes:

- CSR input is the safest sparse format; UMAP validates with `accept_sparse="csr"`.
- Use metrics supported for sparse data; common choices include `euclidean`, `manhattan`, `cosine`, `correlation`, `hellinger`, and binary metrics such as `jaccard` or `dice`.
- `inverse_transform` is not available for sparse original data.
- With `random_state` set, expect UMAP to set effective `n_jobs` to `1` even for sparse workflows.

## Precomputed distance matrix workflow

Use this when distances are already computed or when the raw representation is unavailable.

```python
from sklearn.metrics import pairwise_distances
import umap

D_train = pairwise_distances(X_train)            # shape: (n_train, n_train)
D_new_to_train = pairwise_distances(X_new, X_train)  # shape: (n_new, n_train)

mapper = umap.UMAP(metric="precomputed", n_neighbors=10, random_state=42).fit(D_train)
Z_new = mapper.transform(D_new_to_train)
```

Do not pass a square new-new distance matrix to `transform`. For transform, columns must correspond to the original training rows used at fit time.

For sparse precomputed fit matrices, ensure the matrix is symmetric, has zero diagonal, and each row contains enough neighbor distances. For sparse precomputed transform matrices, each row must contain at least `n_neighbors` distances to training samples.

Limitations: no `inverse_transform`, no `unique=True`, no `update`.

## Reuse precomputed k-NN for parameter sweeps

When exploring many UMAP settings on the same data, compute a k-NN graph once with a k at least as large as the largest `n_neighbors` you will fit.

```python
from umap.umap_ import nearest_neighbors
import umap

knn = nearest_neighbors(
    X,
    n_neighbors=50,
    metric="euclidean",
    metric_kwds=None,
    angular=False,
    random_state=42,
)

for k in [10, 30, 50]:
    mapper = umap.UMAP(
        n_neighbors=k,
        min_dist=0.1,
        precomputed_knn=knn,
        random_state=42,
    ).fit(X)
```

Keep the full three-item tuple if you later need `transform(X_new)`. A two-array tuple `(knn_indices, knn_dists)` fits but cannot transform new raw data because no search index is available.

## Reproducible layouts versus speed

Reproducible run:

```python
mapper1 = umap.UMAP(random_state=42).fit(X)
mapper2 = umap.UMAP(random_state=42).fit(X)
# For the same package/runtime and input, layouts should be repeatable.
```

Speed-oriented run:

```python
mapper = umap.UMAP(random_state=None, n_jobs=-1).fit(X)
```

Rules of thumb:

- Set `random_state` for repeatable layouts and reports.
- Leave `random_state=None` for best multicore speed when exact repeatability is not required.
- If both `random_state` and `n_jobs != 1` are provided, UMAP warns and changes effective `n_jobs` to `1`.
- UMAP uses numba; first calls may include JIT compilation overhead.
- You can limit numba threads with the `NUMBA_NUM_THREADS` environment variable before Python starts.
- Optional `tbb` can improve CPU threading on supported x86 systems when installed via the `tbb` extra, but it is an optimization only and was not required or verified for this core skill.

## Parameter decision checklist

1. **Goal**: visualization usually `n_components=2`; downstream ML features often `n_components=5` to `50`.
2. **Neighborhood scale**: small `n_neighbors` for local structure; large `n_neighbors` for global structure and smoother manifolds.
3. **Cluster tightness**: low `min_dist` for compact clusters; high `min_dist` for more even layouts.
4. **Metric**: match input semantics (`euclidean` for scaled dense continuous features, `cosine`/`correlation` for vector directions, sparse-friendly metrics for sparse matrices, `precomputed` for distance matrices).
5. **Reproducibility**: set `random_state`, accept single-thread behavior.
6. **Memory**: keep `low_memory=True` when memory pressure matters; consider precomputed k-NN for repeated fits.
7. **Small-data approximate path**: use `force_approximation_algorithm=True` only when you intentionally want approximate-neighbor behavior even below the usual exact small-data threshold.
8. **Density preservation**: if the user asks for densMAP, `output_dens`, or density interpretation, route to `../../supervised-density/SKILL.md`.

## Handling repeated rows

If many rows are exact duplicates, set `unique=True` to embed unique rows and map back:

```python
mapper = umap.UMAP(unique=True, n_neighbors=5, random_state=42).fit(X)
embedding = mapper.embedding_
```

This can avoid duplicate points being placed in inconsistent regions. It is invalid for `metric="precomputed"`.

## Serialization and later inspection

UMAP estimators are normal Python objects and are commonly serialized with `pickle` or `joblib` in controlled, trusted environments:

```python
import joblib
joblib.dump(mapper, "mapper.joblib")
mapper = joblib.load("mapper.joblib")
```

Never load untrusted pickle/joblib files. To inspect a trusted fitted object, use the bundled inspector with `--pickle`.
