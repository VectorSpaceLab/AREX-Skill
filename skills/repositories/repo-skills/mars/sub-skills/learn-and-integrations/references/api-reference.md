# Mars Learn and Integration API Reference

## Purpose

Read this for representative Mars Learn estimator signatures and optional integration
entry points.

## Core Mars Learn estimators

The installed package verified these representative signatures:

```python
from mars.learn.cluster import KMeans
KMeans(n_clusters=8, init='k-means||', n_init=1, max_iter=300, tol=0.0001,
       verbose=0, random_state=None, copy_x=True, algorithm='auto',
       oversampling_factor=2, init_iter=5)
```

```python
from mars.learn.decomposition import PCA
PCA(n_components=None, copy=True, whiten=False, svd_solver='auto', tol=0.0,
    iterated_power='auto', random_state=None)
```

```python
from mars.learn.neighbors import NearestNeighbors
NearestNeighbors(n_neighbors=5, radius=1.0, algorithm='auto', leaf_size=30,
                 metric='minkowski', p=2, metric_params=None, **kwargs)
```

Use these for tiny CPU examples before moving to optional integrations.

## Other core namespaces

- `mars.learn.datasets`: sample generation such as `make_blobs`.
- `mars.learn.decomposition`: PCA and SVD-style dimensionality reduction.
- `mars.learn.cluster`: clustering estimators.
- `mars.learn.neighbors`: nearest-neighbor estimators.
- `mars.learn.metrics`: classification, ranking, regression, scorer, and
  pairwise metrics.
- `mars.learn.preprocessing`, `mars.learn.model_selection`, and wrappers for
  scikit-learn-like workflows.

## Optional integration entry points

| Integration | Entry points | Representative signature or behavior | Dependency note |
|---|---|---|---|
| Dask-on-Mars | `mars.contrib.dask.mars_scheduler`, `convert_dask_collection` | When `dask` is absent, both names resolve to `ModulePlaceholder("dask")`; otherwise use the scheduler or conversion helpers from the bundled Dask integration. | Install `dask` before using this route. |
| PyTorch | `mars.learn.contrib.pytorch.run_pytorch_script` | `run_pytorch_script(script, n_workers, data=None, gpu=None, command_argv=None, retry_when_fail=False, session=None, run_kwargs=None, port=None)` | Requires `torch` for real execution; GPU is optional but backend-specific. |
| TensorFlow | `mars.learn.contrib.tensorflow.run_tensorflow_script` | `run_tensorflow_script(script, n_workers, n_ps=0, data=None, gpu=None, command_argv=None, retry_when_fail=False, session=None, run_kwargs=None)` | Requires `tensorflow` for real execution. |
| XGBoost | `mars.learn.contrib.xgboost.train`, `predict` | `train(params, dtrain, evals=(), **kwargs)` and `predict(model, data, output_margin=False, ntree_limit=None, validate_features=True, base_margin=None, session=None, run_kwargs=None, run=True)` | Requires `xgboost` for real training/prediction. |
| LightGBM | `LGBMClassifier`, `LGBMRegressor`, `LGBMRanker` | Wrapper constructors are dynamically forwarded. | Requires `lightgbm`. |
| Statsmodels | `MarsDistributedModel`, `MarsResults` | `MarsDistributedModel(factor=None, num_partitions=None, model_class=None, init_kwds=None, estimation_method=None, estimation_kwds=None, join_method=None, join_kwds=None, results_class=None, results_kwds=None)` | Requires `statsmodels` for real model classes. |
| Joblib | `mars.learn.contrib.joblib.register_mars_backend`, `joblib.parallel_backend('mars', ...)` | Register Mars as a joblib backend before wrapping a scikit-learn workload. | Requires `joblib`; use a Mars service endpoint or existing session. |
| Proxima | `NearestNeighbors(algorithm="proxima", metric="l2")`, `mars.learn.proxima.simple_index.build_index`, `search_index` | Approximate nearest-neighbor route for users who explicitly install Proxima. | Requires `pyproxima2` and a compatible Proxima runtime. |

## Execution behavior

- Many Mars Learn methods such as `fit`, `predict`, and `transform` trigger
  execution internally, unlike bare tensor/DataFrame expressions.
- Start with a small local session for verification.
- Optional integrations should be treated as dependency-gated surfaces: import
  and version checks come before training or distributed execution.
