# Troubleshooting

## Optional Dask extras are missing
Symptom: `import cuml.dask` or `from dask_cuda import LocalCUDACluster` raises `ModuleNotFoundError`.

Likely cause: the base cuML wheel is installed, but the Dask extras are not.
Fix:
- pip: `pip install 'cuml-cu13[dask]'`
- conda: `conda install rapids-dask-dependency dask-cudf raft-dask`
Use the version family that matches the installed cuML build.

Treat missing Dask extras as optional-unverified coverage in the minimum environment, not as a failure of the core cuML package.

If the `cuml.dask` import itself reports that cuML was not built with multiGPU support, hand the task to the native-build path instead of debugging the distributed workflow here.

## `LocalCUDACluster` starts but no workers appear
Likely cause: no visible CUDA devices, `CUDA_VISIBLE_DEVICES` masks the GPUs, or the cluster cannot start its worker processes.
Fix:
- confirm `nvidia-smi` sees the expected GPUs
- keep `threads_per_worker=1`
- pass `device_memory_limit` only when needed
- verify that the Dask scheduler sees one worker per visible GPU

## `Data was not split among all workers`
Likely cause: too many workers for the sample count or too many partitions.
Fix:
- increase `n_parts`
- reduce the worker count for a tiny smoke
- ensure each partition has rows
- for `RandomForest*`, use `ignore_empty_partitions=True` when empty workers are expected
- for other estimators, keep the data non-empty on every active worker because the data handler prunes empty partitions automatically

## `n_estimators cannot be lower than number of dask workers`
Likely cause: the random forest was asked to fit fewer trees than active workers.
Fix:
- raise `n_estimators`
- or reduce the worker count for the smoke

## `X must be chunked by row only`
Likely cause: `MultinomialNB` or `TfidfTransformer` got a multi-dimensional chunk layout.
Fix:
- repartition so only the first axis is chunked
- keep text and count inputs as Dask Arrays of CuPy blocks
- do not pass a Dask-cuDF frame directly to these paths

## `to_dask_df` produced a CPU-backed collection
Likely cause: `to_dask_df` intentionally converts `dask_cudf` partitions to a pandas-backed Dask DataFrame.
Fix:
- use it only when a downstream consumer needs a generic Dask DataFrame
- keep training inputs on `dask_cudf` or Dask Array for cuML

## `get_combined_model()` fails or returns `None`
Likely cause: the estimator has not been fit yet, or the model is composite and cannot be collapsed into one instance.
Fix:
- call `fit` first
- for random forest, expect Treelite-style model combination after fit
- for nearest-neighbor brute-force paths, a combined model may not exist

## `UMAP` transform fails
Likely cause: the distributed wrapper received an unfitted model.
Fix:
- fit `cuml.UMAP` on one GPU first
- pass the fitted model to `cuml.dask.manifold.UMAP(model=...)`
- remember that the wrapper is transform-only

## Pickle and unpickle workflow fails later
Likely cause: a deserialized estimator does not yet have a live `client` for new distributed work.
Fix:
- assign `unpickled_model.client = client` before refitting if needed
- keep the client and cluster alive while you collect results or combined models

## Multi-node runs hang or mismatch workers
Likely cause: network or communication setup is incomplete.
Fix:
- validate the local single-node smoke first
- then check UCX, NCCL, firewall, and host reachability
- keep the cuML workflow separate from general Dask administration
