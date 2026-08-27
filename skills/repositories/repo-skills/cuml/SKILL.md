---
name: cuml
description: "cuML operating skill for GPU-accelerated classical ML, cuml.accel,
  Dask multi-GPU workflows, data utilities, and native source-build guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# cuML

Use this repo skill for NVIDIA cuML tasks: direct GPU-native Python estimators, zero-code-change `cuml.accel` acceleration, `cuml.dask` multi-GPU workflows, supporting data/metrics/preprocessing utilities, or cuML source-build and C++/CUDA maintenance.

cuML is a CUDA/RAPIDS package. Direct `cuml` runtime proof requires a CUDA-capable installation and an NVIDIA GPU; CPU-only imports are not a substitute for estimator execution.

## First checks

1. Confirm the task is about cuML/RAPIDS GPU machine learning, `cuml.accel`, `cuml.dask`, `libcuml`, or source-build/C++ APIs.
2. Read `references/repo-provenance.md` when deciding whether this skill is current for a checkout or when refreshing it.
3. Read `references/package-overview.md` for package surfaces, install variants, required/optional dependencies, output/device/memory behavior, and supported-version notes.
4. Run the bundled probe when an installed package is expected:

   ```bash
   python scripts/cuml_environment_probe.py --checks import cuda
   python scripts/cuml_environment_probe.py --checks import cuda health optional
   ```

5. If any check fails, read `references/troubleshooting.md` before changing dependencies or broadening the scope.

## Route by task

| User task | Read |
| --- | --- |
| Write, convert, debug, or validate direct single-GPU `cuml` estimator code with `fit`, `predict`, `transform`, output types, or model persistence. | `sub-skills/python-estimators/SKILL.md` |
| Keep existing scikit-learn, UMAP, or HDBSCAN code unchanged and accelerate it with `python -m cuml.accel`, notebook magics, environment variables, or programmatic activation. | `sub-skills/sklearn-accel/SKILL.md` |
| Build a `cuml.dask` workflow with Dask-CUDA, partitioned data, multi-GPU estimators, LocalCUDACluster, or distributed model collection. | `sub-skills/distributed-dask/SKILL.md` |
| Generate synthetic data, split/encode/scale data, compute metrics, vectorize text, use explainers, or prepare time-series utility inputs. | `sub-skills/data-pipeline-utilities/SKILL.md` |
| Build cuML from source, diagnose `libcuml`/CMake/CUDA toolchain issues, select native tests, or work with C++ examples/APIs. | `sub-skills/native-build-and-cpp/SKILL.md` |

## Installation and backend guidance

- Prefer the RAPIDS installation selector for current release/nightly commands and choose the CUDA/Python/package-manager combination that matches the host.
- Pip package names are CUDA-suffixed in current RAPIDS wheels, for example `cuml-cu12` or `cuml-cu13`; dependencies such as `libcuml`, `cudf`, `rmm`, `pylibraft`, and CuPy must match the same CUDA/RAPIDS generation.
- `cuml.dask` requires additional Dask RAPIDS dependencies (`rapids-dask-dependency`, `dask-cudf`, `raft-dask`) matching the cuML version; `dask-cuda`/`dask-ml` are needed for many test or local-cluster workflows.
- `cuml.accel` should be enabled before importing scikit-learn, UMAP, or HDBSCAN. Unsupported estimators, inputs, parameters, or versions fall back to CPU and should be diagnosed with logging/profiling rather than treated as cuML estimator failures.
- Source builds are separate from ordinary package use. They need a full CUDA/toolchain/RAPIDS development environment and should start with the non-mutating probe in `sub-skills/native-build-and-cpp/scripts/source_build_probe.py`.

## Validation policy

- Always validate with tiny generated data before scaling to production-sized datasets.
- Prefer quality metrics (`accuracy_score`, `r2_score`, adjusted Rand score, trustworthiness) over exact coefficient or label equality when comparing GPU and CPU algorithms.
- For model serialization, load only trusted pickle/joblib artifacts. Do not unpickle data from untrusted sources.
- For direct `cuml`, do not claim a CPU fallback. For `cuml.accel`, CPU fallback is expected for unsupported operations and should be made visible.
- For Dask and source-build workflows, distinguish optional unverified capability from required CUDA runtime failures.

## Generated helpers

- `scripts/cuml_environment_probe.py`: shared import/CUDA/health/optional dependency check for installed cuML.
- `sub-skills/python-estimators/scripts/single_gpu_estimator_smoke.py`: tiny KMeans, LinearRegression, RandomForest, and pickle checks.
- `sub-skills/sklearn-accel/scripts/cuml_accel_smoke.py`: accelerator CLI/programmatic/profiling checks.
- `sub-skills/distributed-dask/scripts/dask_cuml_smoke.py`: optional LocalCUDACluster + distributed KMeans smoke with missing-dependency diagnostics.
- `sub-skills/data-pipeline-utilities/scripts/data_utility_smoke.py`: datasets, preprocessing, and metric checks.
- `sub-skills/native-build-and-cpp/scripts/source_build_probe.py`: non-mutating source-build prerequisite probe.

## Avoid using this skill when

- The task is general scikit-learn usage with no GPU/RAPIDS/cuML surface.
- The task is generic Dask administration rather than cuML estimators on Dask collections.
- The task is CUDA kernel development unrelated to cuML/libcuml APIs.
- The task requires downloading external datasets or running long benchmarks without explicit user approval.
