# Learn and Integration Troubleshooting

## Core estimator failures

### `fit` or `transform` executes sooner than expected

**Symptoms**
- A Mars Learn method starts progress output immediately.

**Likely cause**
- Mars Learn follows a scikit-learn-like API where `fit`, `predict`, and similar
  methods often trigger execution internally.

**Recovery**
- Start a small local session before the estimator workflow.
- Keep smoke data tiny and deterministic.

### Shape mismatch in `PCA`, `KMeans`, or `NearestNeighbors`

**Symptoms**
- Estimator errors mention dimensions, unknown shape, or invalid inputs.

**Likely cause**
- The Mars tensor/DataFrame shape does not match the estimator's expected
  2-dimensional sample-by-feature layout.

**Recovery**
- Check `X.shape` before fitting.
- Use tiny deterministic data from `mt.random.RandomState` for debugging.

## Optional integration failures

### Dask-on-Mars import returns a placeholder or fails

**Symptoms**
- `mars_scheduler` or `convert_dask_collection` is a placeholder object, or
  `dask` imports fail.

**Likely cause**
- The optional `dask` dependency is not installed.

**Recovery**
- Install `dask` only if the user needs the Dask route.
- Re-run a tiny delayed-object example after installation.

### PyTorch or TensorFlow script launch fails

**Symptoms**
- Missing `torch` or `tensorflow`, `WORLD_SIZE`, `TF_CONFIG`, process-group, or
  device errors.

**Likely causes**
- Framework package missing.
- Worker count or process-group environment does not match the script.
- GPU requested without a verified backend.

**Recovery**
- Verify the framework import first.
- Keep `n_workers` and script assertions aligned.
- Route GPU/backend setup to `deployment-and-backends`.

### XGBoost, LightGBM, or Statsmodels wrappers fail to import

**Symptoms**
- `ImportError` for `xgboost`, `lightgbm`, or `statsmodels`.

**Likely cause**
- Optional package absent from the environment.

**Recovery**
- Install only the requested optional package.
- Confirm a minimal import before running any training.

### Joblib backend registration or execution fails

**Symptoms**
- `joblib.parallel_backend('mars')` raises an error or the workload does not
  execute through Mars.

**Likely causes**
- `register_mars_backend()` was not called.
- `joblib` is missing.
- No Mars session or service endpoint was supplied to the backend.

**Recovery**
- Import `register_mars_backend` from `mars.learn.contrib.joblib` and call it
  before entering the joblib backend context.
- Verify `joblib` imports.
- Retry with either `service='http://<host>:<port>'` or an existing session.

### Proxima nearest-neighbor route is unavailable

**Symptoms**
- `ImportError: pyproxima2`
- `NearestNeighbors(algorithm='proxima')` rejects the algorithm.

**Likely cause**
- The optional Proxima runtime is not installed.

**Recovery**
- Install `pyproxima2` only if the user explicitly needs the Proxima route.
- Otherwise fall back to a standard Mars `NearestNeighbors` algorithm or
  another supported ANN path.

### Training-scale integration runs are too slow

**Symptoms**
- A verification attempt begins a long training or distributed job.

**Likely cause**
- The task moved from API guidance into benchmark or training-scale execution.

**Recovery**
- Stop and ask for explicit runtime, data, backend, and budget constraints.
- Use a tiny synthetic smoke for the skill, and record the real training run as
  a separate downstream task.
