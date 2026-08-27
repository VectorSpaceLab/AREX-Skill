# cuML package overview

## When to read

Read this before choosing a cuML sub-skill, installing dependencies, or deciding whether a failure belongs to direct `cuml`, `cuml.accel`, `cuml.dask`, utility APIs, or source-build/C++ maintenance.

## Core surfaces

- **Direct `cuml` Python API**: GPU-native estimators with scikit-learn-style constructors and `fit`/`predict`/`transform` methods. Use `sub-skills/python-estimators/` for model workflows.
- **`cuml.accel`**: zero-code-change acceleration that intercepts supported scikit-learn, UMAP, and HDBSCAN imports. Unsupported operations fall back to CPU. Use `sub-skills/sklearn-accel/`.
- **`cuml.dask`**: distributed/multi-GPU estimators and dataset helpers on Dask-CUDA/Dask-cuDF collections. Use `sub-skills/distributed-dask/`.
- **Support utilities**: synthetic datasets, preprocessing, metrics, model selection, feature extraction, explainers, and time-series helpers. Use `sub-skills/data-pipeline-utilities/`.
- **`libcuml` and C++/CUDA source builds**: native library, C++ examples, CMake/build/test workflows. Use `sub-skills/native-build-and-cpp/`.

## Required runtime assumptions

- Direct cuML estimator execution requires an NVIDIA GPU and a compatible CUDA/RAPIDS package stack.
- Current Python package metadata requires Python 3.11 or newer and pins RAPIDS dependencies to the same cuML generation.
- Runtime dependencies include NumPy, scikit-learn, SciPy, Numba, CuPy for the selected CUDA generation, Treelite, `libcuml`, cuDF, RMM, and pylibraft.
- CUDA 12 and CUDA 13 wheel families are separated. Match package names and dependencies consistently, such as `cuml-cu12` with CUDA 12 dependencies or `cuml-cu13` with CUDA 13 dependencies.
- For source builds, the build guide requires CUDA Toolkit development libraries, gcc 13+, CMake 4+, Ninja, Python, Cython, and matching RAPIDS C++/Python libraries.

## Optional dependency groups

- **Dask/MNMG**: install RAPIDS Dask dependencies matching the cuML version (`rapids-dask-dependency`, `dask-cudf`, `raft-dask`; many test/local-cluster workflows also need `dask-cuda` and `dask-ml`).
- **`cuml.accel` integrations**: scikit-learn is required by cuML; UMAP and HDBSCAN acceleration needs compatible optional `umap-learn` and `hdbscan` versions.
- **Explainers/export/tests**: SHAP, ONNX-related packages, XGBoost, hdbscan, pynndescent, and plotting/testing dependencies are optional and should be installed only for workflows that need them.

## Device, memory, and output behavior

- Single-GPU cuML methods run on device 0 by default. Select a GPU before Python starts with `CUDA_VISIBLE_DEVICES` when needed.
- cuML uses RAPIDS Memory Manager (RMM). Configure RMM before large allocations if managed memory or async memory resources are desired.
- Some operations may not synchronize outputs before returning. Keep host/device synchronization in mind when mixing custom CUDA streams or external GPU libraries.
- Output containers may be controlled with per-estimator `output_type`, `cuml.set_global_output_type`, or `cuml.using_output_type`. Validate output containers before passing them into CPU-only libraries.

## Result comparison guidance

- GPU and CPU implementations may differ numerically because algorithms and floating-point ordering differ.
- Compare task-appropriate scores or qualities, such as accuracy, R2, adjusted Rand score, log loss, or trustworthiness.
- Do not require exact labels, coefficients, tree structures, or fitted attributes to match scikit-learn unless the API explicitly guarantees it.

## Safety notes

- Only unpickle or joblib-load cuML/scikit-learn models from trusted sources.
- Do not run benchmark-scale notebooks, C++ benchmarks, broad pytest partitions, or external dataset downloads unless the user explicitly asks and the environment budget allows it.
- Treat `cuml.dask` and source-build workflows as optional/additive unless the user explicitly requires them; missing Dask/toolchain dependencies should not be confused with a broken direct `cuml` install.
