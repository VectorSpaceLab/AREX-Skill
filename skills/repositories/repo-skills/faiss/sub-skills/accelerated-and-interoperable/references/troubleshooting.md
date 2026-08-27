# Accelerated and interoperability troubleshooting

Use the checker first:

```bash
python path/to/this/sub-skill/scripts/check_backend.py --json
```

Keep its report with the exact Python executable, Faiss package/build, OS,
device visibility, and library paths. Do not diagnose a GPU failure from host
hardware alone.

## `AttributeError: StandardGpuResources` or missing GPU symbols

**Meaning:** the imported Faiss extension is CPU-only, the wrong environment is
active, or the GPU wrapper failed to load. In the verified environment,
`faiss-cpu 1.15.0` intentionally has no `StandardGpuResources`, `GpuIndex*`,
CPU-to-GPU clone helpers, or GPU count function and reports zero GPUs.

**Safe fallback:** use the CPU `IndexFlat*`/other CPU index with contiguous
NumPy `float32` inputs. Keep the same metric, dimension, IDs, and `k`; run the
CPU smoke and document that GPU acceleration was skipped. Do not monkey-patch
missing classes or infer that a host A100 changes a CPU wheel.

**GPU path:** install a compatible `faiss-gpu` or `faiss-gpu-cuvs` artifact, or
rebuild with the appropriate CMake flags and toolkit. Verify `import faiss`,
GPU symbols, `get_num_gpus()`, and one small transfer in that same environment.
Do not mix CPU and GPU packages or leave a stale `PYTHONPATH` pointing at a
second Faiss checkout.

## Symbols exist but `get_num_gpus() == 0`

Separate binding capability from device visibility. Check process-local
`CUDA_VISIBLE_DEVICES`, container GPU passthrough, driver compatibility, and
whether the package's CUDA runtime can initialize. A host `nvidia-smi` result is
not enough. Skip GPU allocation when the count is zero. For ROCm, inspect HIP
visibility instead; for Metal, check macOS/Apple Silicon and the Metal device
count. Never force device 0 when no device is visible.

## `nvcc`/CMake configuration failure

`FAISS_ENABLE_GPU=ON` causes the top-level CMake project to enable CUDA unless
`FAISS_ENABLE_ROCM=ON`. A missing `nvcc` or toolkit is an expected configure
block, not a Python issue. Install/use one supported toolkit, or set
`-DCUDAToolkit_ROOT=...` to the intended installation; then configure with
`CMAKE_CUDA_ARCHITECTURES` matching deployment devices. Do not point CMake at
headers from one toolkit and libraries from another. For ROCm, use HIP and
hipBLAS with `FAISS_ENABLE_ROCM=ON`; do not pass CUDA-only assumptions.

`FAISS_ENABLE_CUVS=ON` additionally requires GPU support and discoverable
cuVS/RMM/RAFT dependencies. `FAISS_ENABLE_SVS=ON` can download/build the SVS
runtime; budget for that build and make its resulting runtime discoverable to
C++ consumers.

## Dynamic-library or ABI errors

For errors such as `ImportError: lib...so not found`, undefined CUDA/cuBLAS
symbols, `GLIBCXX_*` failures, or crashes at import:

1. Print `sys.executable`, `faiss.__file__`, and the actual package metadata.
2. Run `ldd` on the loaded Faiss shared object on Linux or `otool -L` on macOS
   (use the platform equivalent on Windows).
3. Check that `libfaiss`, `libgpufaiss`, `libfaiss_c`, or `libgpufaiss_c`,
   Python/NumPy ABI, BLAS/OpenMP, CUDA/ROCm, cuVS/RMM, and SVS runtime all come
   from a coherent build/environment.
4. Inspect `LD_LIBRARY_PATH`/`DYLD_LIBRARY_PATH`, rpath, and container mounts;
   remove stale toolkit paths before retrying.
5. Rebuild the extension against the active Python and NumPy if the binary was
   copied between environments.

Avoid “fixing” an ABI issue by loading a random system library first. Static and
shared Faiss builds also have different deployment requirements; do not link a
consumer against headers from one build and a library from another.

## GPU clone, allocation, or parity failure

Check, in order:

- `d`, metric, `k`, dtype, shape, and C-contiguity of every input.
- Device ID is process-visible and is selected after honoring
  `CUDA_VISIBLE_DEVICES`.
- GPU memory and temporary-memory settings; lower the test size first.
- The CPU index was trained before cloning when its type requires training.
- The selected index is supported by the backend. Leave
  `allowCpuCoarseQuantizer=False` unless a deliberate CPU coarse-quantizer
  fallback is required.
- For multi-GPU runs, choose replication versus IVF sharding intentionally and
  verify total IDs and merge behavior.

Use exact Flat L2 first. Float16, cuVS, IVF, and approximate graph paths can
legitimately differ numerically or in tie ordering. Use tolerances/recall
criteria appropriate to the workload, not an unjustified bitwise comparison.
A parity result on one GPU does not prove multi-GPU, cuVS, ROCm, Metal, or SVS.

## CUDA/Torch stream or device errors

A CUDA tensor on a CPU index is unsupported. A non-contiguous tensor or wrong
Torch dtype can produce assertions or bad pointer interpretation. Call
`tensor = tensor.contiguous()` and verify dtype/device/shape before invoking
Faiss. Keep all arguments in one representation (all NumPy or all Torch).

Set the intended Torch device before creating/selecting Faiss resources. Use
`faiss.contrib.torch_utils.using_stream` for the current or explicit Torch
stream; it temporarily changes the Faiss resource stream and restores it. Do
not destroy or reuse a user-owned stream while Faiss work is pending. Add an
explicit synchronization only at a known handoff boundary, not as a substitute
for correct stream ordering.

## cuVS/CMake says enabled but regular GPU behavior appears

CMake capability and runtime dispatch are separate. Check that the imported
Python/native artifact is the build just configured, the `use_cuvs` config or
cloner option is true, and the chosen index type is one of the cuVS-backed
implementations. cuVS is opt-in in the public GPU configuration and can be
rejected for unsupported architectures/configurations. Compare a regular GPU
index and cuVS index on a small workload and record the different numerical
contract.

## ROCm, Metal, or SVS cannot initialize

- **ROCm:** confirm this is a HIP-built artifact, HIP/hipBLAS versions match,
  AMD devices are visible, and no CUDA package is being imported accidentally.
- **Metal:** confirm Apple Silicon/macOS, `FAISS_ENABLE_METAL`, device 0, and
  `MetalDistance.metallib` lookup. `FAISS_METALLIB_PATH` must point to a valid
  deployed resource, not a source checkout path. The Metal bridge is not a
  CUDA API drop-in for every index or multiple devices.
- **SVS:** confirm CMake completed the runtime build, `libsvs_runtime.so` is
  shipped/located, and selected storage kinds are enabled. Check
  `IndexSVSVamana.is_lvq_leanvec_enabled()` before requesting LVQ/LeanVec.

Each backend is unverified until its own tiny import/construction/search smoke
passes. Fall back to a CPU index when the task permits; do not silently switch
backend semantics for an exactness-sensitive task.

## C API errors, crashes, or leaks

Use the headers installed with the library being linked. C names are prefixed
`faiss_`; opaque types are prefixed `Faiss`; IDs are 64-bit. Check every
recoverable integer return and call `faiss_get_last_error()` immediately. Its
pointer becomes invalid after another Faiss function.

Free every caller-owned Faiss object exactly once, including failed-path cleanup
for objects created before a later operation fails. Free query/result buffers
with the allocator that created them. Do not cast an arbitrary `FaissIndex` to a
specific type; use the provided cast/downcast functions and check for NULL.
GPU C headers require the GPU-enabled library and CUDA headers; a CPU C API
build cannot be upgraded at runtime by merely changing `LD_LIBRARY_PATH`.

## RPC connection or security failure

The contributed server binds `HOST = ""` (all interfaces), uses a simple
pickle request/response protocol, exposes object methods, and lacks
authentication and encryption. Treat “connection refused” as an ordinary
endpoint/bind/firewall problem, but treat “it connects” as **not** a security
proof.

For development, bind/limit access to a private interface or loopback and use a
firewall. For any shared or hostile network, do not expose this demo: replace it
with an authenticated, TLS-protected, allow-listed RPC/API layer with request
size/time/concurrency limits and shard/index-version validation. Never put
credentials or sensitive vectors in logs or pickle payloads. `RestrictedUnpickler`
only limits some deserialized globals; it does not provide authentication,
confidentiality, authorization, or a complete application security boundary.
