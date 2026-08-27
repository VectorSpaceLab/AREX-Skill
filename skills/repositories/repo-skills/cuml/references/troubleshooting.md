# cuML troubleshooting

## Install or import fails

Symptoms:
- `ModuleNotFoundError: cuml`, `ModuleNotFoundError: libcuml`, or import errors for `cudf`, `rmm`, `pylibraft`, `cupy`.
- CUDA libraries load errors or unresolved symbols.

Likely causes:
- Mixed CUDA wheel families (`cu12` and `cu13` packages together).
- RAPIDS package versions do not match each other.
- Python version outside the supported range for the selected wheels.
- Source checkout shadowing an installed wheel without built extensions.

Recovery:
1. Run `python scripts/cuml_environment_probe.py --checks import cuda --json`.
2. Check package names and versions. Keep cuML, cuDF, RMM, pylibraft, `libcuml`, and CuPy on the same CUDA/RAPIDS generation.
3. Use the RAPIDS install selector to regenerate the install command for the exact CUDA, Python, and package manager.
4. If working from a source checkout, route to `sub-skills/native-build-and-cpp/SKILL.md`; a checkout alone is not an installed cuML runtime.

## CUDA device is missing or unusable

Symptoms:
- `CuPy sees no CUDA devices`, `cudaErrorNoDevice`, `CUDA driver version is insufficient`, or only CPU libraries are visible.
- Direct `cuml` estimator code imports but fails when fitting or allocating device arrays.

Likely causes:
- No NVIDIA GPU, container runtime did not pass GPUs through, or `CUDA_VISIBLE_DEVICES` hides them.
- Driver does not support the CUDA runtime required by installed wheels.
- A CPU-only dependency replaced a CUDA dependency.

Recovery:
1. Run `nvidia-smi` outside Python and `python scripts/cuml_environment_probe.py --checks cuda` inside the intended environment.
2. Select the target GPU before Python starts, for example `CUDA_VISIBLE_DEVICES=0 python your_script.py`.
3. Reinstall a matching CUDA wheel family if package versions are mixed.
4. Do not call a CPU-only environment verified for direct cuML estimator execution. Direct `cuml` has no full CPU substitute.

## Health check CLI behavior is surprising

The package provides `python -m cuml.health_checks` with named checks. Some nightly builds may reject a no-argument invocation even though named checks pass. Prefer explicit checks:

```bash
python -m cuml.health_checks -v import functional accel-basic accel-cli
```

Use the root `scripts/cuml_environment_probe.py --checks health` helper when you want this explicit invocation wrapped with clear output.

## `cuml.accel` does not accelerate a workflow

Symptoms:
- `cuml.accel.enabled()` is false.
- Estimators are not proxy objects.
- Logs/profiling show CPU fallback.

Likely causes:
- `cuml.accel` was enabled after importing scikit-learn, UMAP, or HDBSCAN.
- The estimator, method, parameter value, sparse input, dependency version, or output mode is unsupported.
- The environment variable was silently ignored because cuML was not importable.

Recovery:
1. Read `sub-skills/sklearn-accel/SKILL.md`.
2. Enable acceleration before imports via `python -m cuml.accel script.py`, `%load_ext cuml.accel`, `CUML_ACCEL_ENABLED=1`, or `cuml.accel.install()`.
3. Use `sub-skills/sklearn-accel/scripts/cuml_accel_smoke.py --profile` and the compatibility reference to identify CPU fallback reasons.
4. If fallback is frequent or GPU-specific control is needed, rewrite the workflow with direct `cuml` APIs using `sub-skills/python-estimators/SKILL.md`.

## `cuml.dask` import or cluster startup fails

Symptoms:
- `ModuleNotFoundError: dask`, `dask_cuda`, `dask_cudf`, `raft_dask`, or `cuml.dask`.
- `LocalCUDACluster` starts with the wrong number of workers or workers cannot see GPUs.
- UCX/NCCL communication errors.

Likely causes:
- Dask optional dependencies were not installed.
- Dask RAPIDS package versions do not match cuML.
- GPUs are hidden or oversubscribed.
- UCX/NCCL settings are incompatible with the host/network.

Recovery:
1. Run `python sub-skills/distributed-dask/scripts/dask_cuml_smoke.py --help` and then a tiny smoke if optional dependencies are installed.
2. Install Dask RAPIDS dependencies matching the cuML version.
3. Start with a local single-node cluster before multi-node or multi-GPU scaling.
4. Close `Client` and cluster explicitly after a failed smoke to avoid orphan workers.

## Outputs cannot be consumed by downstream code

Symptoms:
- Downstream CPU libraries reject cuDF/CuPy outputs.
- Predictions or transformed arrays have unexpected container types.

Likely causes:
- Per-estimator or global `output_type` was not set.
- A downstream library expects NumPy/pandas rather than GPU containers.

Recovery:
1. In direct `cuml`, choose `output_type="numpy"`, `"cupy"`, `"cudf"`, or use `cuml.using_output_type(...)` around the relevant call.
2. Validate a tiny prediction/transform before scaling.
3. Route data conversion/preprocessing issues to `sub-skills/data-pipeline-utilities/SKILL.md`.

## Serialization is unsafe or mismatched

Symptoms:
- Pickled/joblib model load fails after package upgrades.
- Loaded model predictions differ unexpectedly.
- The artifact came from an untrusted source.

Recovery:
1. Do not load untrusted pickle/joblib artifacts. Python pickle can execute arbitrary code.
2. Use the same cuML/RAPIDS generation for save and load when practical.
3. After trusted load, run a tiny prediction or transform parity check.
4. See `sub-skills/python-estimators/references/workflows.md` for safe validation patterns.

## Source build or C++ validation fails

Symptoms:
- `nvcc` missing, CMake too old, Ninja missing, compiler mismatch, RAPIDS dependency mismatch, CTest failures, or public header/API build errors.

Recovery:
1. Run `python sub-skills/native-build-and-cpp/scripts/source_build_probe.py` before configuring a build.
2. Read `sub-skills/native-build-and-cpp/references/source-build-and-cpp.md` for the smallest build/test target.
3. Install full source-build dependencies only when the user task requires source edits, C++ APIs, or native tests.
4. Do not run benchmarks or broad CI partitions unless explicitly requested.
