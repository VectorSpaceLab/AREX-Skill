# Build and install Transformer Engine

This reference is self-contained installation operating knowledge for
Transformer Engine. It covers PyPI, NGC container, and source-build variants;
framework selection; CUDA/cuDNN/NCCL/CUTLASS prerequisites; and safe validation
steps. It intentionally avoids broad development or QA installs as defaults.

## Known target facts for this generated skill

- Package/source version distilled for this skill: `2.19.0.dev0`.
- A verified source-build profile on A100/SM80 used:
  - `NVTE_FRAMEWORK=all`
  - `NVTE_CUDA_ARCHS=80`
  - `NVTE_WITH_NCCL_EP=0`
  - initialized `cutlass` and `googletest` submodules
- PyTorch `2.9.1` and JAX/JAXLIB `0.10.2` import probes passed in the
  prepared inspection environment.
- A100/SM80 supports BF16-oriented Transformer Engine runtime checks, but not
  FP8, MXFP8, or NVFP4 runtime feature claims.
- NCCL EP is optional for the A100 profile and is a Hopper-or-newer feature.

## System requirements and compatibility boundaries

Minimum practical requirements:

| Area | Requirement | Notes |
|---|---|---|
| OS | Linux x86_64 | WSL2 may work with limitations; Linux is the supported baseline. |
| Python | Python 3.10+ | Python 3.12 is a good target when starting fresh. |
| CUDA driver/toolkit | CUDA 12.1+ for Ampere/Ada/Hopper; CUDA 12.8+ for Blackwell | Source builds need `nvcc` and headers, not only a runtime wheel. |
| cuDNN | cuDNN 9.3+ | Keep runtime libraries, headers, and Python cuDNN frontend aligned. |
| Build tools | C++17 compiler, CMake 3.21+, Ninja, wheel, pybind11 | GCC 9+ or Clang 10+ is a safe compiler baseline. |
| Build Python deps | `nvidia-cudnn-frontend>=1.25.0`, `packaging`, `pydantic`, `importlib-metadata` | Install only the framework dependencies selected below. |
| PyTorch build | `torch>=2.1` with CUDA 12/13 | Source packages derive the core CUDA package from `torch.version.cuda`. |
| JAX build | JAX/JAXLIB with a GPU backend, source requirement `jax>=0.5.0` | The JAX extension asserts that a CUDA GPU backend is available. |
| Submodules | `3rdparty/cutlass`, `3rdparty/googletest`; `3rdparty/nccl-extensions` only for NCCL EP | Source builds check submodule state and try to initialize submodules if git is available. |

Hardware feature boundaries:

- Ampere/A100/SM80: valid for BF16/FP16 and many non-FP8 workflows; compile with
  `NVTE_CUDA_ARCHS=80` to avoid unnecessary targets. Do not claim FP8, MXFP8, or
  NVFP4 runtime success on A100.
- Ada/Hopper/Blackwell with compute capability 8.9+: FP8-capable family. Hopper
  is SM90, while Ada is SM89.
- Hopper or newer SM90+: eligible for NCCL EP. If targeting only SM80, disable
  NCCL EP explicitly.
- Blackwell SM100/SM120 family: required for MXFP8 and NVFP4 runtime recipes;
  use CUDA 12.8+.

## Install decision tree

1. **Need a known-compatible GPU stack and no source patch?** Use an NGC
   framework container.
   - PyTorch container image pattern: `nvcr.io/nvidia/pytorch:<release>-py3`.
   - JAX container image pattern: `nvcr.io/nvidia/jax:<release>-py3`.
   - Inside NGC containers, Transformer Engine is preinstalled in recent PyTorch
     images and can be validated by import. If an NGC image also contains a
     source tree under `/opt/transformerengine` or `/opt/transformer-engine`, do
     not depend on those examples for skill validation; use the import checks
     below.
2. **Need a stable package with framework bindings?** Use PyPI extras.
   - PyTorch: `python -m pip install --no-build-isolation 'transformer_engine[pytorch]'`
   - JAX: `python -m pip install --no-build-isolation 'transformer_engine[jax]'`
   - Both: `python -m pip install --no-build-isolation 'transformer_engine[pytorch,jax]'`
   - Pip normalizes underscore and hyphen names, so `transformer-engine[...]`
     is equivalent for package resolution.
3. **Need core C++/runtime library only?** Use the core extra, not an empty
   metapackage.
   - Default CUDA-major core: `python -m pip install 'transformer_engine[core]'`
   - CUDA 12 core: `python -m pip install 'transformer_engine[core_cu12]'`
   - CUDA 13 core: `python -m pip install 'transformer_engine[core_cu13]'`
4. **Need current checkout, editable mode, a patch, or custom arch/framework
   selection?** Use a source build.
   - Initialize required submodules first.
   - Preinstall only the selected framework stack and build requirements.
   - Use `--no-build-isolation` so pip does not create a temporary build env with
     a different PyTorch/JAX stack.
   - For A100/SM80 both-framework source builds, use the verified profile in the
     known target facts section.

## Framework selection for source builds

`NVTE_FRAMEWORK` controls which Python extension modules are built:

| Value | Meaning | Use when |
|---|---|---|
| unset | Auto-detect installed `torch` and/or `jax` | Quick local source build when the environment contains only desired frameworks. |
| `pytorch` | Build `transformer_engine_torch` and PyTorch package support | PyTorch-only tasks or when JAX is not installed/verified. |
| `jax` | Build `transformer_engine_jax` and JAX package support | JAX-only tasks with a GPU JAXLIB. |
| `pytorch,jax` | Build both explicit framework extensions | Prefer this over autodetect in mixed environments. |
| `all` | Alias for both supported frameworks | Good for controlled environments where both framework stacks are verified. |
| `none` | Build only the framework-agnostic C++/core package | Core library work or dependency probing without framework imports. |

If `NVTE_FRAMEWORK` is unset and both PyTorch and JAX are importable, source
setup will try to build both. Set it explicitly when debugging one framework so
missing unrelated framework extensions do not obscure the failure.

## Source-build command template

The bundled template is at `../scripts/source_build_env_template.sh`. It prints
usage by default and runs the editable install only with `--install`.

Minimal explicit examples:

```bash
# PyTorch-only source build for the current GPU family.
NVTE_FRAMEWORK=pytorch python -m pip install --no-build-isolation -e .

# JAX-only source build.
NVTE_FRAMEWORK=jax python -m pip install --no-build-isolation -e .

# Both frameworks on A100/SM80, avoiding Hopper-only NCCL EP.
NVTE_FRAMEWORK=all NVTE_CUDA_ARCHS=80 NVTE_WITH_NCCL_EP=0 \
  python -m pip install --no-build-isolation -e .

# Core-only C++ library build.
NVTE_FRAMEWORK=none python -m pip install --no-build-isolation -e .
```

Do not add `[test]`, broad development requirements, full QA wheel scripts, or
all optional communication libraries by default. Add only what the user's
selected workflow requires.

## Environment variable table

| Variable | Scope | Typical values | Operating guidance |
|---|---|---|---|
| `NVTE_FRAMEWORK` | Build | `pytorch`, `jax`, `pytorch,jax`, `all`, `none` | Set explicitly in mixed environments. |
| `NVTE_CUDA_ARCHS` | Build | `80`, `89`, `90`, `100`, `120`, semicolon list | Reduces build time and binary size. A100 uses `80`; H100 uses `90`; Blackwell uses `100` or newer values appropriate to the GPU. |
| `NVTE_WITH_NCCL_EP` | Build/runtime feature | `0` or `1` | Leave off for SM80/A100. Use only on Hopper-or-newer systems with compatible NCCL. |
| `CUDA_HOME` / `CUDA_PATH` | Build/runtime lookup | Toolkit prefix | Needed for `nvcc`, CUDA headers, NVRTC headers, and loader fallback. |
| `NVTE_CUDA_INCLUDE_DIR` | Runtime/header lookup | CUDA include directory or package CUDA root | Prefer this exact name when `cuda_runtime.h` is not found. |
| `CUDNN_HOME` / `CUDNN_PATH` | Build/runtime lookup | cuDNN prefix | Set both names when using a non-system cuDNN. CMake searches `CUDNN_PATH`; runtime loader also recognizes `CUDNN_HOME`/`CUDNN_PATH`. |
| `CUDNN_INCLUDE_PATH` / `CUDNN_LIBRARY_PATH` | Build lookup | cuDNN include/lib directories | Use when headers and libraries are split. |
| `NCCL_HOME` | NCCL EP build/runtime | NCCL prefix | Required when NCCL EP cannot locate `nccl.h` and `libnccl.so`. Runtime loader should resolve the same NCCL used for the build. |
| `LD_LIBRARY_PATH` | Runtime loader | CUDA/cuDNN/NCCL library directories | Put the intended toolkit/cuDNN/NCCL libraries before conflicting container or wheel libraries. |
| `NVTE_BUILD_MAX_JOBS` | Build resource control | Positive integer | Transformer Engine build parallelism; also respected by NCCL EP build. |
| `MAX_JOBS` | Build resource control | Positive integer | Standard fallback recognized by the build helper. |
| `NVTE_BUILD_THREADS_PER_JOB` | CUDA compile control | Positive integer | Reduces per-job CUDA compiler threads when memory is tight. |
| `NVTE_BUILD_DEBUG` | Build | `0` or `1` | Adds debug symbols and disables optimizations; do not enable for normal installs. |
| `NVTE_CMAKE_BUILD_DIR` | Build cache | Build directory | Enables incremental CMake builds; avoid using stale directories across incompatible CUDA/framework changes. |
| `NVTE_USE_CCACHE` / `NVTE_CCACHE_BIN` | Build acceleration | `1`, `ccache` or `sccache` | Optional compile cache; not a correctness requirement. |
| `NVTE_RELEASE_BUILD` | Packaging | `0` or `1` | Wheel/distribution mode. Do not set for ordinary editable source installs. |
| `NVTE_BUILD_METAPACKAGE` | Packaging | `0` or `1` | Only for package publishing workflows; not for normal users. |
| `NVTE_USE_PYTORCH_TRITON` | JAX test/runtime corner | `0` or `1` | Use `1` only when intentionally using PyTorch's Triton package in a mixed JAX+PyTorch environment. |

## Submodule notes

Source builds need vendor submodules checked out at the commits expected by the
checkout:

- `3rdparty/cutlass`: required for CUDA kernels.
- `3rdparty/googletest`: required by the source tree and build checks.
- `3rdparty/nccl-extensions`: required only when building NCCL EP.

If submodules are missing, initialize them before the source build:

```bash
git submodule update --init --recursive
```

Avoid bypassing submodule checks unless doing a deliberate development-only
experiment; stale submodules can build the wrong kernels.

## Safe validation sequence

Run validation in increasing order. Stop at the first failing layer and use
`troubleshooting.md` before reinstalling unrelated packages.

1. **Environment and GPU probe**

   ```bash
   python - <<'PY'
   import platform, sys
   print('python', sys.version.split()[0], platform.platform())
   try:
       import torch
       print('torch', torch.__version__, 'cuda', torch.version.cuda, 'cuda_available', torch.cuda.is_available())
       if torch.cuda.is_available():
           print('torch_device_capability', torch.cuda.get_device_capability(0))
   except Exception as exc:
       print('torch_probe_failed', type(exc).__name__, exc)
   try:
       import jax, jaxlib
       print('jax', jax.__version__, 'jaxlib', jaxlib.__version__)
       print('jax_devices', jax.devices())
   except Exception as exc:
       print('jax_probe_failed', type(exc).__name__, exc)
   PY
   ```

2. **Core package and version consistency**

   ```bash
   python - <<'PY'
   import importlib.metadata as md
   for name in ['transformer-engine', 'transformer-engine-cu12', 'transformer-engine-cu13',
                'transformer_engine_torch', 'transformer_engine_jax']:
       try:
           print(name, md.version(name))
       except md.PackageNotFoundError:
           print(name, 'not-installed')
   import transformer_engine as te
   print('transformer_engine import OK', te.__version__)
   PY
   ```

3. **PyTorch extension import, only if PyTorch support was selected**

   ```bash
   NVTE_FRAMEWORK=pytorch python - <<'PY'
   import torch
   import transformer_engine.pytorch
   import transformer_engine_torch
   print('TE PyTorch import OK', torch.__version__)
   PY
   ```

4. **JAX extension import, only if JAX support was selected**

   ```bash
   NVTE_FRAMEWORK=jax python - <<'PY'
   import jax, jaxlib
   import transformer_engine.jax
   import transformer_engine_jax
   print('TE JAX import OK', jax.__version__, jaxlib.__version__)
   PY
   ```

5. **Hardware capability classification**

   - If the detected capability is SM80/A100, mark BF16-capable and FP8/MXFP8/NVFP4-unverified/unsupported.
   - If SM89 or newer, FP8 checks may be eligible but still require framework-level verification.
   - If SM90 or newer and NCCL EP was intentionally built, verify runtime NCCL availability before EP-specific use.
   - If SM100/SM120 or newer, Blackwell-only MXFP8/NVFP4 checks become eligible.

6. **Final native behavior checks**

   Defer full native examples, QA wheel scripts, and framework behavior tests to
   the repo-skill verification phase. This install-build sub-skill should report
   install/import readiness, selected framework coverage, hardware eligibility,
   and unresolved loader or backend gaps.
