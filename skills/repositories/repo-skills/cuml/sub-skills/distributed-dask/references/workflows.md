# Workflows

## Prerequisite gate
`cuml.dask` is only available when CUDA and the Dask extras are installed. If the base cuML wheel is present but `dask`, `dask_cuda`, `dask_cudf`, or `raft_dask` are missing, treat distributed coverage as optional-unverified rather than a cuML algorithm failure.

## 1. Start a local GPU cluster
```python
from dask.distributed import Client
from dask_cuda import LocalCUDACluster

cluster = LocalCUDACluster(threads_per_worker=1, device_memory_limit='auto')
client = Client(cluster)
try:
    print(client.dashboard_link)
    ...
finally:
    client.close()
    cluster.close()
```
- One worker per visible GPU is the default OPG pattern.
- Keep `threads_per_worker=1` for most cuML jobs.
- Pass `device_memory_limit` when a worker must be memory bounded.
- For multi-node runs, keep the Dask-CUDA networking configuration separate from the cuML estimator logic.

## 2. Choose an input layout
- Dask Array with CuPy blocks: dense numeric work.
- Dask-cuDF DataFrame / Series: tabular GPU work.
- Row-chunked Dask Array with dense or sparse CuPy blocks: `MultinomialNB` and `TfidfTransformer`.
- If a downstream library needs a pandas-backed Dask DataFrame, use `cuml.dask.common.to_dask_df(dask_cudf_obj)` to convert a Dask-cuDF collection. Do not use that conversion as the default training input for cuML.

Partitioning rule of thumb:
```python
n_workers = len(client.scheduler_info()['workers'])
n_parts = max(1, min(n_samples, n_workers * 2))
```
- `make_blobs`, `make_classification`, and `make_regression` all accept `n_parts`.
- When starting from a cuDF DataFrame, use `dask_cudf.from_cudf(df, npartitions=n_parts)`.
- Persist partitions if you want the workers to keep local copies during repeated fit or predict calls.

## 3. Clustering and decomposition
### KMeans / DBSCAN
- Fit on partitioned GPU collections.
- `predict`, `transform`, and `fit_predict` return the same collection family as the input when the estimator supports it.
- `KMeans` also exposes `score` and sample-weight handling.
- For `DBSCAN`, keep the clustering input partitioned so that each worker has non-empty work.

Example:
```python
from cuml.dask.cluster import KMeans
from cuml.dask.datasets import make_blobs

X, y = make_blobs(
    n_samples=1024,
    n_features=8,
    centers=4,
    n_parts=n_parts,
    client=client,
)
model = KMeans(n_clusters=4, client=client)
model.fit(X)
labels = model.predict(X)
```

### PCA / TruncatedSVD
- Use the distributed decomposition classes when the feature matrix is already partitioned.
- `PCA` supports `fit`, `fit_transform`, `transform`, and `inverse_transform`.
- `TruncatedSVD` supports `fit`, `fit_transform`, `transform`, and `inverse_transform`.
- Keep the input layout consistent with the downstream collection type you want back.

## 4. Linear models
`LinearRegression`, `LogisticRegression`, `Ridge`, `Lasso`, and `ElasticNet` all fit distributed linear-model workflows.

Typical pattern:
```python
from cuml.dask.linear_model import LinearRegression
from cuml.dask.datasets import make_regression

X, y = make_regression(n_samples=2048, n_features=16, n_parts=n_parts, client=client)
model = LinearRegression(client=client)
model.fit(X, y)
pred = model.predict(X)
```
Notes:
- Use these when the data already lives on multiple GPUs or when the dataset is too large for one GPU.
- Keep partition counts balanced; empty partitions can be dropped by the data handler.
- `Ridge` and other synchronized linear models depend on all active workers participating in fit.

## 5. Random forest
`RandomForestClassifier` and `RandomForestRegressor` spread trees across workers.

Recommended workflow:
- start with shuffled, representative partitions
- set `broadcast_data=True` only when you intentionally want to replicate the training data to all workers
- keep `n_estimators` at least as large as the worker count
- use `ignore_empty_partitions=True` only if empty workers are expected and acceptable

```python
from cuml.dask.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=64, client=client)
model.fit(X_train, y_train)
pred = model.predict(X_test)
```

Model collection:
- `get_combined_model()` materializes a single-GPU model when the distributed fit can be collapsed.
- Random forest predictions may combine worker trees through Treelite before collection or serialization.

## 6. Neighbors
`NearestNeighbors`, `KNeighborsClassifier`, and `KNeighborsRegressor`
- fit on partitioned GPU data
- accept cuML-style distributed collections
- return distributed predictions or neighbor tables
- `kneighbors` on `NearestNeighbors` yields distance and index collections

Example:
```python
from cuml.dask.neighbors import NearestNeighbors
nn = NearestNeighbors(client=client)
nn.fit(X)
distances, indices = nn.kneighbors(X)
```

## 7. Preprocessing
Use the distributed preprocessing estimators when you need GPU-aware category encoding on partitioned data.
- `LabelBinarizer`
- `OneHotEncoder`
- `OrdinalEncoder`

Tips:
- prefer `dask_cudf.DataFrame` for tabular categorical columns
- keep categories stable across partitions when possible
- use `inverse_transform` only when the estimator exposes it and the label/category mapping is still intact

## 8. Distributed UMAP
Distributed `UMAP` is transform-only.
- Fit a single-GPU `cuml.UMAP` first.
- Wrap the fitted model with `cuml.dask.manifold.UMAP(model=local_model, client=client)`.
- Call `transform` on a Dask Array or Dask-cuDF collection.

This is the right path when you need distributed inference for an existing embedding model, not distributed training.

## 9. Naive Bayes and TF-IDF
### MultinomialNB
- Input must be a Dask Array with row-only chunking.
- Dense or sparse CuPy blocks are supported.
- Pass `classes=` when you want to avoid inferring them from the distributed labels.

### TfidfTransformer
- Input must be a Dask Array with row-only chunking.
- Use dense or sparse CuPy blocks.
- This is the distributed TF-IDF transformer, not a raw tokenizer or count-vectorizer.

Example sparse path:
```python
from cuml.dask.common import to_sparse_dask_array
from cuml.dask.feature_extraction.text import TfidfTransformer
from cuml.dask.naive_bayes import MultinomialNB

X_counts = to_sparse_dask_array(count_matrix, client)
tfidf = TfidfTransformer(client=client)
X_tfidf = tfidf.fit_transform(X_counts)
nb = MultinomialNB(client=client)
nb.fit(X_tfidf, y)
```

## 10. Synthetic datasets
Use `cuml.dask.datasets.make_blobs`, `make_classification`, and `make_regression` for tiny validation cases.
- They create GPU-backed Dask arrays directly on the cluster.
- Use `n_parts` to control worker partitioning.
- They are the easiest starting point for smoke tests and partitioning experiments.

## 11. Collection and shutdown
- `cuml.dask.common.to_dask_df` is a collection bridge from Dask-cuDF to a pandas-backed Dask DataFrame, not a cuML training primitive.
- `get_combined_model()` is the main way to recover a single-GPU model from some distributed estimators.
- `pickle` and `cloudpickle` can preserve distributed estimator state, but an unfitted object usually needs its `client` reattached before a later fit.
- Always close `client` and `cluster` explicitly when the workflow is done.
