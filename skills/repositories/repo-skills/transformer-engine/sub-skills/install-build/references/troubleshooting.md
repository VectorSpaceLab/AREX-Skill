# Install and build troubleshooting

Use this reference by matching the symptom first, then applying the narrowest
fix. Avoid reinstalling all frameworks or adding broad development extras unless
the matched symptom proves they are required.

## Missing Transformer Engine shared objects

**Symptoms**

- `FileNotFoundError: Could not find shared object file for Transformer Engine torch lib`
- `FileNotFoundError: Could not find shared object file for Transformer Engine jax lib`
- Top-level `import transformer_engine` warns that PyTorch or JAX is installed
  but the matching Transformer Engine extension library is missing.

**Likely cause**

The core package or metapackage is installed, but the selected framework
extension was not installed or not built. A source build may also have used
`NVTE_FRAMEWORK=none` or autodetected only the other framework.

**Fix**

- PyPI: reinstall the exact framework extra needed, for example
  `python -m pip install --no-build-isolation 'transformer_engine[pytorch]'` or
  `python -m pip install --no-build-isolation 'transformer_engine[jax]'`.
- Source: rebuild with explicit `NVTE_FRAMEWORK=pytorch`, `NVTE_FRAMEWORK=jax`,
  or `NVTE_FRAMEWORK=all`.
- During validation, set `NVTE_FRAMEWORK` to the expected framework so missing
  extensions fail loudly instead of becoming warnings.

## Empty metapackage without core/extensions

**Symptom**

`RuntimeError: Found empty transformer-engine meta package installed.`

**Likely cause**

The top-level metapackage was installed without `core`, `pytorch`, or `jax`
extras.

**Fix**

Install one of the real payload extras:

```bash
python -m pip install 'transformer_engine[core]'
python -m pip install --no-build-isolation 'transformer_engine[pytorch]'
python -m pip install --no-build-isolation 'transformer_engine[jax]'
python -m pip install --no-build-isolation 'transformer_engine[pytorch,jax]'
```

Use `core_cu12` or `core_cu13` when the CUDA major must be explicit.

## Package version mismatch

**Symptoms**

- `Transformer Engine package version mismatch`
- Mismatched versions among `transformer-engine`, `transformer-engine-cu12` or
  `transformer-engine-cu13`, `transformer_engine_torch`, and
  `transformer_engine_jax`.

**Likely cause**

Pip resolved packages from different releases, or stale source-built shared
objects remain on the import path.

**Fix**

- Use one target version across the metapackage, core package, and framework
  extension packages.
- Uninstall stale `transformer-engine*`, `transformer_engine_torch`, and
  `transformer_engine_jax` packages before reinstalling the selected extras.
- For source checkouts, rebuild from a clean environment or remove stale build
  artifacts when switching CUDA major, Python minor, or framework versions.

## PyTorch or JAX version mismatch

**PyTorch symptoms**

- Undefined C++ symbols when importing `transformer_engine.pytorch`.
- ABI-looking errors involving `_GLIBCXX_USE_CXX11_ABI`.
- Build errors when `torch.version.cuda` is not CUDA 12 or CUDA 13.

**PyTorch fixes**

- Use a CUDA-enabled PyTorch build whose CUDA major is 12 or 13.
- Build Transformer Engine with the same PyTorch installation that will import
  it; use `--no-build-isolation` to prevent a temporary build environment from
  selecting a different torch.
- If a custom PyTorch ABI is used, rebuild Transformer Engine against that same
  PyTorch ABI. Do not mix container PyTorch, system PyTorch, and venv PyTorch.

**JAX symptoms**

- `GPU backend is required to build TE jax extensions.`
- `Could not find xla source.`
- `No registered implementation for custom call ... for platform CUDA`.

**JAX fixes**

- Use a GPU-enabled JAX/JAXLIB pair and keep the pair version-compatible.
- Use `--no-build-isolation` for both source builds and wheel builds so the
  wheel is compiled against the JAX/JAXLIB that will import it.
- When mixing PyTorch and JAX plus Triton, set `NVTE_USE_PYTORCH_TRITON=1` only
  if the environment intentionally uses the PyTorch Triton package for JAX
  Triton kernels.

## CUDA runtime, cuBLAS, cuDNN, and loader order

**Symptoms**

- `cudnn shared object not found`, `nvrtc shared object not found`,
  `curand shared object not found`, `cublas shared object not found`, or
  `cudart shared object not found`.
- Import succeeds in one shell but fails in another.
- Runtime imports load a different CUDA/cuDNN library than the one used at build
  time.

**How Transformer Engine searches**

Runtime loading checks system/toolkit locations first via `CUDNN_HOME`,
`CUDNN_PATH`, `CUDA_HOME`, `CUDA_PATH`, default CUDA locations, and the dynamic
loader. If needed, it can fall back to NVIDIA Python packages for CUDA runtime
libraries. Mixed system/container libraries and pip-provided CUDA libraries are
therefore a common source of mismatches.

**Fix**

- Decide whether system/toolkit libraries or pip NVIDIA libraries are the source
  of truth.
- Put the intended CUDA/cuDNN/NCCL library directories first in
  `LD_LIBRARY_PATH` before import and before source build.
- Set `CUDA_HOME`/`CUDA_PATH` for toolkit libraries and `CUDNN_HOME`/`CUDNN_PATH`
  for cuDNN when they are not in default locations.
- If headers are missing at runtime for NVRTC kernels, set
  `NVTE_CUDA_INCLUDE_DIR` to the directory containing `cuda_runtime.h`.

## cuDNN mismatch or sublibrary loading failed

**Symptoms**

- `CUDNN_STATUS_SUBLIBRARY_LOADING_FAILED`
- cuDNN frontend version mismatch errors.
- JAX fused attention or flex attention fails immediately after import or first
  use.

**Likely cause**

The source build compiled against one cuDNN while runtime loads another, or the
Python cuDNN frontend package does not match the C++ frontend/runtime used by
Transformer Engine.

**Fix**

- Align cuDNN runtime libraries, cuDNN headers, and `nvidia-cudnn-frontend`.
- Before rebuilding from source, set:

  ```bash
  export CUDNN_HOME="<cudnn-prefix>"
  export CUDNN_PATH="$CUDNN_HOME"
  export LD_LIBRARY_PATH="$CUDNN_HOME/lib:$CUDNN_HOME/lib64:${LD_LIBRARY_PATH:-}"
  ```

- Rebuild with `--no-build-isolation` after the desired cuDNN is first on the
  loader path.

## Missing nvcc, CUDA headers, or NVML headers

**Symptoms**

- `Could not find NVCC`
- CMake or compiler errors for `cuda_runtime.h`, `cublas_v2.h`, `cudnn.h`,
  `cudnn_frontend.h`, or `nvml.h`.
- Build succeeds with runtime wheels for import-only checks but fails when
  compiling source.

**Likely cause**

The environment has CUDA runtime packages but not a full CUDA Toolkit and header
set, or the include path is not visible to CMake/NVCC.

**Fix**

- Install or expose a CUDA Toolkit matching the selected CUDA major, including
  `nvcc`, CUDA headers, cuBLAS headers, and NVML headers.
- Set `CUDA_HOME` to the toolkit prefix and ensure `$CUDA_HOME/bin` is on `PATH`.
- Set `NVTE_CUDA_INCLUDE_DIR` when `cuda_runtime.h` is outside the standard
  toolkit include directory.
- Install or expose `nvidia-cudnn-frontend>=1.25.0` so
  `cudnn_frontend.h` is available.

## NCCL EP on SM80/A100

**Symptoms**

- `NCCL EP requires Hopper or newer (SM >= 90)`.
- `NVTE_WITH_NCCL_EP=1 was set but NVTE_CUDA_ARCHS ... contains no arch >= 90`.
- NCCL EP submodule or `libnccl.so` errors on A100 builds.

**Likely cause**

NCCL EP was enabled while targeting A100/SM80. A100 can build and use other
Transformer Engine functionality, but NCCL EP is a Hopper-or-newer optional
feature.

**Fix**

For A100/SM80 source builds, set both values explicitly:

```bash
export NVTE_CUDA_ARCHS=80
export NVTE_WITH_NCCL_EP=0
python -m pip install --no-build-isolation -e .
```

If building on Hopper or newer and EP is required, initialize
`3rdparty/nccl-extensions`, provide NCCL headers and `libnccl.so`, and ensure
runtime NCCL is new enough for EP.

## Submodule missing or stale

**Symptoms**

- `NCCL EP submodule not found ... Run git submodule update --init --recursive`.
- Build errors under CUTLASS or missing vendor headers.
- Submodule state assertion says submodules are initialized incorrectly.

**Likely cause**

The source checkout is missing vendor submodules, or submodules are at
unexpected commits.

**Fix**

Run:

```bash
git submodule update --init --recursive
```

Then rebuild. Do not use `NVTE_SKIP_SUBMODULE_CHECKS_DURING_BUILD` unless the
user explicitly wants a development-only experiment with known submodule drift.

## Framework import order and mixed environments

**Symptoms**

- `import transformer_engine` warns about the framework you are not trying to
  use.
- PyTorch-only installs in an environment with JAX, or JAX-only installs in an
  environment with PyTorch, produce confusing missing-extension warnings.
- A top-level import passes, but `transformer_engine.pytorch` or
  `transformer_engine.jax` fails later.

**Likely cause**

The top-level package probes installed frameworks. If PyTorch or JAX is
importable but the corresponding Transformer Engine extension is absent,
Transformer Engine may warn unless `NVTE_FRAMEWORK` says that framework is
required.

**Fix**

- Validate the exact selected framework import, not only top-level import.
- Set `NVTE_FRAMEWORK=pytorch`, `NVTE_FRAMEWORK=jax`, or `NVTE_FRAMEWORK=all`
  during validation so missing expected extensions fail loudly.
- In source builds, set the same `NVTE_FRAMEWORK` value used by the validation
  target.

## Build resource exhaustion

**Symptoms**

- Host becomes unresponsive during CUDA compilation.
- Compiler is killed, often without a clear Python traceback.
- FlashAttention-related compilation consumes excessive RAM.

**Fix**

Limit parallelism before rebuilding:

```bash
export NVTE_BUILD_MAX_JOBS=1
export MAX_JOBS=1
export NVTE_BUILD_THREADS_PER_JOB=1
python -m pip install --no-build-isolation -e .
```

Increase jobs only after a one-job build proves the toolchain and dependencies
are correct.
