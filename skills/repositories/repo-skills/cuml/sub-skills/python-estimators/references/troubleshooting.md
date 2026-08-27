# python-estimators troubleshooting

## Fast triage

When a direct estimator workflow fails, first separate these three causes:

1. **Backend/import issue**: cuML, libcuml, CuPy, or CUDA is missing or mismatched
2. **Workflow issue**: the wrong estimator family, input shape, or output type was chosen
3. **Persistence issue**: a model was loaded from an untrusted or incompatible artifact

## Common symptoms and fixes

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError` for `cuml`, `libcuml`, or `cupy` | The runtime does not have the cuML stack installed | Reinstall a matching cuML / libcuml / CUDA wheel set in the active environment |
| CUDA runtime / driver errors on import or first fit | GPU or driver mismatch, or the active device is not visible | Check GPU visibility, confirm the driver stack, and pin the target device with `CUDA_VISIBLE_DEVICES` |
| `fit`, `predict`, or `transform` returns the wrong array type | The estimator or global output type was left at the default | Set `output_type="numpy"` for smoke runs, or wrap the workflow with `cuml.using_output_type(...)` |
| `ValueError` or type mismatch during fit | Dense arrays, dtypes, or label encodings do not match the estimator's expectations | Cast feature arrays to `float32` or `float64`, and cast classification targets to integer labels |
| `NotFittedError` or missing fitted attributes | The estimator was used before `fit` completed | Fit first, then call `predict`, `transform`, `score`, `kneighbors`, or `forecast` as appropriate |
| Pickle / joblib load fails after a version change | Serialized artifacts are version-coupled or not trusted | Only load trusted local files and re-fit when the save/load version gap is large |
| Distances from `NearestNeighbors` do not match scikit-learn exactly | FAISS exact search uses single-precision arithmetic in the current path | Compare indices first and allow a tolerance on distances |
| `HDBSCAN` cannot produce approximate predictions or membership vectors | `prediction_data` was not enabled before fitting | Recreate the model with `prediction_data=True` and fit again |
| `TSNE` / `ARIMA` / `ExponentialSmoothing` warns about deprecation | The entire `cuml.tsa` family is deprecated | Keep the workflow only when you intentionally need that compatibility path |
| `python -m cuml.health_checks` rejects an empty invocation | This build expects explicit checks instead of a blank list | Run explicit checks, for example `python -m cuml.health_checks -v import functional accel-basic accel-cli` |

## Output-type surprises

If outputs flip between `cupy`, `cudf`, `pandas`, and `numpy`, fix the output
policy before the model is built:

```python
with cuml.using_output_type("numpy"):
    model = KMeans(n_clusters=3).fit(X)
    labels = model.predict(X)
```

Rules of thumb:

- Use `numpy` when you want easy assertions or host-side post-processing
- Use `input` only when the caller really needs results to mirror the input container
- Avoid mixing output-type policies across a single fit/predict/transform cycle

## Input-shape and dtype problems

Most direct estimator workflows are simplest when you keep the data dense and
numeric.

- Features: 2D arrays or dataframes
- Regression targets: 1D numeric arrays
- Classification targets: integer-coded labels
- Tiny smoke data: keep it well separated and deterministic with a fixed seed

If a workflow needs sparse input, verify that the chosen estimator family really
supports it before debugging the rest of the pipeline.

## Memory and device selection

Single-GPU cuML methods run on device 0 by default.

- Use `CUDA_VISIBLE_DEVICES` to pin the GPU you want
- If memory pressure is the issue, prefer a managed RMM allocator instead of changing the estimator logic
- Keep the smoke data tiny before you widen the sample size or feature count

```python
import rmm

rmm.mr.set_current_device_resource(rmm.mr.CudaAsyncMemoryResource())
# or
rmm.mr.set_current_device_resource(
    rmm.mr.PrefetchResourceAdaptor(rmm.mr.ManagedMemoryResource())
)
```

## Safe serialization reminders

- Only unpickle or load `joblib` files from trusted sources
- Prefer protocol 5 for local pickle round-trips when the artifact stays in your control
- For a quick validation, compare predictions before and after load instead of trusting the load step alone
- If you need a scikit-learn-shaped object for CPU-side tooling, convert with `as_sklearn()` / `from_sklearn()` separately from the persistence step

## Family-specific reminders

- `DBSCAN` / `HDBSCAN`: `fit_predict` is usually the primary call
- `KMeans`: `fit` or `fit_predict` first, then `predict`
- `PCA` / `TruncatedSVD` / `UMAP` / `TSNE`: use `fit_transform` when the embedding is the goal
- `NearestNeighbors`: compare both distances and indices, but allow a tolerance on distances
- `ARIMA`: `fit` first, then `predict` or `forecast`
- `ExponentialSmoothing`: `fit` first, then `forecast`, `score`, or the component getters

## When to stop debugging this sub-skill

If the problem is actually one of these, hand it to the sibling sub-skill instead:

- zero-code-change acceleration of existing sklearn / UMAP / HDBSCAN code -> `sklearn-accel`
- distributed or multi-GPU estimator work -> `distributed-dask`
- data generation, preprocessing, metrics, or model selection -> `data-pipeline-utilities`
- source build or native C++ issues -> `native-build-and-cpp`
