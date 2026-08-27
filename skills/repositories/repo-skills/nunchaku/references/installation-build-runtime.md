# Installation, build, and runtime notes

Use this reference when a task asks to install, build, or diagnose an installed Nunchaku runtime. Keep private environment paths out of user-facing outputs.

## Recommended runtime path: prebuilt wheel

For normal use, prefer a prebuilt Nunchaku wheel matching the user's Python, PyTorch, CUDA, operating system, and GPU architecture.

1. Install a compatible PyTorch CUDA build first. For example, PyTorch 2.7 with CUDA 12.8 uses the PyTorch CUDA 12.8 wheel index.
2. Install the Nunchaku wheel from the project's release channels.
3. Probe the environment with this skill's `scripts/inspect_nunchaku_install.py` before loading large models.

Do not install into a ComfyUI portable Python or any user-managed environment without confirming that the chosen interpreter is the intended target.

## Source-build requirements

From repository docs and `setup.py`:

- Python: `>=3.10`; Python 3.11 is a well-supported choice.
- PyTorch: docs require PyTorch `>=2.5`; Blackwell users need PyTorch `>=2.7`.
- CUDA:
  - Linux: `>=12.2`.
  - Windows: `>=12.6`.
  - Blackwell/RTX 50-series: CUDA `>=12.8`.
- Compiler:
  - Linux: `gcc/g++ >= 11`.
  - Windows: current MSVC via Visual Studio developer tools.
- Submodules: source builds require initialized `third_party` submodules.
- CUDA architectures supported by `setup.py`: `sm_75`, `sm_80`, `sm_86`, `sm_89`, `sm_120a`, and `sm_121a` when the NVCC version supports them.

## Source-build commands

Typical developer build:

```bash
git clone --recurse-submodules https://github.com/nunchaku-tech/nunchaku.git
cd nunchaku
pip install -e ".[dev,docs]"
```

If the repository is already cloned without submodules:

```bash
git submodule update --init --recursive
```

For a faster local build that only targets GPUs visible on the build host, `setup.py` uses `NUNCHAKU_INSTALL_MODE=FAST` by default. For a distributable wheel covering all supported architectures, set:

```bash
NUNCHAKU_INSTALL_MODE=ALL NUNCHAKU_BUILD_WHEELS=1 python -m build --wheel --no-isolation
```

## Build-mode implications

| Setting | Effect | Use when |
| --- | --- | --- |
| `NUNCHAKU_INSTALL_MODE=FAST` (default) | Detects visible CUDA devices and compiles only their SM targets. | Local development or a private environment tied to the current GPU type. |
| `NUNCHAKU_INSTALL_MODE=ALL` | Builds all supported SM targets allowed by the NVCC version. | Creating a wheel for other machines or mixed architectures. |
| `NUNCHAKU_BUILD_WHEELS=1` | Omits `--generate-line-info` from NVCC flags and supports wheel build flow. | Packaging a wheel. |

If a FAST-built source install moves from one GPU family to another, refresh/rebuild it.

## PyTorch CUDA wheels plus source NVCC

When PyTorch is installed from pip CUDA wheels and NVCC/toolkit headers come from another source, the compiler may not automatically search the `nvidia-*` wheel include/library directories. Missing-header errors can include:

- `cublas_v2.h: No such file or directory`
- `cusparse.h: No such file or directory`
- `cusolverDn.h: No such file or directory`
- `nvToolsExt.h: No such file or directory`

A generic repair pattern is to add all installed NVIDIA wheel include/library directories to build-time search paths before rerunning the source install:

```bash
NVIDIA_ROOT="$(python - <<'PY'
import pathlib, nvidia
print(pathlib.Path(nvidia.__file__).parent)
PY
)"
export CPATH="$(find "$NVIDIA_ROOT" -mindepth 2 -maxdepth 2 -type d -name include | sort | paste -sd: -):${CPATH:-}"
export LIBRARY_PATH="$(find "$NVIDIA_ROOT" -mindepth 2 -maxdepth 2 -type d -name lib | sort | paste -sd: -):${LIBRARY_PATH:-}"
export LD_LIBRARY_PATH="$LIBRARY_PATH:${LD_LIBRARY_PATH:-}"
pip install --no-build-isolation -e ".[dev]"
```

Adapt this only inside an explicitly selected build environment. Do not mutate a user-owned environment without approval.

## Runtime sanity checks

Run either root or performance checker:

```bash
python scripts/inspect_nunchaku_install.py --device cuda:0 --pretty
python sub-skills/performance-and-memory/scripts/check_nunchaku_cuda.py --device cuda:0 --pretty
```

A healthy runtime should show:

- `torch` imports.
- CUDA is available and the requested device index is visible.
- `nunchaku` imports.
- Public transformer APIs and helper modules are available.
- The GPU SM maps to an expected Nunchaku precision (`int4` for SM 75/80/86/89, `fp4` for SM 120/121).

## Architecture and precision defaults

| GPU family | Typical SM | Default asset precision | Notes |
| --- | --- | --- | --- |
| Turing / RTX 20-series | 75 | INT4 | Use `torch.float16`, `nunchaku-fp16` attention for FLUX, and offload if VRAM is tight. Quantized T5 encoder is documented as not yet for Turing. |
| Ampere / A100/RTX 30-series | 80/86 | INT4 | `torch.bfloat16` is the normal path. |
| Ada / RTX 40-series | 89 | INT4 | `torch.bfloat16`; FP16 attention can be a speed candidate. |
| Blackwell / RTX 50-series | 120/121 | FP4 | Requires PyTorch `>=2.7` and CUDA `>=12.8`. |

Use `nunchaku.utils.get_precision(device=...)` when possible rather than hard-coding the precision.

## What not to do

- Do not call a CPU-only environment ready for Nunchaku quantized inference.
- Do not run all examples/tests as an install smoke. Use a safe import/CUDA check first and defer native examples to selected verification cases.
- Do not rely on a source checkout being present in downstream user projects. Package APIs and bundled scripts should be sufficient.
- Do not silently choose model assets that may require gated Hugging Face access; ask for local paths or credentials policy.
