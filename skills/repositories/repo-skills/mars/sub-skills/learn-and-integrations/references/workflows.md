# Mars Learn Workflows

## Purpose

Read this when the user asks for a small Mars Learn estimator workflow or an
optional integration route.

## 1) Tiny PCA workflow

```python
import mars
import mars.tensor as mt
from mars.learn.decomposition import PCA

mars.new_session()
X = mt.random.RandomState(0).rand(20, 3, chunk_size=10)
pca = PCA(n_components=2)
pca.fit(X)
X2 = pca.transform(X)
print(X2.shape)
mars.stop_server()
```

Use this when the user wants a safe CPU smoke or a pattern for a
scikit-learn-like estimator.

## 2) Tiny nearest-neighbor workflow

```python
import mars.tensor as mt
from mars.learn.neighbors import NearestNeighbors

X = mt.random.RandomState(0).rand(20, 3, chunk_size=10)
nn = NearestNeighbors(n_neighbors=2)
nn.fit(X)
distances, indices = nn.kneighbors(X[:3])
```

Use this for shape/debug checks and nearest-neighbor questions.

## 3) Dask-on-Mars route

Use Dask-on-Mars when the user already thinks in Dask delayed or collection
objects and wants Mars to be the scheduler.

Key checks:
- Real `dask` must be installed.
- If `mars_scheduler` or `convert_dask_collection` is a placeholder, the
  optional Dask dependency is absent.
- Do not use a Dask distributed client for this route unless the user explicitly
  asks for a separate Dask runtime.

## 4) Deep-learning script integration route

Use `run_pytorch_script` or `run_tensorflow_script` when the user wants Mars to
launch a worker-side training script. Before running:

- Verify the framework package is installed.
- Confirm `n_workers` and, for TensorFlow, `n_ps`.
- Decide whether `gpu=True` is required; if so, route backend prerequisites to
  `deployment-and-backends`.
- Keep any smoke script tiny.

## 5) XGBoost, LightGBM, and Statsmodels route

Use these only after the optional package is installed and importable. For
training-scale tasks, first ask for data size, backend/runtime, and acceptable
runtime because these integrations can start distributed work.

## 6) Joblib route

Use this when scikit-learn already frames the workload and you want Mars to act
as the joblib backend.

Key checks:
- Import `register_mars_backend` from `mars.learn.contrib.joblib` and call it
  before entering the `joblib.parallel_backend('mars', ...)` context.
- Use either `service='http://<host>:<port>'` or an existing `session=sess`.
- Keep the workload small enough to fit the single-machine data model that
  joblib expects.

## 7) Proxima route

Use this when the user explicitly wants approximate nearest-neighbor search
backed by the optional Proxima runtime.

Key checks:
- Verify `pyproxima2` imports; if it does not, explain that the Proxima route
  is unavailable.
- Prefer `NearestNeighbors(algorithm='proxima', metric='l2')` for ordinary Mars
  usage.
- Use `mars.learn.proxima.simple_index.build_index` and `search_index` only
  when the user asks for direct index control.

## 8) When to route away

- Pure tensor/DataFrame preprocessing -> `tensor-dataframe-core`.
- Generic remote function DAG -> `remote-and-scripts`.
- Backend selection, GPU devices, Ray, Kubernetes, or YARN ->
  `deployment-and-backends`.
