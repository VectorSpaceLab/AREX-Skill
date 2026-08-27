# MinkowskiEngine build and install reference

This reference distills the package build surfaces needed for a self-contained install plan. It covers PyPI, source, and Docker-style installs; CPU-only and CUDA builds; BLAS and compiler choices; and minimal post-install checks. CUDA commands are conditional recipes only: verify them in the user's environment before saying CUDA is working.

## Requirements and compatibility facts

- Python: 3.6 or newer is required by the setup script.
- Operating system: Linux is the normal target. Windows is explicitly rejected by the setup script. macOS has extra compiler/OpenMP requirements and is not the primary path here.
- Python packages: install PyTorch before building MinkowskiEngine; the setup script imports `torch` at build time. `numpy` and `ninja` are also expected for normal builds.
- BLAS: CPU kernels need a BLAS library. Supported setup choices are `flexiblas`, `openblas`, `mkl`, `atlas`, and `blas`. OpenBLAS is the most common documented default; MKL is useful on Intel/conda stacks.
- CUDA: CUDA acceleration requires a PyTorch CUDA build, a matching CUDA toolkit with `nvcc`, matching headers/libraries, and a CUDA architecture list suitable for the GPU. If `torch.cuda.is_available()` is false at build time, MinkowskiEngine defaults to CPU-only unless `--force_cuda` is supplied.
- Build backend: the setup script uses PyTorch C++/CUDA extension machinery and Ninja. The source tree also has a Makefile that is useful for `make clean` and single-threaded prebuilds when diagnosing failures.

## Bundled versus source-tree artifacts

- `scripts/build_command_helper.py` is the bundled replacement helper for planning build commands; it is safe and dry-run only.
- The Docker section below is a distilled replacement recipe, not a link to a source-tree Dockerfile.
- Any `make` command in this reference is recovery-only for users who already have a source tree with a Makefile; it is not a required runtime helper bundled in this sub-skill.

## Setup flags accepted by `setup.py`

Use these after `python setup.py install` in a source tree:

| Flag | Meaning | Notes |
|---|---|---|
| `--cpu_only` | Force a CPU-only extension. | Valid when no GPU/toolkit is available or the user only needs CPU operations. |
| `--force_cuda` | Build CUDA extension even if PyTorch reports CUDA unavailable. | Takes precedence over `--cpu_only`; only use when the toolkit and PyTorch CUDA package are intentionally prepared. |
| `--cuda_home=<cuda-home>` | Declare the CUDA toolkit root. | Also export `CUDA_HOME` because PyTorch's extension discovery uses the environment. |
| `--blas=<name>` | Choose BLAS. | Valid names: `flexiblas`, `openblas`, `mkl`, `atlas`, `blas`. |
| `--blas_include_dirs=<dir1,dir2>` | Add BLAS include directories. | Only active when `--blas` is set. Use comma-separated values. |
| `--blas_library_dirs=<dir1,dir2>` | Add BLAS library directories and runtime rpath. | Only active when `--blas` is set. Use comma-separated values. |
| `--fast_math` | Add CUDA fast-math flags. | CUDA-only optimization; avoid while debugging numerical differences. |
| `--debug` | Build with debug flags. | Slower; useful for native extension debugging. |
| `--force` | Force setuptools to rebuild/install. | Useful after stale build or ABI/CUDA changes. |

## Environment variables and build knobs

| Variable | Purpose | Practical use |
|---|---|---|
| `CXX` or `CC` | Select the host C++ compiler. | Use when CUDA requires a specific GCC version or when the default compiler fails. If `CXX` is set, the setup script also assigns it to `CC`. |
| `CUDA_HOME` | CUDA toolkit root for PyTorch extension discovery. | Set it from the active `nvcc` when multiple toolkits exist: `export CUDA_HOME="$(dirname "$(dirname "$(command -v nvcc)")")"`. |
| `TORCH_CUDA_ARCH_LIST` | GPU compute capabilities to compile. | Set explicitly when the default list misses the user's GPU. Example value format: `7.5 8.0 8.6+PTX`. |
| `MAX_JOBS` | Ninja parallel build limit. | Lower it, such as `MAX_JOBS=2` or `MAX_JOBS=4`, when compilation runs out of memory. If unset, the setup script caps very high CPU counts. |
| `OMP_NUM_THREADS` | OpenMP runtime thread count after import. | Set below 24 on high-core machines to avoid MinkowskiEngine's import-time warning and poor kernel-map scaling. |
| `TORCH_NVCC_FLAGS` | Extra NVCC flags used in Docker-style builds. | The distilled Docker recipe uses `-Xfatbin -compress-all` to reduce CUDA binary size. |

## Install routes

### 1. PyPI package route

Use this first when the user's platform has a compatible package build path and they do not need custom compile flags:

```bash
python -m pip install -U pip setuptools wheel
python -m pip install -U torch numpy ninja
python -m pip install -U MinkowskiEngine
```

If the PyPI install needs custom BLAS flags and the user's pip still supports legacy `--install-option`, use:

```bash
python -m pip install -U MinkowskiEngine -v --no-deps \
  --install-option="--blas=openblas"
```

If pip rejects `--install-option`, switch to the source-tree route below. The custom flags in this checkout are designed for `setup.py` arguments.

### 2. Source route: CPU-only build

Use CPU-only when CUDA is unavailable, `nvcc` is missing, the user is on a CPU machine, or the user wants a quick importable build before diagnosing GPU support.

```bash
python -m pip install -U pip setuptools wheel
python -m pip install -U torch numpy ninja
MAX_JOBS=4 CXX=g++ python setup.py install --cpu_only --blas=openblas
```

If BLAS auto-detection works, `--blas_include_dirs` is not needed. If headers are in a non-default location, add placeholders supplied by the user:

```bash
MAX_JOBS=4 CXX=g++ python setup.py install --cpu_only --blas=openblas \
  --blas_include_dirs="<blas-include-dir>" \
  --blas_library_dirs="<blas-library-dir>"
```

### 3. Source route: CUDA build

Use this only when all of the following are true:

1. `python -c "import torch; print(torch.cuda.is_available())"` returns `True`, or the user intentionally needs `--force_cuda`.
2. `command -v nvcc` finds the CUDA compiler.
3. The CUDA toolkit version used by `nvcc` matches the CUDA runtime expected by the installed PyTorch package.
4. `TORCH_CUDA_ARCH_LIST` covers the target GPU.

```bash
python -m pip install -U pip setuptools wheel
python -m pip install -U torch numpy ninja
export CUDA_HOME="$(dirname "$(dirname "$(command -v nvcc)")")"
export TORCH_CUDA_ARCH_LIST="<compute-capability-list>"
MAX_JOBS=4 CXX=g++ python setup.py install --force_cuda --blas=openblas --cuda_home="$CUDA_HOME"
```

For CUDA builds with OpenBLAS headers outside the default search path:

```bash
MAX_JOBS=4 CXX=g++ python setup.py install --force_cuda --blas=openblas --cuda_home="$CUDA_HOME" \
  --blas_include_dirs="<blas-include-dir>" \
  --blas_library_dirs="<blas-library-dir>"
```

### 4. Source route: MKL build

Use MKL when the environment is already MKL-oriented, especially on Intel/conda stacks:

```bash
conda install -c intel mkl mkl-include
MAX_JOBS=4 CXX=g++ python setup.py install --blas=mkl
```

If an MKL install is not auto-discovered, ask the user for the MKL include and library directories and pass them with `--blas_include_dirs` and `--blas_library_dirs`.

### 5. System package prerequisites on Debian-like systems

When using a system Python instead of a managed environment, install a compiler, Python headers, and OpenBLAS headers before building:

```bash
sudo apt install build-essential python3-dev libopenblas-dev
python3 -m pip install -U pip setuptools wheel
python3 -m pip install torch numpy ninja
python3 setup.py install --blas=openblas
```

Match the installed PyTorch CUDA variant with the CUDA toolkit used by `nvcc` if this is a CUDA build.

### 6. Docker-style CUDA build recipe

The source Docker recipe builds from a PyTorch CUDA development image, sets CUDA architecture and NVCC flags, installs OpenBLAS and build tools, limits parallel build jobs, then runs `setup.py install --force_cuda --blas=openblas`. This self-contained template preserves those choices without requiring a local Dockerfile from the source checkout:

```bash
cat > Dockerfile.minkowski <<'DOCKER'
ARG PYTORCH="1.12.0"
ARG CUDA="11.3"
ARG CUDNN="8"
FROM pytorch/pytorch:${PYTORCH}-cuda${CUDA}-cudnn${CUDNN}-devel

ENV TORCH_CUDA_ARCH_LIST="6.0 6.1 6.2 7.0 7.2 7.5 8.0 8.6"
ENV TORCH_NVCC_FLAGS="-Xfatbin -compress-all"
ENV MAX_JOBS=4

RUN apt-get update && apt-get install -y git ninja-build cmake build-essential libopenblas-dev
RUN apt-get clean

WORKDIR workspace
RUN git clone --recursive "https://github.com/NVIDIA/MinkowskiEngine" MinkowskiEngine
WORKDIR MinkowskiEngine
RUN python setup.py install --force_cuda --blas=openblas
DOCKER

docker build --build-arg PYTORCH=1.12.0 --build-arg CUDA=11.3 --build-arg CUDNN=8 \
  -t minkowski_engine -f Dockerfile.minkowski .
docker run --rm --gpus all minkowski_engine \
  python -c "import MinkowskiEngine as ME; print(ME.__version__, ME.is_cuda_available())"
```

For CPU-only containers, start from a CPU PyTorch image or install CPU PyTorch, remove `--force_cuda`, and add `--cpu_only`.

## Dry-run command helper

From this sub-skill directory, print a safe CPU command:

```bash
python scripts/build_command_helper.py --mode cpu --blas openblas --max-jobs 4
```

Print a CUDA command template:

```bash
python scripts/build_command_helper.py --mode cuda --blas openblas \
  --cuda-home "$CUDA_HOME" --torch-cuda-arch-list "<compute-capability-list>" --max-jobs 4
```

The helper never installs anything; it only prints commands and reminders.

## Minimal post-install checks

Run these after any install route:

```bash
python -m pip check
python - <<'PY'
from importlib.metadata import version
import torch
import MinkowskiEngine as ME

print("MinkowskiEngine distribution:", version("MinkowskiEngine"))
print("MinkowskiEngine module:", ME.__version__)
print("torch:", torch.__version__)
print("torch.cuda.is_available:", torch.cuda.is_available())
print("MinkowskiEngine.is_cuda_available:", ME.is_cuda_available())
if hasattr(ME, "cuda_version"):
    print("MinkowskiEngine.cuda_version:", ME.cuda_version())
if hasattr(ME, "cudart_version"):
    print("MinkowskiEngine.cudart_version:", ME.cudart_version())
PY
```

Interpretation:

- `MinkowskiEngine.is_cuda_available: False` is expected for a CPU-only build and should not be reported as a failed install unless the user requested CUDA.
- For a CUDA build, both PyTorch CUDA availability and MinkowskiEngine CUDA availability should be `True`; if not, use the CUDA troubleshooting table.
- Import-time `OMP_NUM_THREADS` or `CPU_ONLY` warnings are diagnostic warnings, not necessarily fatal errors.
