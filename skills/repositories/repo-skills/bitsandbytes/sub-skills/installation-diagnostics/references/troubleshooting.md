# Troubleshooting Installation and Backend Failures

Start with read-only evidence. Most bitsandbytes installation failures reduce to one of four mismatches: PyTorch accelerator runtime, bitsandbytes native library filename, system runtime library path, or hardware target support.

## Triage Commands

```bash
python -m bitsandbytes
python sub-skills/installation-diagnostics/scripts/backend-report.py --json
python -c "import torch; print('torch', torch.__version__, 'cuda', torch.version.cuda, 'hip', torch.version.hip, 'cuda_available', torch.cuda.is_available())"
python -c "import bitsandbytes as bnb; print('bitsandbytes', bnb.__version__)"
```

If `python -m bitsandbytes` exits nonzero, keep the full traceback but sanitize home paths, usernames, tokens, and private project names before sharing.

## Symptom Table

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'` or import fails before diagnostics | PyTorch is missing, but bitsandbytes expects PyTorch at import time. | Install a compatible PyTorch first. Choose CPU, CUDA, ROCm, XPU, or HPU PyTorch according to the target backend, then reinstall or retry bitsandbytes. |
| `torch.cuda.is_available()` is false but the user expects CUDA | CPU-only PyTorch, missing driver, no visible GPU, container missing GPU passthrough, or stale environment variables. | Check the PyTorch install selector, GPU driver visibility, container runtime, and `CUDA_VISIBLE_DEVICES`. Do not debug bitsandbytes CUDA kernels until PyTorch sees CUDA. |
| CPU-only CI needs package inspection | Environment intentionally lacks GPUs or uses CPU-only PyTorch. | Use import/version/signature checks and `backend-report.py`. Do not run CUDA tensor smoke tests, and do not claim GPU op success. |
| `Configured CUDA binary not found` | bitsandbytes requested a CUDA library based on PyTorch CUDA or `BNB_CUDA_VERSION`, but the installed package does not include that filename. | Compare `torch.version.cuda`, `BNB_CUDA_VERSION`, and bundled `libbitsandbytes_cuda*` files. Clear the override if it points to an absent binary; otherwise install a matching wheel/PyTorch pair or build from source. |
| `Configured ROCm binary not found` or missing `libbitsandbytes_rocm*` | PyTorch ROCm version or `BNB_ROCM_VERSION` points to a missing ROCm library. | Compare `torch.version.hip`, `BNB_ROCM_VERSION`, and bundled `libbitsandbytes_rocm*` files. Set the override only to a built library's suffix or rebuild with `-DROCM_VERSION`. |
| `BNB_CUDA_VERSION` set in a ROCm environment | Wrong override variable for the backend. | Unset `BNB_CUDA_VERSION`; use `BNB_ROCM_VERSION` only if intentionally selecting a different ROCm library suffix. |
| `BNB_ROCM_VERSION` set in a CUDA environment | Wrong override variable for the backend. | Unset `BNB_ROCM_VERSION`; use `BNB_CUDA_VERSION` only if intentionally selecting a different CUDA library suffix. |
| `libcudart.so`, `cudart64*.dll`, `amdhip64`, or shared object cannot open | The bitsandbytes binary exists, but its CUDA/ROCm runtime dependency is not discoverable. | Add the matching runtime library directory to the platform library path (`LD_LIBRARY_PATH` on Linux), activate the intended environment, remove stale conflicting runtime paths, or install a PyTorch/toolkit pair that ships the needed runtime. |
| `fatbinwrap` | CUDA runtime/toolkit mismatch between the loaded native library and runtime libraries. | Inspect `PATH`, `CUDA_HOME`, `LD_LIBRARY_PATH`, and environment manager library directories for multiple CUDA versions. Make them consistent before rebuilding or rerunning. |
| `no kernel image available` | GPU compute capability is not covered by the loaded binary, or CUDA/PyTorch mismatch selected an incompatible binary. | Check GPU compute capability and wheel target coverage. If unsupported, build from source with `COMPUTE_CAPABILITY` including the device. |
| Import succeeds but a native op fails later | bitsandbytes uses a deferred error handler for some native library failures, so import can succeed until a native method is called. | Trigger diagnostics, inspect the deferred error text, and classify it as missing binary, missing dependency, CPU-only backend, or source checkout without compiled library. |
| `Method ... not available in CPU-only version of bitsandbytes` | A CUDA/ROCm-only native symbol was called while the CPU backend is loaded. | Use CPU-supported workflows only, install an accelerator-enabled PyTorch/backend stack, or move the task to hardware that supports the needed operation. |
| Source checkout says compiled library is missing | The Python package is being imported from source without a built native library. | Build the chosen backend with CMake and install the result. For CPU-only source inspection, avoid native op calls. |
| Jetson/aarch64 wheel imports but CUDA op fails with symbol errors | Generic Linux aarch64 CUDA wheel is not ABI-compatible with Jetson L4T/JetPack runtime libraries. | Build on-device with explicit compute capability, or use a Jetson-specific wheel source chosen by the user. |
| XPU backend not selected | PyTorch is not an XPU build or `torch._C._has_xpu` is false. | Install/activate a PyTorch XPU stack first. Verify PyTorch detects XPU before debugging bitsandbytes. |
| MPS/macOS user asks for CUDA | CUDA/HIP builds are not valid on macOS. | Use macOS arm64 wheel or MPS/CPU guidance; do not suggest CUDA toolkit installation on Apple Silicon. |

## Deep-Dive: Override Mismatch

When a user reports `BNB_CUDA_VERSION=130` and a failure such as `Configured CUDA binary not found`:

```bash
python sub-skills/installation-diagnostics/scripts/backend-report.py --json
python -c "import torch; print(torch.version.cuda, torch.cuda.is_available())"
```

Interpretation:

- If `requested_library` is `libbitsandbytes_cuda130...` and `available_bnb_libraries` does not include that file, the override requests an unavailable binary.
- If `torch.version.cuda` is something else, such as `12.8`, and `libbitsandbytes_cuda128...` exists, recommend clearing `BNB_CUDA_VERSION` and retrying.
- If the desired CUDA 13 binary is genuinely needed but absent, recommend a matching wheel if available or a CUDA source build with CUDA 13 first on `PATH`.
- If the bitsandbytes CUDA 13 binary exists but loading fails on `libcudart`, debug runtime library paths instead of the override.

Use the same pattern for ROCm with `BNB_ROCM_VERSION`, `torch.version.hip`, and `libbitsandbytes_rocm*`.

## Deep-Dive: CPU-Only CI

For CI that only needs imports, signatures, and package metadata:

```bash
python -c "import bitsandbytes, torch; print(bitsandbytes.__version__, torch.__version__)"
python sub-skills/installation-diagnostics/scripts/backend-report.py
```

A valid CPU-only result can include `torch.cuda.is_available(): False`. The correct advice is to keep CPU smoke checks and skip accelerator kernels. Do not run older CUDA-only checks that allocate `torch.rand(...).cuda()`.

## Library Path Hygiene

- `PATH` chooses compilers and command-line tools.
- `CUDA_HOME` or toolkit-specific variables influence builds.
- `LD_LIBRARY_PATH` on Linux controls runtime shared library lookup.
- Environment managers can add their own CUDA runtime libraries under their active prefix.

If multiple CUDA or ROCm runtime versions are visible, ask the user to simplify to one intended runtime before rebuilding. Fix path conflicts before compiling from source; otherwise the build can succeed but runtime loading can still fail.

## Sanitized Issue Report Template

Ask for:

```text
OS and architecture:
Python version:
PyTorch version:
torch.version.cuda / torch.version.hip:
torch.cuda.is_available():
bitsandbytes version:
Install method: wheel or source build
Expected backend: CPU / CUDA / ROCm / XPU / HPU / MPS
BNB_CUDA_VERSION / BNB_ROCM_VERSION values, if set:
Output of python -m bitsandbytes, sanitized:
Output of backend-report.py --json, sanitized:
Minimal traceback:
What was already tried:
```

Do not ask for private environment dumps. If paths are necessary, request shortened path endings or library filenames rather than full home or project paths.
