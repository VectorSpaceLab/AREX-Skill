# Installation and Backend Troubleshooting

Use this reference after the basic validation sequence fails:

```bash
python --version
python -c "import deepmd; print('deepmd import ok')"
dp --version
dp -h
python scripts/check_deepmd_environment.py --backend all --check-backend-help
```

## Failure Matrix

| Symptom | Likely cause | Confirm with | Recovery |
| --- | --- | --- | --- |
| `ModuleNotFoundError: No module named 'deepmd'` | Wrong environment or package not installed | `python -c "import sys; print(sys.executable)"`; `python -m pip show deepmd-kit` | Activate the intended environment; install `deepmd-kit`; avoid mixing `pip` from one Python with `python` from another. |
| `dp: command not found` | Console script not on `PATH` or package install incomplete | `python -m pip show deepmd-kit`; `python -m deepmd.main -h` if available | Re-activate environment; reinstall package; use `python -m pip install deepmd-kit...` from the intended Python. |
| `dp --version` works but backend command fails | Backend Python module missing or backend alias mismatch | `dp --pt -h`; `python -c "import torch"`; bundled helper | Install the matching backend package or use the correct backend flag. |
| Python version error or resolver refuses package | Python older than 3.10 | `python --version` | Create a Python 3.10+ environment. |
| Large downloads or slow install | Heavy backend wheels and CUDA runtimes selected | `pip install -v ...`; inspect extras requested | Use CPU extras, install only one backend, or switch to conda/Docker if binary compatibility is the goal. |
| CUDA visible during install but runtime fails | Driver/toolkit/runtime mismatch | `nvidia-smi`; backend CUDA availability probe | Install a backend wheel compatible with the driver, or use CPU packages. |
| Source build cannot find TensorFlow | Isolated build cannot discover TensorFlow root | build log; `python -c "import tensorflow, pathlib; print(pathlib.Path(tensorflow.__file__).parent)"` | Set `TENSORFLOW_ROOT` to the TensorFlow package root or install TensorFlow in the build environment. |
| Source build cannot find PyTorch | `DP_ENABLE_PYTORCH=1` but `torch` root not discoverable | build log; `python -c "import torch; print(torch.__path__[0])"` | Set `PYTORCH_ROOT` or disable custom PyTorch OPs with `DP_ENABLE_PYTORCH=0`. |
| ABI or undefined symbol errors after source build | TensorFlow/PyTorch/C++ libraries built with incompatible compiler or CXX11 ABI | import traceback, `ldd`, framework compiler metadata | Rebuild in one consistent environment; prefer conda-forge for compatible compiled libraries. |
| Rebuild ignores new flags | Stale CMake/scikit-build build directory | build log still showing old `ENABLE_*` or `DP_VARIANT` | Remove the build directory/cache and reinstall with explicit flags. |
| LAMMPS or i-PI command missing | Python-only install or integration extras/toggles omitted | `dp -h`; `which lmp`; `python scripts/check_deepmd_environment.py` | Install integration extras or rebuild with `DP_LAMMPS_VERSION`/`DP_ENABLE_IPI`; route detailed setup to integrations. |

## Backend-Specific Diagnosis

### TensorFlow

Common signals:

- `dp --tf -h` fails because `tensorflow` is not importable.
- TensorFlow imports but GPU is not available.
- Source build reports missing `TENSORFLOW_ROOT` or incompatible compiler details.

Confirm:

```bash
python -c "import tensorflow as tf; print(tf.__version__)"
python scripts/check_deepmd_environment.py --backend tensorflow --check-backend-help
```

Recovery:

- For CPU-only use, prefer `tensorflow-cpu` or `deepmd-kit[cpu]`.
- For CUDA use, match the TensorFlow package to the installed NVIDIA driver and supported CUDA runtime.
- For source builds, install TensorFlow in the build Python environment or set `TENSORFLOW_ROOT` to the TensorFlow Python package root.
- If the user only needs a non-TensorFlow backend, set `DP_ENABLE_TENSORFLOW=0` for a source build and validate the intended backend instead.

### PyTorch

Common signals:

- `.pth` model workflows fail in an environment where only TensorFlow is installed.
- `dp --pt -h` fails because `torch` is not importable.
- Warnings mention custom PyTorch OPs or `DP_ENABLE_PYTORCH`.

Confirm:

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
python scripts/check_deepmd_environment.py --backend pytorch --check-backend-help
```

Recovery:

- Install a CPU or GPU PyTorch wheel that matches the user's machine, then validate `dp --pt -h`.
- Do not assume a `.pth` model can run with TensorFlow only; route model operations to PyTorch after install validation.
- Use `DP_ENABLE_PYTORCH=1` only when the user needs custom C++ OPs and has a compatible compiler/CMake stack.
- For CPU-only source builds with CUDA-enabled PyTorch wheels, consider CMake behavior that bypasses torch CUDA compiler discovery when DeePMD-kit itself is not building CUDA support.

### JAX

Common signals:

- `dp --jax -h` fails because `jax` is missing.
- A JAX SavedModel or C++ inference path fails because TensorFlow support is missing.
- GPU-generated JAX model cannot run on CPU.

Confirm:

```bash
python -c "import jax; print(jax.__version__); print(jax.devices())"
python scripts/check_deepmd_environment.py --backend jax --check-backend-help
```

Recovery:

- Install `deepmd-kit[jax]` for CPU JAX workflows.
- Install a CUDA-enabled JAX wheel only when the driver and CUDA target support it.
- Add TensorFlow support if the task requires `.savedmodel` export or C++ inference from JAX-generated artifacts.
- Avoid moving device-specific JAX models between GPU and CPU without confirming format support.

### Paddle

Common signals:

- `dp --pd -h` fails because `paddle` is not importable.
- Paddle CPU package installed on a GPU task, or GPU package installed against the wrong CUDA index.

Confirm:

```bash
python -c "import paddle; print(paddle.__version__); print(paddle.device.is_compiled_with_cuda())"
python scripts/check_deepmd_environment.py --backend paddle --check-backend-help
```

Recovery:

- Install `paddlepaddle` from the CPU index for CPU tasks.
- Install `paddlepaddle-gpu` from the CUDA index matching the target runtime for GPU tasks.
- For C++ Paddle inference, source builds require a Paddle inference library directory rather than only the Python wheel.

## Wrong Backend Flag or Model Suffix

DeePMD-kit has two backend-selection mechanisms that users often conflate:

- CLI backend flags choose the backend implementation for commands such as training and freezing.
- Model suffixes often let inference commands infer a backend from the model file.

When diagnosing install state, prefer explicit CLI flags and import checks:

```bash
dp --tf -h
dp --pt -h
dp --jax -h
dp --pd -h
```

If the user's file is `.pth`, require PyTorch availability before debugging model contents. If the file is `.pb`, require TensorFlow availability. If the file is `.json` plus `.pdiparams`, require Paddle availability. If the file is `.xlo`, `.jax`, or JAX-generated `.savedmodel`, require JAX and possibly TensorFlow depending on the operation.

## CUDA and ROCM Mismatch Checklist

For NVIDIA CUDA failures:

1. Run `nvidia-smi` and note the driver-supported CUDA version.
2. Check the backend package CUDA target; TensorFlow, PyTorch, JAX, and Paddle publish different wheel/index combinations.
3. Avoid mixing a package that bundles CUDA runtime components with an incompatible system driver.
4. For source builds, set `DP_VARIANT=cuda` only when a suitable toolkit and compiler are available.
5. Set `CUDAToolkit_ROOT` only to a real toolkit root with compiler/runtime files; do not point it at a Python wheel cache.

For ROCM failures:

1. Use a source build; prebuilt pip GPU paths are CUDA-oriented.
2. Set `DP_VARIANT=rocm`.
3. Set `ROCM_ROOT` or `ROCM_PATH` when auto-detection cannot find ROCM.
4. Confirm the selected backend framework supports the ROCM version and device.

## Source Build Cache Cleanup

When flags change but the build output does not, remove stale build state before retrying. Common stale-state signs include old `ENABLE_TENSORFLOW`, `ENABLE_PYTORCH`, `USE_CUDA_TOOLKIT`, or `DP_VARIANT` values appearing in logs.

Safe cleanup pattern from a source checkout:

```bash
rm -rf build
python -m pip install --no-cache-dir .
```

If the project uses a wheel-tagged scikit-build directory, remove the relevant generated build directory rather than editing installed files. Reinstall from a clean shell with all environment variables exported in the same command block.

## TensorFlow and PyTorch ABI Roots

TensorFlow and PyTorch C++ libraries may use specific compiler versions and `_GLIBCXX_USE_CXX11_ABI` settings. Mixing libraries from unrelated package managers can produce import-time undefined symbols or runtime crashes.

Prefer one of these approaches:

- Use conda-forge packages for a consistent compiled stack.
- Use framework Python packages and source-build flags that explicitly use the Python libraries.
- Build all C++ dependencies with one compiler/toolchain policy.

Avoid this pattern unless the user is intentionally debugging ABI issues:

- TensorFlow from pip, PyTorch from system packages, CMake from another package manager, and DeePMD-kit built against manually downloaded C++ libraries.

## LAMMPS and i-PI Toggle Diagnosis

LAMMPS and i-PI are integration concerns. This sub-skill should only diagnose whether install/build choices included them, then route detailed usage to `../integrations-development/SKILL.md`.

Signals:

- `lmp` is missing after a Python-only pip install.
- `dp_ipi` is missing after a build that did not set i-PI support.
- LAMMPS plugin or version mismatch appears in build logs.

Recovery options:

- For pip installs, include integration extras only when needed, such as LAMMPS or i-PI extras.
- For source builds, set `DP_ENABLE_IPI=1` to request the i-PI entry point.
- For LAMMPS-version-aware source builds, set `DP_LAMMPS_VERSION` to the target version.
- For lower-level C++ builds, use the appropriate CMake variables and route implementation details to integrations.

## Unsupported Python or Platform

If Python is older than 3.10, do not attempt to force install DeePMD-kit. Create a new environment with Python 3.10+.

If the platform is not covered by pip wheels, choose one of:

- conda-forge if it supports the platform and target backend stack;
- Docker if containerization is acceptable;
- offline installer if available for the platform;
- source build with explicit backend/toolchain planning.

## Heavy Wheel or Resolver Recovery

If the user complains that installation is slow or unexpectedly large:

1. Identify which backend extras were requested.
2. Remove unneeded extras such as GPU runtime bundles, JAX stack, LAMMPS, i-PI, or test/docs dependencies.
3. Install exactly one backend family first.
4. Prefer CPU-only backend wheels for smoke tests.
5. Use conda/Docker when binary dependency solving is more important than a minimal pip environment.

## Minimum Report Format

When handing the issue back to the user or another sub-skill, include:

- Python version and package environment status.
- `deepmd` import result.
- `dp --version` and `dp -h` result.
- Backend modules checked and their versions if importable.
- Backend CLI help checks that passed or failed.
- Install method used or recommended.
- Source-build variables or CMake variables involved.
- Remaining platform, CUDA/ROCM, ABI, LAMMPS, or i-PI risk.
