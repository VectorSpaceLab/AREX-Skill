# MinkowskiEngine build and install troubleshooting

Match the exact symptom first. Most failures come from one of four mismatches: PyTorch versus CUDA toolkit, missing BLAS headers/libraries, an unsuitable compiler/toolchain, or stale native extension artifacts.

## Quick triage commands

Run these in the same environment where the user builds or imports MinkowskiEngine:

```bash
python - <<'PY'
import sys
print("python:", sys.version)
try:
    import torch
    print("torch:", torch.__version__)
    print("torch.version.cuda:", getattr(torch.version, "cuda", None))
    print("torch.cuda.is_available:", torch.cuda.is_available())
except Exception as exc:
    print("torch probe failed:", type(exc).__name__, exc)
PY
command -v nvcc || true
nvcc --version || true
python - <<'PY'
try:
    import MinkowskiEngine as ME
    print("MinkowskiEngine:", ME.__version__)
    print("ME.is_cuda_available:", ME.is_cuda_available())
except Exception as exc:
    print("MinkowskiEngine probe failed:", type(exc).__name__, exc)
PY
```

Do not treat `ME.is_cuda_available(): False` as a failure when the user intentionally built CPU-only.

## Symptom table

| Symptom | Likely cause | Fix |
|---|---|---|
| `BLAS not found from numpy.distutils.system_info.get_info` | No supported BLAS detected; OpenBLAS/MKL headers are missing or not discoverable. | Install OpenBLAS or MKL development files, then rebuild with `--blas=openblas` or `--blas=mkl`. If auto-discovery fails, ask for BLAS include/library locations and pass `--blas_include_dirs=<dir>` and, when useful, `--blas_library_dirs=<dir>`. |
| Linker cannot find `openblas`, `mkl_rt`, `atlas`, or `blas` | Library package missing or not on the build/link path. | Prefer installing BLAS into the active build environment. Then rebuild from a clean source tree command such as `MAX_JOBS=4 python setup.py install --cpu_only --blas=openblas`. If using custom library directories, ensure the compiler/linker can resolve them; this checkout's setup parser accepts `--blas_library_dirs`, but standard environment library discovery is more reliable. |
| `fatal error: cublas_v2.h: No such file or directory` | `CUDA_HOME` points to the wrong toolkit or PyTorch extension discovery cannot find CUDA headers. | Set `CUDA_HOME` from the active `nvcc`: `export CUDA_HOME="$(dirname "$(dirname "$(command -v nvcc)")")"`. Confirm `"$CUDA_HOME/bin/nvcc" --version`, then rebuild with `--force_cuda --cuda_home="$CUDA_HOME"`. |
| NVCC compile segmentation fault or unexpected old CUDA version | A generic CUDA symlink or shell startup changed `CUDA_HOME` to a different toolkit than intended. | Do not rely on the default CUDA directory. Export `CUDA_HOME` in the current shell immediately before building and ensure PyTorch's CUDA runtime matches `nvcc --version`. |
| Build prints `torch.cuda.is_available() is False. MinkowskiEngine will compile with CPU_ONLY` | PyTorch reports no CUDA at build time and `--force_cuda` was not supplied. | If CPU-only is acceptable, continue and verify import. If CUDA is required, install a PyTorch CUDA package, make `nvcc` available, set `CUDA_HOME`, optionally set `TORCH_CUDA_ARCH_LIST`, then rebuild with `--force_cuda`. |
| Import warns `The MinkowskiEngine was compiled with CPU_ONLY flag` | The installed extension is CPU-only. | This is expected for CPU-only installs. For GPU support, uninstall/rebuild in an environment where PyTorch CUDA and the CUDA toolkit are available, then check `ME.is_cuda_available()` again. |
| Import warns `OMP_NUM_THREADS not set` and says it will set `OMP_NUM_THREADS=16` | High-core machine without explicit OpenMP thread limit. | Set a thread count before running Python, often below 24: `export OMP_NUM_THREADS=12; python your_program.py`. This is a performance warning, not an install failure. |
| `undefined symbol`, a C++ ABI-looking symbol, `thrust::system::system_error`, or `CUDA error: invalid device function` after an upgrade | Stale extension artifacts, ABI mismatch, PyTorch/CUDA mismatch, or missing compiled GPU architecture. | Clean and force rebuild: `make clean` then `MAX_JOBS=4 python setup.py install --force --blas=openblas` with the same CPU/CUDA flags used for the target install. For CUDA, match PyTorch CUDA with `nvcc`, and set `TORCH_CUDA_ARCH_LIST` for the GPU. If still broken, use a fresh environment. |
| Compilation dies with `Killed`, OOM, or a cluster memory limit | Too many parallel compiler jobs, especially with CUDA/Ninja. | Lower parallelism: `MAX_JOBS=2 python setup.py install ...`. If using the source Makefile as a prebuild fallback, run a single-threaded `make` first, then `python setup.py install`. Request more memory for CUDA builds. |
| `ModuleNotFoundError: No module named 'pkg_resources'` or torch imports fail through `pkg_resources` | Very new `setuptools` removed the legacy `pkg_resources` import expected by an older PyTorch/build stack. | Install a compatible setuptools in the build environment: `python -m pip install "setuptools<70"`, then rerun the same build command. If using a newer PyTorch stack, upgrading `setuptools` and `wheel` may also be sufficient; choose the path that matches the user's PyTorch version. |
| C++ compile error mentions `std::uint16_t`, `uint16_t`, or missing integer types in bundled pybind11/native headers | Host compiler/header combination needs `<cstdint>` included before those declarations. | Prefer a compatible compiler and clean rebuild. Advanced local workaround: patch the affected local source/header to include `<cstdint>` or use a source-tree compiler wrapper that runs `g++ -include cstdint` and set `CXX=./<wrapper-name>` for this build only. Do not make this global unless other packages need it. |
| `SetuptoolsDeprecationWarning: setup.py install is deprecated` | Modern packaging tools warn about legacy setup invocation. | In this checkout, custom flags such as `--cpu_only`, `--force_cuda`, and `--blas` are parsed by `setup.py`; the warning is not fatal if the build succeeds. For custom-flag builds, use a disposable environment and source-tree `python setup.py install ...`. |
| `pip` rejects `--install-option` | Recent pip versions removed or restrict legacy install options. | Use the source-tree route and pass flags directly to `python setup.py install`. If the user insists on pip-source installation with flags, they need a legacy packaging toolchain, but source-tree setup is clearer and easier to diagnose. |
| Docker CUDA build fails because no matching architecture was compiled | `TORCH_CUDA_ARCH_LIST` omitted the target GPU capability. | Rebuild the image with a capability list that includes the user's GPU. Keep `MAX_JOBS` conservative inside Docker to avoid compile OOM. |

## Recommended recovery workflows

### BLAS recovery

1. Install one supported BLAS development package in the active build environment.
2. Rebuild explicitly:

```bash
make clean || true
MAX_JOBS=4 python setup.py install --cpu_only --blas=openblas
```

3. If the user chose MKL:

```bash
make clean || true
MAX_JOBS=4 python setup.py install --blas=mkl
```

4. If includes are still not found, ask for the include directory and add `--blas_include_dirs=<blas-include-dir>`.

### CUDA recovery

1. Probe PyTorch and CUDA:

```bash
python - <<'PY'
import torch
print(torch.__version__)
print(torch.version.cuda)
print(torch.cuda.is_available())
PY
command -v nvcc
nvcc --version
```

2. Set CUDA variables in the current shell:

```bash
export CUDA_HOME="$(dirname "$(dirname "$(command -v nvcc)")")"
export TORCH_CUDA_ARCH_LIST="<compute-capability-list>"
```

3. Clean and rebuild:

```bash
make clean || true
MAX_JOBS=4 CXX=g++ python setup.py install --force --force_cuda --blas=openblas --cuda_home="$CUDA_HOME"
```

4. Verify:

```bash
python - <<'PY'
import torch
import MinkowskiEngine as ME
print("torch.cuda.is_available:", torch.cuda.is_available())
print("ME.is_cuda_available:", ME.is_cuda_available())
print("ME.cuda_version:", ME.cuda_version())
print("ME.cudart_version:", ME.cudart_version())
PY
```

If PyTorch reports CUDA unavailable after installation, rebuilding MinkowskiEngine alone is not enough; install a matching PyTorch CUDA package first.

### Compile OOM recovery

Use smaller parallelism and avoid CUDA unless required:

```bash
make clean || true
MAX_JOBS=2 python setup.py install --cpu_only --blas=openblas
```

If CUDA is required, keep `MAX_JOBS` low and consider compiling only the needed architecture via `TORCH_CUDA_ARCH_LIST`.

## Setup.py quirks to remember

- The setup script removes the relative `build` directory each run and invokes `pip uninstall MinkowskiEngine -y` before building. Warn users before running it in a shared environment.
- `--force_cuda` overrides `--cpu_only`.
- If PyTorch says CUDA is unavailable and `--force_cuda` is absent, the build becomes CPU-only automatically.
- `--cuda_home` is parsed and printed, but exporting `CUDA_HOME` is still important because PyTorch extension discovery reads the environment.
- `--blas_include_dirs` only takes effect when `--blas` is set.
- The source Makefile is referenced only for source-tree recovery commands such as `make clean` and single-threaded fallback builds. It is not bundled in this sub-skill; ordinary package users should start with `setup.py` commands unless diagnosing a native build failure.
