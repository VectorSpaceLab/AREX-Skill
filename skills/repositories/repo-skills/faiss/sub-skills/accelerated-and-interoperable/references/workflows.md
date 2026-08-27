# Accelerated and interoperability workflows

These workflows are bounded and source-independent. Replace only environment,
package, device, and caller-chosen paths. Do not make the source checkout a
runtime dependency.

## 1. Inspect before selecting a backend

From any directory, run:

```bash
python path/to/this/sub-skill/scripts/check_backend.py
python path/to/this/sub-skill/scripts/check_backend.py --json
```

The checker does not allocate GPU resources, build code, download packages,
start servers, or contact a network service. Read the report as separate gates:

1. Can Python import Faiss?
2. Which symbols and compile options are present?
3. Does the binding's own GPU count report a visible device?
4. Are optional Python modules and toolkits discoverable?
5. Has a backend smoke actually passed?

An A100, `nvidia-smi`, or a CUDA driver alone does not satisfy the Faiss GPU
binding/build gate. The prepared environment's correct action is CPU fallback.

## 2. CPU-first recipe with graceful GPU skip

The following deliberately starts with an exact CPU baseline and never accesses
GPU symbols until all gates pass. It is a recipe to adapt, not a promise that
GPU execution is available:

```python
import numpy as np
import faiss

rng = np.random.default_rng(7)
d = 8
xb = np.ascontiguousarray(rng.normal(size=(32, d)).astype("float32"))
xq = np.ascontiguousarray(rng.normal(size=(4, d)).astype("float32"))
k = 3

cpu = faiss.IndexFlatL2(d)
cpu.add(xb)
d_cpu, i_cpu = cpu.search(xq, k)

has_gpu_api = all(hasattr(faiss, name) for name in (
    "StandardGpuResources", "index_cpu_to_gpu", "get_num_gpus"))
ngpu = int(faiss.get_num_gpus()) if has_gpu_api else 0
if not has_gpu_api or ngpu < 1:
    print("SKIP GPU: use the CPU result; GPU Faiss is not available")
else:
    res = faiss.StandardGpuResources()
    gpu = faiss.index_cpu_to_gpu(res, 0, cpu)
    d_gpu, i_gpu = gpu.search(xq, k)
    np.testing.assert_array_equal(i_gpu, i_cpu)
    np.testing.assert_allclose(d_gpu, d_cpu, rtol=1e-4, atol=1e-4)
    print("GPU FlatL2 parity passed on device 0")
```

Use a larger, representative smoke only after this passes. For IVF, train the
CPU index before cloning, preserve metric and index parameters, and document
whether training/addition occurred before or after the transfer.

## 3. One GPU: choose the device explicitly

1. Run the checker and record the reported `get_num_gpus()`.
2. Select a device ID in `[0, ngpu)` that is visible to the process. Respect
   `CUDA_VISIBLE_DEVICES`: Faiss sees the process-local numbering, not
   necessarily the host's physical numbering.
3. Create one `StandardGpuResources` for that device and clone a small CPU
   `IndexFlatL2` or a trained supported index with `index_cpu_to_gpu`.
4. Add/search with contiguous `float32` arrays first. GPU indexes copy CPU
   input/output as needed; keeping data resident on the GPU is an optimization,
   not a correctness prerequisite.
5. Use `index_gpu_to_cpu` when a CPU-owned index is required. Free or release
   the resource after all GPU operations have completed.

For memory pressure, use the resource's `noTempMemory`, `setTempMemory`, or
`setPinnedMemory` deliberately and inspect the resulting behavior. These are
resource controls, not a substitute for reducing an oversized index or query
batch.

## 4. Multiple GPUs: replication versus sharding

Start with an explicit device list, for example `[0, 1]`, only after proving
both IDs are visible and have enough memory. Build one resource per selected
GPU when using the lower-level API. In Python, use
`index_cpu_to_gpus_list(cpu, gpus=[0, 1])` or the all-GPU helper only when
"all" is intentional.

- **Replication**: each GPU owns a copy; queries are distributed and results
  are merged. It is usually the simplest multi-GPU choice for a Flat index and
  needs enough memory for a copy on every device.
- **IVF sharding**: set `GpuMultipleClonerOptions.shard = True` when the index
  is too large to replicate or when inverted lists should be partitioned.
  Verify the shard semantics, ID handling, and total result merge for the
  selected index type.
- **Shared IVF quantizer**: use `common_ivf_quantizer` only when its memory and
  training semantics are understood. It does not mean every index type or
  configuration is supported.

Run the same CPU-vs-GPU parity check on a tiny exact Flat workload before
scaling. For approximate, quantized, cuVS, or sharded IVF paths, compare an
explicit acceptance metric and inspect missing/duplicate IDs; do not claim
bitwise parity.

## 5. cuVS, ROCm, Metal, and SVS gates

### cuVS

Use `FAISS_ENABLE_CUVS=ON` only with GPU enabled and a matching libcuvs/RAFT/RMM
stack. The Python cuVS example configures an RMM pool and opts into cuVS via a
GPU config or `GpuClonerOptions.use_cuvs`. Confirm the field exists and is true
before assuming dispatch. cuVS implementations cover selected IVF-Flat,
IVF-PQ, and CAGRA paths, not every Faiss index. Compare numerical behavior to
the regular GPU implementation on the actual workload.

### ROCm

Use a ROCm-built Faiss with HIP and hipBLAS, not a CUDA package. Confirm the
compiler/toolkit and the built Python/native symbols in the same environment.
The inspected stable install guide states that the ROCm Conda package is not
available; source support is therefore a separate, unverified path here.

### Metal

Metal is an Apple Silicon/macOS CMake backend (`FAISS_ENABLE_METAL=ON`) with a
separate resource/cloner bridge. The implementation loads
`MetalDistance.metallib`, optionally from `FAISS_METALLIB_PATH`. Check the
Metal device count and metallib before cloning. The bridge supports a narrower
surface than CUDA (for example, the public cloner documents Flat variants and
device 0); do not reuse CUDA multi-GPU recipes.

### SVS

Enable `FAISS_ENABLE_SVS=ON` only when CMake can fetch/build the SVS runtime and
the deployed C++ process can locate `libsvs_runtime.so`. Choose a supported
`IndexSVSVamana`/`IndexSVSIVF` storage kind and check
`is_lvq_leanvec_enabled()` before selecting LVQ/LeanVec. Static SVS indexes have
additional mutation/serialization constraints; route persistence details to
the sibling persistence skill.

## 6. C++20 and C API integration

For an application built against an installed Faiss, compile with C++20 and
include the installed headers, then link the matching `libfaiss` (or
`libgpufaiss`) and BLAS/OpenMP dependencies. Keep all libraries from one build
and ensure the runtime loader finds the same versions. A CMake application
should prefer imported targets/configuration from the Faiss installation when
available; otherwise set include and library paths explicitly and validate
transitive dependencies.

For a CPU C API build:

```bash
cmake -S . -B build \
  -DFAISS_ENABLE_GPU=OFF -DFAISS_ENABLE_PYTHON=OFF \
  -DFAISS_ENABLE_C_API=ON -DBUILD_SHARED_LIBS=ON
cmake --build build --target faiss_c example_c -j2
```

For a GPU C API build, add `-DFAISS_ENABLE_GPU=ON` and build `gpufaiss_c`
and `example_gpu_c`. Do not include `c_api/gpu/*.h` or link GPU symbols
against the CPU-only library.

C usage pattern:

```c
FaissIndex *index = NULL;
int rc = faiss_index_factory(&index, d, "Flat", METRIC_L2);
if (rc != OK) { fprintf(stderr, "%s\n", faiss_get_last_error()); return 1; }
rc = faiss_Index_add(index, n, xb);
if (rc != OK) { fprintf(stderr, "%s\n", faiss_get_last_error()); }
faiss_Index_free(index); /* caller-owned; do this on every exit path */
```

Use the exact `faiss_` and `Faiss` names in the installed headers. Check every
recoverable return code, capture the last error immediately, and manually free
all Faiss objects and caller buffers. For FFI, preserve opaque-pointer types,
64-bit IDs, `float` layout, calling convention, and library lifetime; never
reinterpret a C++ object layout in a foreign language.

## 7. Optional Torch tensors

Import the optional Torch utility layer only in an environment with compatible
Torch, NumPy, and Faiss bindings. Keep each call all-NumPy or all-Torch; do not
mix. Make tensors contiguous (`tensor.contiguous()`), use the required dtype,
and ensure shape `(n, d)` with `d == index.d`. CPU Torch tensors can use CPU
indexes; CUDA Torch tensors require a GPU index.

For CUDA tensors, set the intended Torch device first and use the Faiss GPU
resource's default stream or `faiss.contrib.torch_utils.using_stream(res,
stream)` around the call. The helper restores the prior Faiss stream but does
not own the Torch stream. Keep tensors alive until queued work is ordered, and
synchronize only at an intentional boundary.

## 8. RPC deployment boundary

The contributed `rpc.py`/`client_server.py` code is useful for a private,
cooperating shard demonstration: clients send method names and pickle-encoded
arguments, servers invoke methods, and a client can merge shard results. It
binds a server to all interfaces by default and is explicitly not a secure
production service.

Before any real deployment, replace or wrap it with an authenticated and
TLS-protected protocol, bind to a private interface, restrict method names and
payload sizes, validate index/shard versions, cap concurrency, and log without
vectors or secrets. Treat every server as a trust boundary; do not expose
Faiss object methods or pickle payloads to arbitrary clients. A firewall or
private subnet reduces exposure but does not supply application authentication.
