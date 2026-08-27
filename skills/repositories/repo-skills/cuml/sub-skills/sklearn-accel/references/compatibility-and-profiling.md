# Compatibility and profiling

## Activation choices

| Path | Use | Notes |
| --- | --- | --- |
| CLI | `python -m cuml.accel script.py` | Best for existing scripts. Trailing arguments are forwarded to the script or module. |
| CLI module | `python -m cuml.accel -m module --args` | Runs a module instead of a file. |
| CLI command | `python -m cuml.accel -c "code"` | Runs inline Python source. |
| Notebook / IPython | `%load_ext cuml.accel` | Load before importing `sklearn`, `umap`, or `hdbscan`. |
| Environment variable | `CUML_ACCEL_ENABLED=1 python script.py` | Useful for third-party apps you cannot edit. |
| Programmatic | `import cuml; cuml.accel.install(disable_uvm=False, log_level=None)` | Call before importing the libraries you want accelerated. |

Public checks:

- `cuml.accel.enabled()` tells you whether the accelerator is active.
- `cuml.accel.is_proxy(obj)` tells you whether a class or instance is a proxy created by the accelerator.
- `cuml.accel.profile(quiet=False)` captures GPU/CPU call statistics and fallback reasons.

Notebook profiling and logging magics:

- `%cuml.accel.log_level [error|warn|info|debug]`
- `%%cuml.accel.profile`
- `%%cuml.accel.line_profile`

## Verified CLI flags

The `python -m cuml.accel` entrypoint accepts:

- `-v` / `--verbose` for logging (`-vv` is more verbose than `-v`)
- `--profile` for the function profiler
- `--line-profile` for the line profiler
- `--disable-uvm` to turn off managed-memory allocation
- `-m MODULE` to run a module
- `-c CMD` to run inline Python source
- a script path plus any trailing arguments to forward to that script

Notes:

- `--line-profile` is not supported with `-m`.
- The CLI preserves the target script or module `sys.argv` layout while forwarding arguments.
- `install()` sets accelerator-related environment variables for subprocesses when possible.

## Tested version window

| Package | Tested range | Behavior outside range |
| --- | --- | --- |
| scikit-learn | `1.6` through `1.9` | Emits a runtime warning and continues. Array API acceleration requires `1.8+`. |
| umap-learn | `0.5.7` through `0.5.12` | Emits a runtime warning and continues. |
| hdbscan | `0.8.39` through `0.8.44` | Emits a runtime warning and continues. |

UMAP also has a stability note: `numba<0.62` is the safer choice when you want to minimize compatibility risk.

## What to expect

- GPU and CPU implementations should be comparable, but not numerically identical.
- Fitted attributes may differ from scikit-learn even when the model is accelerated successfully.
- Compare task metrics such as accuracy, R2, ARI, or trustworthiness instead of relying on exact coefficient equality.
- Small datasets can be slower because import, dispatch, transfer, and warm-up costs dominate.
- First-use compilation overhead is normal for some GPU code paths.
- If managed memory hurts performance, compare a run with `--disable-uvm`.

## Common fallback conditions

| Family | Typical CPU fallback triggers | Notes |
| --- | --- | --- |
| `KMeans` | callable `init`, sparse `X` | `labels_` may not match scikit-learn exactly. |
| `SpectralClustering` | `assign_labels` not `kmeans`, `affinity` not `nearest_neighbors` or `precomputed`, sparse `X` | `affinity_matrix_` is not computed. |
| `DBSCAN` | `algorithm` not `auto` or `brute`, unsupported `metric`, sparse `X` | ONNX export is unsupported. |
| `PCA` | `n_components=0`, `n_components="mle"` | Randomized solver extras are ignored. |
| `TruncatedSVD` | sparse `X` | Randomized solver extras are ignored. |
| `LinearRegression` | `positive=True` | `rank_` and `singular_` are not computed. |
| `LogisticRegression` | `warm_start=True`, `intercept_scaling != 1`, deprecated `multi_class`, callbacks configured | Use model-quality scores to compare runs. |
| `Ridge` | `positive=True`, `solver="lbfgs"` |  |
| `Lasso` / `ElasticNet` | `positive=True`, `warm_start=True`, `precompute != False` | `dual_gap_` is not computed. |
| `RandomForestClassifier` | sparse `X`, `NaN` in `X`, multi-output `y`, plus other parameter-based cases listed in the compatibility notes | Use dense inputs for the GPU path; sparse input is a reliable fallback smoke. |
| `RandomForestRegressor` | sparse `X`, `NaN` in `X`, multi-output `y`, plus other parameter-based cases listed in the compatibility notes | Use dense inputs for the GPU path; sparse input is a reliable fallback smoke. |
| `NearestNeighbors` / `KNeighbors*` | unsupported `metric` | `algorithm` is ignored and `radius_neighbors` falls back to CPU. |
| `TSNE` | `n_components != 2`, array `init`, `init="pca"` with sparse `X`, unsupported `metric` | Results are not fully deterministic. |
| `UMAP` | unsupported `init`, unsupported `metric`, unsupported `target_metric`, `unique=True`, `densmap=True`, `ensure_all_finite` not `True` | Quality may remain good even when coordinates differ. |
| `HDBSCAN` | unsupported `metric`, configured `memory`, `match_reference_implementation=True`, `branch_detection_data=True` | `exemplars_`, `outlier_scores_`, and `relative_validity_` are not computed. |

## When to switch routes

- If you need GPU-native control or repeated fallback-free execution, prefer direct cuML and hand off to `../python-estimators/SKILL.md`.
- If the workflow should run across multiple GPUs or nodes, hand off to `../distributed-dask/SKILL.md`.
