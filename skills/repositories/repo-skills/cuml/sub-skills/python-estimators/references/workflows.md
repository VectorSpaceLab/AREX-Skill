# python-estimators workflows

This file turns the API catalog into small, repeatable workflows for direct
single-GPU cuML estimators.

## 1) Choose the estimator family

- **Clustering with centroids**: `KMeans`
- **Density clustering**: `DBSCAN` or `HDBSCAN`
- **Linear baselines**: `LinearRegression`, `LogisticRegression`, `Ridge`, `Lasso`, `ElasticNet`
- **Tree-based tabular models**: `RandomForestClassifier`, `RandomForestRegressor`
- **Dimensionality reduction**: `PCA`, `TruncatedSVD`
- **Neighbor search or k-NN prediction**: `NearestNeighbors`, `KNeighborsClassifier`, `KNeighborsRegressor`
- **Margin-based models**: `SVC`, `SVR`, `LinearSVC`, `LinearSVR`
- **Embeddings**: `UMAP`, `TSNE`
- **Time-series compatibility**: `ARIMA`, `AutoARIMA`, `ExponentialSmoothing` when you intentionally need the deprecated `cuml.tsa` family

If the code must stay unchanged and only be accelerated, hand off to the
`sklearn-accel` sub-skill instead. If the workflow needs Dask, use
`distributed-dask`.

## 2) Tiny validation pattern

Use a tiny synthetic dataset, a fixed seed, and a single explicit output type.
The smoke path should stay small enough that a future agent can run it quickly
while still proving that the estimator family is wired correctly.

```python
with cuml.using_output_type("numpy"):
    model = KMeans(n_clusters=3, random_state=0)
    labels = model.fit_predict(X)
```

For host-side comparisons, `numpy` is the easiest output type. Use `input` only
when you intentionally want results to follow the caller's input type.

## 3) Clustering workflows

### KMeans

- Fit with `fit` or `fit_predict`
- Reuse with `predict`
- Validate with an external clustering metric such as adjusted Rand index

```python
from cuml.cluster import KMeans
from cuml.datasets import make_blobs
from cuml.metrics import adjusted_rand_score

X, y = make_blobs(n_samples=96, n_features=6, centers=3, cluster_std=0.35, random_state=0)
model = KMeans(n_clusters=3, n_init=2, random_state=0, output_type="numpy")
labels = model.fit_predict(X)
score = adjusted_rand_score(y, labels)
```

### DBSCAN / HDBSCAN

- Use `fit_predict` when the cluster labels are the main result
- Prefer `HDBSCAN(prediction_data=True, ...)` if you need approximate prediction or membership vectors later
- Keep `HDBSCAN` in this sub-skill for explicit GPU control; route unchanged HDBSCAN code to `sklearn-accel`

```python
from cuml.cluster import DBSCAN, HDBSCAN

labels = DBSCAN(eps=0.4, min_samples=5).fit_predict(X)
hdb = HDBSCAN(min_cluster_size=8, prediction_data=True)
hdb_labels = hdb.fit_predict(X)
```

## 4) Linear, forest, and SVM workflows

### Linear models

- Use `LinearRegression` for a fast regression baseline
- Use `LogisticRegression` for linear classification
- Use `Ridge`, `Lasso`, or `ElasticNet` when regularization matters
- Validate with `.score(...)` or a simple metric on a holdout split

```python
from cuml import LinearRegression
from cuml.datasets import make_regression
from cuml.model_selection import train_test_split

X, y = make_regression(n_samples=128, n_features=12, n_informative=8, random_state=0)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)
model = LinearRegression(output_type="numpy")
model.fit(X_train, y_train)
r2 = model.score(X_test, y_test)
```

### Random forest

- Cast classification targets to integer labels
- Use `score` for a quick accuracy check
- Keep the model tiny: a few estimators and shallow depth is enough for a smoke run

```python
from cuml.ensemble import RandomForestClassifier
from cuml.datasets import make_classification
from cuml.model_selection import train_test_split

X, y = make_classification(
    n_samples=160,
    n_features=12,
    n_informative=8,
    n_redundant=0,
    n_classes=2,
    n_clusters_per_class=1,
    class_sep=1.5,
    random_state=0,
)
X = X.astype("float32")
y = y.astype("int32")
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)
model = RandomForestClassifier(n_estimators=10, max_depth=4, random_state=0)
model.fit(X_train, y_train)
accuracy = model.score(X_test, y_test)
```

### SVMs

- Use `SVC` / `SVR` for kernelized fits
- Use `LinearSVC` / `LinearSVR` for linear margin models
- Keep the data dense and tiny for smoke runs unless a sparse case is the point of the exercise

```python
from cuml import SVC
svc = SVC(output_type="numpy")
svc.fit(X_train, y_train)
preds = svc.predict(X_test)
```

## 5) Decomposition and embeddings

### PCA / TruncatedSVD

- Use `fit_transform` when the embedding is the main output
- Use `inverse_transform` only when you need to reconstruct or inspect a low-dimensional approximation

```python
from cuml.decomposition import PCA
embedding = PCA(n_components=2, output_type="numpy").fit_transform(X)
```

### UMAP / TSNE

- Use `UMAP` when you want a nonlinear embedding plus `transform`
- Use `TSNE` when the workflow is visualization-only and `fit_transform` is the desired endpoint
- If unchanged UMAP code should be accelerated instead of rewritten, route to `sklearn-accel`

```python
from cuml.manifold import UMAP, TSNE
umap_embedding = UMAP(n_neighbors=10, output_type="numpy").fit_transform(X)
tsne_embedding = TSNE(n_components=2, output_type="numpy").fit_transform(X)
```

## 6) Neighbor search workflows

- `NearestNeighbors` is the pure search primitive
- `KNeighborsClassifier` / `KNeighborsRegressor` are the supervised prediction variants
- Distances may differ slightly from scikit-learn because the current exact search path uses FAISS and single-precision arithmetic
- If you compare distances across libraries, allow a tolerance and focus on indices when possible

```python
from cuml.neighbors import NearestNeighbors
nn = NearestNeighbors(n_neighbors=5, output_type="numpy").fit(X)
distances, indices = nn.kneighbors(X[:10])
```

## 7) Time-series workflows

The `cuml.tsa` family is deprecated, so treat these as compatibility workflows
rather than the default route.

- `ARIMA`: fit, then `predict` or `forecast`
- `AutoARIMA`: fit, then `predict` or `forecast`
- `ExponentialSmoothing`: fit, then `forecast`, `score`, or the component getters

```python
from cuml import ARIMA
model = ARIMA(endog, order=(1, 1, 1), output_type="numpy")
model.fit()
forecast = model.forecast(5)
```

## 8) Output control

- Use `output_type="numpy"` in smoke runs so assertions stay simple
- Use `cuml.set_global_output_type(...)` when you want a process-wide default
- Use `cuml.using_output_type(...)` when you want a local override for a small scope
- Keep the setting stable for the whole fit/predict/transform cycle when you are comparing results or validating a pickle round-trip

## 9) Safe persistence

Only load trusted local artifacts.

```python
import pickle
from pathlib import Path

path = Path("model.pkl")
with path.open("wb") as fh:
    pickle.dump(model, fh, protocol=5)
with path.open("rb") as fh:
    restored = pickle.load(fh)
```

- Use `pickle` or `joblib` only for artifacts you trust
- Keep the same cuML version for save and load when possible
- After loading, re-run a tiny prediction check and compare the result to the pre-save output
- If a downstream consumer needs a scikit-learn-shaped object, use `as_sklearn()` / `from_sklearn()` conversion separately from persistence

## 10) Device and memory notes

- Single-GPU cuML methods run on device 0 by default
- Pin a specific GPU with `CUDA_VISIBLE_DEVICES`
- For memory pressure, prefer RMM-managed allocators such as `CudaAsyncMemoryResource` or `ManagedMemoryResource` with a prefetch adaptor instead of ad hoc changes to the workflow
