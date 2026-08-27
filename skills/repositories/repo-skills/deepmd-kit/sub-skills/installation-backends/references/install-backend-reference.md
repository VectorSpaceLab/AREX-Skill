# Install and Backend Reference

This reference distills DeePMD-kit installation and backend-selection behavior into commands future agents can adapt without relying on the source checkout.

## Install Decision Tree

| User goal | Recommended path | Why | Immediate validation |
| --- | --- | --- | --- |
| Fast complete runtime with `dp`, LAMMPS, MPI tools | Conda-forge | Solver-managed compiled stack and integrations | `dp -h`, `lmp -h` if LAMMPS is installed |
| Python-only TensorFlow workflows | Pip with TensorFlow extras | Minimal Python interface for default backend | `python -c "import deepmd"`, `dp --tf -h` |
| Python-only PyTorch workflows | Install `torch`, then `deepmd-kit` | PyTorch wheel source must match CPU/GPU target | `python -c "import torch, deepmd"`, `dp --pt -h` |
| JAX workflows | Pip with JAX extra and matching JAX wheel | JAX wheel choice depends on CPU/CUDA target | `python -c "import jax, deepmd"`, `dp --jax -h` |
| Paddle workflows | Install Paddle first, then `deepmd-kit` | Paddle indexes differ for CPU/GPU | `python -c "import paddle, deepmd"`, `dp --pd -h` |
| Unsupported platform, ROCM, custom C++ OPs, custom roots | Source build | Prebuilt wheels cannot express the target | source build log plus `dp -h` outside the source tree |
| No host mutation or reproducible shell runtime | Docker | Isolated prebuilt image | `docker run ... dp -h` |
| Restricted network with predownloaded bundles | Offline installer | Avoids live package downloads | activate bundle then `dp -h` |

## Python and Platform Requirements

- Python interface requires Python 3.10 or newer.
- Project metadata supports Python 3.10, 3.11, 3.12, and 3.13.
- Conda and offline packages require GNU C Library 2.17 or newer.
- Pip wheel support varies by platform and may require newer glibc for Linux wheels.
- GPU packages require a compatible NVIDIA driver at runtime, not only a CUDA toolkit package in the environment.
- Build tools for source work include a modern CMake, a C++ compiler, and backend framework headers/libraries when compiling C++ interfaces or custom OPs.

## Backend and Model Format Matrix

| Backend | CLI aliases | Python module to probe | Typical model/checkpoint suffixes | Notes |
| --- | --- | --- | --- | --- |
| TensorFlow | `--tf`, `--tensorflow`, `--backend tensorflow` | `tensorflow` | `.pb`, `.meta`, `.index`, `.data-00000-of-00001` | Default CLI backend; uses TensorFlow v1 compatibility graph mode internally. |
| PyTorch | `--pt`, `--pytorch`, `--backend pytorch` | `torch` | `.pth`, `.pt` | `.pth` is a DeePMD-kit frozen model; `.pt` is a checkpoint. Custom C++ OPs are source-build opt-in. |
| JAX | `--jax`, `--backend jax` | `jax` | `.xlo`, `.savedmodel`, `.jax` | `.savedmodel` export requires TensorFlow support for SavedModel/C++ usage. |
| Paddle | `--pd`, `--paddle`, `--backend paddle` | `paddle` | `.json` plus `.pdiparams`, `.pd` | Install Paddle wheel from the CPU/GPU index matching the target. |
| PyTorch exportable | `--pt-expt`, `--pytorch-exportable`, `--backend pytorch-exportable` | `torch` | exportable PyTorch artifacts | Use only for workflows that explicitly target exportable/AOT PyTorch behavior. |

## Pip Install Patterns

Create and activate a clean environment first. Avoid installing all backend stacks unless the user needs cross-backend conversion or multi-backend tests.

### TensorFlow

CPU-oriented install:

```bash
pip install deepmd-kit[cpu]
python -c "import deepmd; import tensorflow as tf; print('deepmd/tensorflow ok', tf.__version__)"
dp --tf -h
```

CUDA 12 wheel-bundle style install when toolkit/cuDNN Python wheels are desired:

```bash
pip install deepmd-kit[gpu,cu12]
python -c "import deepmd; import tensorflow as tf; print('deepmd/tensorflow ok', tf.__version__)"
dp --tf -h
```

### PyTorch

CPU-oriented install:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install deepmd-kit
python -c "import deepmd; import torch; print('deepmd/torch ok', torch.__version__)"
dp --pt -h
```

GPU-oriented install:

```bash
# Choose the torch command from PyTorch for the machine's CUDA/driver target.
pip install torch
pip install deepmd-kit
python -c "import deepmd; import torch; print('torch cuda available:', torch.cuda.is_available())"
dp --pt -h
```

### JAX

CPU-oriented install:

```bash
pip install deepmd-kit[jax]
python -c "import deepmd; import jax; print('deepmd/jax ok', jax.__version__)"
dp --jax -h
```

CUDA-oriented install:

```bash
pip install deepmd-kit[jax] 'jax[cuda12]'
python -c "import deepmd; import jax; print('jax devices:', jax.devices())"
dp --jax -h
```

### Paddle

CPU-oriented install:

```bash
pip install paddlepaddle -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
pip install deepmd-kit
python -c "import deepmd; import paddle; print('deepmd/paddle ok', paddle.__version__)"
dp --pd -h
```

CUDA-oriented install example:

```bash
pip install paddlepaddle-gpu -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
pip install deepmd-kit
python -c "import deepmd; import paddle; print('paddle compiled with cuda:', paddle.device.is_compiled_with_cuda())"
dp --pd -h
```

## Conda, Docker, and Offline Patterns

### Conda-forge

Use conda-forge for compiled-stack compatibility:

```bash
conda create -n deepmd deepmd-kit lammps horovod -c conda-forge
conda activate deepmd
dp -h
```

Use solver-specific CUDA package guidance from conda-forge when requesting GPU-enabled backend packages. Do not mix a conda-managed compiled stack with arbitrary pip GPU wheels unless the user accepts ABI risk.

### Docker

Use CPU or GPU image tags that match the user's deployment target:

```bash
docker pull ghcr.io/deepmodeling/deepmd-kit:<tag>
docker run --rm ghcr.io/deepmodeling/deepmd-kit:<tag> dp -h
```

Choose Docker when isolation matters more than integrating with an existing host Python environment.

### Offline Installers

Offline installers are useful for air-gapped machines. After transfer, merge split archives if the release package is split, run the installer, activate the resulting environment, then validate:

```bash
dp --version
dp -h
```

Do not assume offline GPU packages work on a machine whose NVIDIA driver is older than the package CUDA runtime requires.

## Source Build Controls

Source builds are split into Python-package builds and lower-level C++ interface builds. Use the Python-package environment variables for `pip install .` or `pip install --no-binary deepmd-kit deepmd-kit`; use CMake variables when building from the `source` C++ tree.

### Python Package Build Environment Variables

| Variable | Values | Default | Purpose |
| --- | --- | --- | --- |
| `DP_VARIANT` | `cpu`, `cuda`, `rocm` | `cpu` | Select CPU, CUDA, or ROCM build mode. |
| `DP_ENABLE_TENSORFLOW` | `0`, `1` | `1` | Enable or disable TensorFlow backend build support. |
| `DP_ENABLE_PYTORCH` | `0`, `1` | `0` | Enable custom PyTorch C++ OP build support. PyTorch Python workflows can still exist without custom OPs. |
| `DP_ENABLE_PADDLE` | `0`, `1` | build-profile dependent | Enable Paddle build support when the build profile supports it. |
| `TENSORFLOW_ROOT` | path | auto-detected | Point build discovery at a TensorFlow Python library root. |
| `PYTORCH_ROOT` | path | auto-detected | Point build discovery at a PyTorch Python library root. |
| `CUDAToolkit_ROOT` | path | auto-detected | Point CUDA source builds at a toolkit with compiler/runtime files. |
| `ROCM_ROOT` / `ROCM_PATH` | path | auto-detected | Point ROCM source builds at a ROCM installation. |
| `DP_ENABLE_NATIVE_OPTIMIZATION` | `0`, `1` | `0` | Optimize for the build CPU; avoid for portable wheels. |
| `DP_ENABLE_IPI` | `0`, `1` | `0` | Build i-PI entry point support. |
| `DP_LAMMPS_VERSION` | version string | unset | Request LAMMPS-version-aware C++ interface behavior. |
| `CMAKE_ARGS` | string | unset | Add extra CMake arguments through scikit-build. |
| `CXXFLAGS`, `CUDAFLAGS`, `HIPFLAGS` | compiler flags | unset | Pass language-specific compiler flags. |

CPU-only source install with TensorFlow support and no PyTorch custom OPs:

```bash
python -m pip install --upgrade pip
pip install tensorflow-cpu
DP_VARIANT=cpu DP_ENABLE_TENSORFLOW=1 DP_ENABLE_PYTORCH=0 pip install .
cd ..
python -c "import deepmd; print('deepmd import ok')"
dp -h
```

CPU-only source install with PyTorch CLI support but without custom OPs:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
DP_VARIANT=cpu DP_ENABLE_TENSORFLOW=0 DP_ENABLE_PYTORCH=0 pip install .
cd ..
python -c "import deepmd, torch; print('deepmd/torch import ok')"
dp --pt -h
```

Source install with custom PyTorch C++ OPs:

```bash
pip install torch
DP_VARIANT=cpu DP_ENABLE_TENSORFLOW=0 DP_ENABLE_PYTORCH=1 pip install .
cd ..
dp --pt -h
```

CUDA source-build sketch:

```bash
pip install tensorflow torch
DP_VARIANT=cuda \
  DP_ENABLE_TENSORFLOW=1 \
  DP_ENABLE_PYTORCH=1 \
  CUDAToolkit_ROOT=/path/to/cuda \
  pip install .
```

Do not copy the placeholder path into public instructions for a specific user; ask them for their actual toolkit location or rely on auto-discovery.

ROCM source-build sketch:

```bash
DP_VARIANT=rocm ROCM_ROOT=/path/to/rocm pip install .
```

### C++ Interface CMake Variables

Use direct CMake builds for maintainers integrating C++ inference, plugin builds, or non-Python runtime libraries.

| CMake variable | Purpose |
| --- | --- |
| `ENABLE_TENSORFLOW=ON|OFF` | Build TensorFlow backend and also enable JAX support through TensorFlow C++ libraries. |
| `ENABLE_PYTORCH=ON|OFF` | Build PyTorch backend support. |
| `ENABLE_JAX=ON|OFF` | Build JAX backend support; can use TensorFlow C API/C++ libraries. |
| `ENABLE_PADDLE=ON|OFF` | Build Paddle backend support. |
| `USE_TF_PYTHON_LIBS=TRUE|FALSE` | Use TensorFlow libraries from the Python package. |
| `USE_PT_PYTHON_LIBS=TRUE|FALSE` | Use libtorch from the PyTorch Python package. |
| `TENSORFLOW_ROOT` | TensorFlow C++ library root when not using Python libraries. |
| `PADDLE_INFERENCE_DIR` | Paddle inference C++ directory. |
| `USE_CUDA_TOOLKIT=TRUE|FALSE` | Enable CUDA toolkit support in C++ build. |
| `CUDAToolkit_ROOT` | CUDA toolkit root. |
| `USE_ROCM_TOOLKIT=TRUE|FALSE` | Enable ROCM toolkit support. |
| `CMAKE_HIP_COMPILER_ROCM_ROOT` | ROCM root for HIP compiler discovery. |
| `LAMMPS_SOURCE_ROOT` | Optional LAMMPS source root for plugin mode. |
| `ENABLE_IPI=ON|OFF` | Enable i-PI integration support. |
| `DEEPMD_BYPASS_TORCH_CUDA_CHECK=ON|OFF` | Let CPU-only PyTorch builds bypass local CUDA compiler discovery when using CUDA-enabled PyTorch wheels. |
| `ENABLE_NATIVE_OPTIMIZATION=ON|OFF` | Optimize for current CPU only. |

Minimal TensorFlow/JAX-flavored C++ build using TensorFlow Python libraries:

```bash
cmake -DENABLE_TENSORFLOW=TRUE -DUSE_TF_PYTHON_LIBS=TRUE -DCMAKE_INSTALL_PREFIX=<install-prefix> ..
cmake --build . --parallel 4
cmake --install .
```

Minimal PyTorch C++ build using PyTorch Python libraries:

```bash
cmake -DENABLE_PYTORCH=TRUE -DUSE_PT_PYTHON_LIBS=TRUE -DCMAKE_INSTALL_PREFIX=<install-prefix> ..
cmake --build . --parallel 4
cmake --install .
```

## Validation Command Catalog

Use these checks in order, stopping at the first failure and applying the troubleshooting reference.

```bash
python --version
python -c "import deepmd; print('deepmd import ok')"
python -c "import importlib.metadata as m; print(m.version('deepmd-kit'))"
dp --version
dp -h
dp --tf -h
dp --pt -h
dp --jax -h
dp --pd -h
dp --pt-expt -h
```

Optional backend module probes:

```bash
python -c "import tensorflow as tf; print(tf.__version__)"
python -c "import torch; print(torch.__version__)"
python -c "import jax; print(jax.__version__)"
python -c "import paddle; print(paddle.__version__)"
```

Bundled helper probes:

```bash
python scripts/check_deepmd_environment.py --backend all --check-backend-help
python scripts/check_deepmd_environment.py --backend pytorch --strict
python scripts/check_deepmd_environment.py --module tensorflow --module torch
```

## Routing Examples

### Diagnose a `.pth` model on a TensorFlow-only install

1. Recognize `.pth` as a PyTorch frozen model suffix.
2. Run `python scripts/check_deepmd_environment.py --backend pytorch --check-backend-help`.
3. If `torch` is missing, install a CPU or GPU PyTorch wheel matching the machine, then install or reuse `deepmd-kit`.
4. Re-run `dp --pt -h` before routing model operations to `../inference-model-ops/SKILL.md`.

### Plan a CPU-only source install disabling heavy custom OPs

1. Confirm Python 3.10+ and C++ build tools.
2. Choose only the Python backend package needed by the user.
3. Set `DP_VARIANT=cpu`.
4. Disable unused backend build support: for example `DP_ENABLE_TENSORFLOW=0` when only PyTorch CLI support is needed.
5. Keep `DP_ENABLE_PYTORCH=0` unless the user needs custom PyTorch OP acceleration.
6. Run `pip install .`, leave the source directory, then validate `import deepmd`, `dp -h`, and the intended backend help.
