---
name: distributed-dask
description: "Route cuML multi-GPU and distributed Dask workflows through
  LocalCUDACluster, partitioned data, supported estimators, and model
  collection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# distributed-dask

Use this sub-skill for cuML workloads that need `cuml.dask`, `dask_cuda.LocalCUDACluster`, or multi-GPU / multi-node execution.

## Use this sub-skill when
- the user wants a Dask-CUDA cluster for cuML training or inference
- data must be partitioned across workers before fitting or transforming
- the workflow needs a distributed `cuml.dask` estimator, dataset helper, or model collection step
- a quick smoke is needed to confirm optional Dask dependencies and CUDA visibility

## Route elsewhere when
- the request is a single-GPU `cuml` estimator or utility workflow -> use `python-estimators`
- the request is a source build, C++ example, or MPI/C++ debugging task -> use `native-build-and-cpp`
- the request is generic Dask administration that does not involve cuML -> out of scope

## Covered families
- clustering: `KMeans`, `DBSCAN`
- decomposition: `PCA`, `TruncatedSVD`
- ensemble: `RandomForestClassifier`, `RandomForestRegressor`
- linear models: `LinearRegression`, `LogisticRegression`, `Ridge`, `Lasso`, `ElasticNet`
- manifold: distributed `UMAP` transform around a fitted single-GPU model
- naive bayes: `MultinomialNB`
- neighbors: `NearestNeighbors`, `KNeighborsClassifier`, `KNeighborsRegressor`
- preprocessing: `LabelBinarizer`, `OneHotEncoder`, `OrdinalEncoder`
- text feature extraction: `TfidfTransformer`
- synthetic datasets: `make_blobs`, `make_classification`, `make_regression`

## Operating sequence
1. Check that the Dask optional dependencies and CUDA runtime are present.
2. Start `LocalCUDACluster` and `Client`.
3. Partition data into Dask Array or Dask-cuDF collections.
4. Fit, predict, or transform with the chosen estimator family.
5. Collect combined models or outputs when the estimator supports that pattern.
6. Close the client and cluster explicitly.

See `references/workflows.md` for the exact data-layout patterns and `references/troubleshooting.md` for dependency and cluster failures. Use `scripts/dask_cuml_smoke.py` for a tiny parser / dependency / fit smoke.
