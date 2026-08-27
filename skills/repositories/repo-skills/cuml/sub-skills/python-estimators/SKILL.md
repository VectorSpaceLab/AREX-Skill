---
name: python-estimators
description: "Direct single-GPU cuML Python estimator workflows on NVIDIA GPUs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# python-estimators

Use this sub-skill for direct, GPU-native `cuml` Python estimators on one NVIDIA GPU. The expected workflow is scikit-learn-style construction plus `fit`, `predict`, `transform`, `fit_predict`, or `fit_transform`, with explicit handling of GPU inputs, output containers, validation, and trusted model persistence.

## Route here when

- Rewriting or authoring explicit `cuml` estimator code rather than keeping scikit-learn imports unchanged.
- Choosing among single-GPU estimator families: clustering, linear models, random forests, decomposition, nearest neighbors, SVMs, manifold learning, or estimator-like time-series models.
- Controlling `output_type`, `set_global_output_type`, `using_output_type`, fitted attributes, prediction outputs, or safe pickle/joblib round-trips.
- Running a tiny single-GPU validation before a larger workflow.
- Debugging direct estimator failures caused by CUDA visibility, RMM memory, input containers, dtypes, output conversion, model state, or serialization.

## Route away

- `cuml.dask`, Dask-CUDA, multi-GPU, or multi-node workflows -> sibling sub-skill `distributed-dask`.
- Zero-code-change acceleration for existing scikit-learn, UMAP, or HDBSCAN code -> sibling sub-skill `sklearn-accel`.
- Detailed dataset generation, preprocessing, metrics, model selection, text features, explainers, or time-series utility schemas -> sibling sub-skill `data-pipeline-utilities`.
- Source builds, C++ APIs, native CI test selection, CUDA compiler, or linker/toolchain issues -> sibling sub-skill `native-build-and-cpp` or root troubleshooting.

## Covered estimator families

- Clustering: `KMeans`, `DBSCAN`, `HDBSCAN` plus HDBSCAN approximate prediction and membership helper routing notes.
- Linear models: `LinearRegression`, `LogisticRegression`, `Ridge`, `Lasso`, `ElasticNet`.
- Ensembles: `RandomForestClassifier`, `RandomForestRegressor`.
- Decomposition: `PCA`, `TruncatedSVD`.
- Neighbors: `NearestNeighbors`, `KNeighborsClassifier`, `KNeighborsRegressor`.
- SVMs: `SVC`, `SVR`, `LinearSVC`, `LinearSVR`.
- Manifold route notes: `UMAP`, `TSNE`.
- Estimator-like time-series route notes: `ARIMA`, `AutoARIMA`, `ExponentialSmoothing` with deprecation cautions.

## Operating procedure

1. Read `references/api-reference.md` to select the estimator family and confirm constructor defaults, common methods, output-type behavior, and routing boundaries.
2. Read `references/workflows.md` for direct fit/predict/transform recipes, health checks, output-type management, serialization, and tiny validation patterns.
3. Read `references/troubleshooting.md` before changing environments when imports, CUDA, RMM, input shape/type, fitted-state, or pickle/joblib behavior fails.
4. Keep work single-GPU unless the user explicitly asks for Dask; select a GPU before Python starts with `CUDA_VISIBLE_DEVICES` when the host has multiple GPUs.
5. Validate tiny code paths before scaling data. From this sub-skill directory, use:

   ```bash
   python scripts/single_gpu_estimator_smoke.py --help
   python scripts/single_gpu_estimator_smoke.py --case all --check-pickle
   ```

Do not claim CPU fallback for direct `cuml` estimators. A CUDA-capable cuML installation and visible NVIDIA GPU are required for runtime proof.
