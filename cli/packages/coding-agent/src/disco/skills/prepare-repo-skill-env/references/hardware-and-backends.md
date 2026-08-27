# Hardware and Backends

## Purpose

Read this reference before choosing torch/CUDA/backend packages or declaring that an install is impossible. Hardware facts determine which wheels can run, whether source compilation is needed, and whether a fallback CPU/backend install is the only valid path.

## Facts to Gather

Always gather:

- OS and architecture: `uname -a`, `platform.machine()`, `x86_64` vs `aarch64`/`arm64`.
- Conda executable and version.
- Python version requested for the target prefix.
- Available RAM and disk space if large source builds or GPU packages are expected.

For NVIDIA, run the applicable terminal commands directly:

```bash
nvidia-smi
nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader,nounits
nvcc --version  # only required for source builds
```

Some older `nvidia-smi` builds do not expose `compute_cap` as a query field. If that
query fails, fall back to:

```bash
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits
```

Then recover compute capability from a Python backend check after torch is installed:
`torch.cuda.get_device_capability(0)`.

Record:

- GPU model/count/VRAM.
- Compute capability.
- Driver version.
- Driver-reported maximum CUDA version from `nvidia-smi`.
- Whether the system has `nvcc`, and which CUDA toolkit version it reports.
- CPU architecture (`x86_64` or `aarch64`), because many CUDA extension wheels are missing on ARM.

For other backends:

- ROCm/Hygon DCU: `rocminfo`, `rocm-smi`.
- Apple MPS: macOS + Apple Silicon `arm64`; verify with torch MPS if torch is used.
- TPU: TPU device/env signals and framework-specific packages such as JAX or torch-xla.
- Ascend/Cambricon/MetaX: vendor tools and framework forks. Use vendor docs; mainstream CUDA wheels will not work.
- CPU-only: still verify imports and `pip check`; do not claim GPU support.

## NVIDIA CUDA Decision Rules

Use this chain:

1. GPU compute capability determines the minimum CUDA generation the package must support.
2. Driver-reported max CUDA determines the highest CUDA runtime a wheel can require.
3. Python version and platform determine whether a wheel exists.
4. Torch CUDA extension packages must match the installed torch ABI and CUDA tag.

Practical torch wheel guidance:

| Hardware | Usual torch wheel direction | Notes |
| --- | --- | --- |
| Volta/Turing/Ampere/Ada/Hopper on modern drivers | `cu121`, `cu124`, `cu126`, or newer supported wheel | Prefer repo-documented version when available. |
| Blackwell (`sm_100`, `sm_120`) | recent `cu128` or newer torch build | Older torch/CUDA wheels may install but fail at runtime. |
| `aarch64` NVIDIA | verify wheel availability before install | Torch has more ARM CUDA support than many extension packages. |
| Old drivers | use an older CUDA wheel or update driver | A wheel requiring newer CUDA than the driver supports cannot run. |

`nvidia-smi` showing "CUDA Version X.Y" means the driver can support CUDA runtime up to X.Y. It does not mean the matching toolkit is installed. Pip torch wheels usually include the CUDA runtime; source builds require a matching toolkit and compiler.

## When to Require GPU Verification

Select the CUDA install path and run a backend smoke test when:

- The user explicitly requested a CUDA/GPU environment.
- The repo package imports CUDA extensions at import time.
- The repo's main APIs require torch CUDA, JAX CUDA, CuPy, TensorRT, vLLM, flash-attn, xformers, deepspeed ops, or similar GPU runtime.
- The later skill needs to inspect GPU-specific APIs or CLI paths.
- An included native test/example is classified with `Backend requirement:
  cuda`, `Backend criticality: required`, and no full CPU substitute.

Do not require CUDA just because the host has a GPU. For package inspection, CPU importability is often enough unless the repo is GPU-only or the user asked for GPU support.

## Backend-Coverage Decisions

Use both repo evidence and host compatibility:

| Selected capability | Host verdict | Environment decision | Readiness consequence |
| --- | --- | --- | --- |
| Required CUDA/ROCm/MPS/vendor backend, no full CPU substitute | Compatible | Install the matching backend variant and pass a minimal device smoke | Eligible for `ok`; run the planned native case after skill integration |
| Required backend, no full CPU substitute | Unavailable, incompatible, or unknown after probing | Do not silently use CPU | `failed`, or `partial` only after explicit user acceptance; never auto-import |
| Optional backend | Unavailable or outside selected scope | Omit expensive backend packages and record the capability as unverified | CPU scope may remain `ok`, but do not claim backend verification |
| Alternative backend with full CPU substitute | CPU path is evidence-backed | Prepare CPU and run the equivalent selected check | May be `ok`; record which alternative was verified |
| Multiple required incompatible variants | Each host path is compatible | Use separate prefixes per variant | All required prefixes/smokes must pass for `ok` |

A GPU-capable environment normally handles CPU checks too; do not create a
second CPU prefix without a conflicting dependency variant or an independently
selected CPU-fallback claim. Conversely, never install a CPU-only framework
build and treat a successful import as CUDA/ROCm verification.

If required hardware is unavailable, give the user three explicit choices:
repair/use compatible hardware, narrow the extraction scope so the backend is
no longer claimed, or accept partial drafting. Partial drafting preserves a
blocking backend item for final verification and disables auto-import; it does
not convert the missing runtime evidence into a pass.

## CUDA Verification Signals

For torch-based repos, verify with the target environment's Python. The example
below uses a Unix prefix path; use `conda run --prefix <prefix> python` or the
platform-equivalent environment Python when appropriate:

```bash
/path/to/prefix/bin/python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
    torch.empty((1,), device="cuda")
PY
```

If this fails:

- `torch.cuda.is_available() == False` on a GPU host often means CPU-only torch, driver too old for the wheel, missing NVIDIA libraries, or container GPU passthrough is absent.
- `no kernel image is available` means the installed binary does not support the GPU's compute capability.
- `undefined symbol` or import crashes usually mean ABI mismatch between torch and an extension package.
- `nvcc not found` only matters if building source CUDA extensions.

## ARM and New-GPU Risk

On `aarch64` and new NVIDIA GPUs:

- Assume non-torch CUDA extension wheels may be missing until verified.
- Prefer repo-supported CPU/SDPA/native torch fallback if the extension is optional.
- Use source builds only when compilers, toolkit, RAM, and time budget are adequate.
- Report expected compile time and RAM risk for source builds. Do not silently launch a huge source build without considering host resources.

## Declaring Hardware Impossibility

Declare the current hardware/driver stack unable to satisfy the requested environment only after you have concrete evidence, such as:

- Requested CUDA backend but no NVIDIA GPU is visible.
- GPU compute capability requires a newer CUDA generation than the driver can support, and driver updates are outside the task.
- Required wheel does not exist for the platform/Python/CUDA combination and source build prerequisites are unavailable or unsupported.
- Vendor accelerator requires a vendor-specific framework fork that is not installable for the requested Python/platform.
- The package requires GPU features but the host is CPU-only and no CPU fallback exists.

The failure report must name the missing or incompatible component and a realistic next step: change backend, change Python version, choose a different wheel tag, install toolkit/compiler, update driver, use CPU fallback, or run on different hardware.
