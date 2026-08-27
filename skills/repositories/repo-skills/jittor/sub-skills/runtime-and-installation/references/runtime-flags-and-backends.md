# Runtime flags and backends

This reference covers the install/runtime choices that matter before any deeper Jittor workflow: package installation, compiler selection, CPU JIT validation, and optional backend enablement.

## What is required vs optional

- **Required:** a working Python environment plus a C++ compiler that can build Jittor's first JIT runtime objects.
- **Optional:** CUDA, ROCm, MPI/NCCL, ACL/vendor accelerators, and MKL/DNNL acceleration.
- **Truth rule:** only claim an optional backend after its own smoke passes.

## Installation paths

| Path | When to use | Notes |
| --- | --- | --- |
| pip | Fastest path for supported native setups | Requires the base Python runtime, compiler, and the package dependencies from metadata. |
| Docker | Safest when host setup is messy or OS support is unclear | Public images exist for CPU-only and CUDA-enabled Linux; Docker is also the safest Windows/macOS fallback. |
| Manual | When you need explicit compiler or Python control | Use a supported compiler and Python version, then install the package and validate with a CPU smoke. |

## Platform notes

| Platform | High-level note |
| --- | --- |
| Linux | Primary native target. Use `g++` or `clang++`, plus Python dev headers and OpenMP support. |
| macOS | Native support is documented. Prefer `clang++` because the platform's `g++` is often a clang wrapper. |
| Windows | README documents a Windows path and automatic CUDA handling, but package metadata still guards non-Linux/Darwin installs unless explicitly forced. Treat native Windows as experimental and prefer Docker unless you already have a vetted setup. |

## Package metadata and prerequisites

- Python support: `>=3.7` on native Unix-like setups; `>=3.8` is documented for Windows.
- Runtime dependencies from package metadata: `numpy<2.0`, `tqdm`, `pillow`, `astunparse`, plus `pywin32` on Windows.
- Native install prerequisites: Python dev headers, a C++ compiler, and OpenMP support where the compiler stack expects it.

## Compiler and runtime knobs

| Knob | Meaning | Typical use |
| --- | --- | --- |
| `cc_path` | Selects the host C++ compiler Jittor uses for JIT/runtime builds | Point it at `g++`, `clang++`, or the platform compiler you want Jittor to use. |
| `cc_flags` | Extra host-compiler flags | Use only when you know you need extra include/lib or warning flags. |
| `kernel_flags` | Extra flags for generated kernels | Advanced tuning only. |
| `nvcc_path` | Path to the CUDA compiler | Set this when CUDA should be available; set it to an empty string to keep Jittor from trying to auto-enable CUDA during CPU-only validation. |
| `nvcc_flags` | Extra CUDA compiler flags | Advanced CUDA tuning only. |
| `jt.flag_scope(...)` | Temporary flag override scope | Preferred way to localize backend/debug changes. |

### Backend flags worth knowing

| Flag or env | Meaning | Notes |
| --- | --- | --- |
| `jt.flags.use_cuda` | CUDA runtime selector | `0` off, `1` try CUDA, `2` force CUDA. Use `1` for normal optional enablement and reserve `2` for strict backend checks. |
| `jt.flags.use_rocm` | ROCm runtime selector | Enable only on compatible ROCm hosts. |
| `jt.flags.use_acl` | ACL/vendor accelerator selector | Enable only on compatible vendor hardware. |
| `use_mkl` | Enable optional CPU acceleration assets | Leave on for normal CPU performance; set to `0` if you need to skip the optional oneDNN/MKL fetch/build path. |
| `use_mpi` | Enable MPI probing and distributed support | Set to `0` if you are validating a single-process environment without MPI toolchains. |
| `lazy_execution` | Lazy vs eager execution | `1` is the default. Set to `0` for clearer traces and less confusing failures. |
| `trace_py_var` | Python stack tracing depth | `3` gives the strongest trace context and is the most useful for failure localization. |
| `profile_memory_enable` | Memory profiler switch | Use with `trace_py_var=3` when investigating memory growth. |
| `JT_CHECK_NAN` | Numeric sanity guard | Useful for finding the first NaN/Inf producer during debugging. |

## CPU baseline

The CPU baseline is the required operating target. A valid CPU smoke should:

1. Import `jittor` successfully.
2. Create a tiny Var.
3. Force one JIT compile and one synchronized reduction.
4. Avoid claiming any accelerator backend.

Example shape of a safe smoke:

```bash
python - <<'PY'
import jittor as jt
x = jt.float32([1, 2, 3])
y = (x * x).sum()
print({"version": jt.__version__, "sum_squares": float(y.data), "has_cuda": bool(jt.has_cuda)})
PY
```

## CUDA selection pattern

Use this pattern when CUDA is intentionally part of the task:

```python
import jittor as jt

if not jt.has_cuda:
    raise SystemExit("CUDA is not available to Jittor.")

jt.flags.use_cuda = 1
x = jt.float32([1, 2, 3])
print(float((x * x).sum().data))
```

Notes:

- A visible NVIDIA GPU is not enough.
- If `jt.has_cuda` is false, validate CPU-only behavior instead of claiming CUDA.
- Use `jt.flags.use_cuda = 2` only when you want an explicit hard failure if the CUDA path is not really present.

## ROCm, MPI, and ACL selection pattern

- ROCm: use `jt.flags.use_rocm = 1` only on a compatible ROCm system.
- MPI: Jittor auto-detects `mpicc`; if detection fails, point `mpicc_path` at the MPI compiler wrapper or disable MPI probing with `use_mpi=0`.
- ACL/vendor accelerators: enable only when the backend is present and the corresponding Jittor compiler probe reports support.

## Optional CPU acceleration notes

- Jittor may fetch or build a packaged CPU acceleration library the first time it needs it.
- If you already have a compatible oneDNN/MKL build, the environment can point Jittor at it instead of relying on the packaged fetch path.
- If the optional CPU acceleration path fails and the task only needs a basic import or JIT validation, disable it and continue with the CPU baseline.

## Smoke commands worth remembering

- `python ../../scripts/check_jittor_env.py` — bundled import/backend diagnostic from the root skill.
- `python ../../scripts/jittor_cache_doctor.py` — safe cache inspection before any cleanup decision.
- `python scripts/jittor_perf_probe.py --warmup 1 --rerun 5` — bounded CPU-first timing smoke.
- `python scripts/jittor_perf_probe.py --use-cuda --warmup 1 --rerun 5` — optional CUDA timing smoke only after CUDA is truly configured.
