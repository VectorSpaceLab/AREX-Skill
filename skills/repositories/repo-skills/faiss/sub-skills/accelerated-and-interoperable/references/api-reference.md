# Accelerated and interoperability reference

This reference records source-backed contracts and gates for Faiss 1.15.0-style
builds. It is intentionally not a benchmark or release matrix. Verify the
installed artifact rather than inferring capabilities from the host.

## Evidence and verified baseline

The public README/INSTALL material, root `CMakeLists.txt`, GPU public headers
and Python wrappers, Metal/SVS headers, C API installation guide and examples,
Torch utilities, tutorial transfer examples, and the contributed RPC modules
were inspected. The private inspection environment proved:

- `faiss-cpu 1.15.0` is the prepared CPU package; Python is >=3.10.
- NumPy inputs use the normal row-major `float32` contract for ordinary Faiss
  Python calls.
- Its compile options report `OPTIMIZE DD AVX2`.
- It has no `StandardGpuResources`, `GpuIndex*`, or CPU-to-GPU clone symbols and
  reports zero GPUs.
- The host has NVIDIA A100 x8 and driver `580.126.20`, but `nvcc` is absent.
  This is host evidence only; CUDA Faiss and all GPU runtime claims are
  unverified.

## Package and source-build matrix

| Capability | Supported installation/source gate | Runtime proof required |
|---|---|---|
| CPU package | `faiss-cpu=1.15.0`; Conda channels `pytorch`, `conda-forge`. CPU package is published for Linux x86-64/aarch64, macOS arm64, and Windows x86-64. | Import Faiss, inspect compile options, construct/search a tiny CPU index. |
| NVIDIA GPU | `faiss-gpu=1.15.0`; published Linux x86-64 packages target CUDA 11.4 or 12.1 and use the `pytorch`, `nvidia`, and `conda-forge` channels. Source requires C++20, BLAS, CUDA toolkit, and `nvcc`; set `FAISS_ENABLE_GPU=ON`. | `StandardGpuResources`, GPU clone symbols, `get_num_gpus() > 0`, and a tiny transfer smoke. |
| NVIDIA cuVS | `faiss-gpu-cuvs=1.15.0` package is published for Linux x86-64/CUDA 13.2; channels include `pytorch`, `nvidia`, `rapidsai`, and `conda-forge`, with `libnvjitlink`. Source requires `FAISS_ENABLE_GPU=ON`, `FAISS_ENABLE_CUVS=ON`, `libcuvs=26.06`, RAPIDS RAFT/RMM discovery, and a matching CUDA toolchain. | GPU gates plus explicit `GpuClonerOptions.use_cuvs` or a backend-specific config. cuVS has distinct numerical behavior; compare the actual workload. |
| AMD ROCm | Source option `FAISS_ENABLE_ROCM=ON` requires `FAISS_ENABLE_GPU=ON`, HIP, hipBLAS, and a compatible ROCm toolchain. The inspected INSTALL says a ROCm Conda package is not available. | HIP/ROCm toolchain, built symbols, visible AMD device, and focused smoke. Never infer support from CUDA visibility. |
| Apple Metal | `FAISS_ENABLE_METAL` is intended for Apple Silicon (`arm64`) and CMake rejects non-Apple platforms. The Metal path has its own resources/cloner bridge and requires the packaged/located `MetalDistance.metallib`; `FAISS_METALLIB_PATH` can override lookup. | Apple Silicon, Metal device count, bridge symbols, metallib load, and a Flat-index smoke. Metal is unverified in the prepared Linux CPU environment. |
| Intel SVS | Source `FAISS_ENABLE_SVS=ON`; CMake fetches/builds the SVS runtime (`libsvs_runtime.so`). C++ users must make that runtime discoverable. Public classes include `IndexSVSVamana` and `IndexSVSIVF`, with storage kinds and optional LVQ/LeanVec support. | Built SVS symbols, runtime-library load, and a small index construction/search. SVS is unverified here. |
| C API, CPU | CMake `-DFAISS_ENABLE_C_API=ON`; build target `faiss_c`; produces `libfaiss_c.so` or `.dylib` and C headers. | Compile/link a tiny C caller and check every recoverable return code. |
| C API, GPU | Configure both `FAISS_ENABLE_GPU=ON` and `FAISS_ENABLE_C_API=ON`; build `gpufaiss_c` and `example_gpu_c`; produces `libgpufaiss_c.so`, linked to CUDA runtime/cuBLAS. | Same GPU gates plus C API `faiss_get_num_gpus` and CPU-to-GPU clone. |

Example package commands (run only after choosing the target environment):

```bash
conda install -c pytorch -c conda-forge faiss-cpu=1.15.0
conda install -c pytorch -c nvidia -c conda-forge faiss-gpu=1.15.0
conda install -c pytorch -c nvidia -c rapidsai -c conda-forge \
  libnvjitlink faiss-gpu-cuvs=1.15.0
```

Do not combine the CPU and GPU packages in one environment or treat a package
name as proof that its native extension loaded. Resolve the actual binary and
library dependencies in the environment where the application will run.

## Python GPU transfer API

The normal single-device route is:

```python
res = faiss.StandardGpuResources()
cpu = faiss.IndexFlatL2(d)
gpu = faiss.index_cpu_to_gpu(res, device_id, cpu)
```

GPU indexes accept CPU or GPU-resident inputs and copy as needed. Keeping input
and output resident on the GPU can avoid transfers. `faiss.index_gpu_to_cpu`
returns a caller-owned CPU index. The public C++ equivalents are
`faiss::gpu::index_cpu_to_gpu(provider, device, index, options)` and
`index_gpu_to_cpu(index)`.

For multiple devices, the Python wrapper offers
`index_cpu_to_all_gpus(index, co=None, ngpu=-1)` and
`index_cpu_to_gpus_list(index, co=None, gpus=None, ngpu=-1)`. The lower-level
wrapper creates one `StandardGpuResources` per selected device and calls
`index_cpu_to_gpu_multiple`. `GpuMultipleClonerOptions.shard` chooses sharding
rather than replication; `common_ivf_quantizer` and IVF shard options affect
how inverted lists are partitioned. Use an explicit visible list of device IDs
when reproducibility and resource ownership matter; do not assume IDs are
contiguous or that all visible GPUs have equal memory.

Useful `GpuClonerOptions` fields include `indicesOptions`,
`useFloat16CoarseQuantizer`, `useFloat16`, `usePrecomputed`, `reserveVecs`,
`storeTransposed`, `verbose`, `use_cuvs`, and
`allowCpuCoarseQuantizer`. The default `allowCpuCoarseQuantizer=False` means an
unsupported GPU coarse quantizer should fail instead of silently falling back.
Make fallback explicit when selecting that option.

### Exact parity procedure

Use the same deterministic, contiguous `float32` database and query arrays,
metric, `k`, trained state, and index contents. Search the CPU `IndexFlatL2`
first, search the cloned GPU index second, then compare host labels and
same-row distances. Flat L2 is the appropriate first parity target. For ties,
compare neighbor sets or use a deterministic tie policy; for reduced-precision,
cuVS, IVF, or approximate indexes, require a documented tolerance/recall target
instead of exact label equality. A CPU-only result proves only the CPU path.

## C++20/CMake and ABI

The top-level build sets `CMAKE_CXX_STANDARD 20`. A minimal CPU shared build
with C API is conceptually:

```bash
cmake -S . -B build \
  -DFAISS_ENABLE_GPU=OFF \
  -DFAISS_ENABLE_PYTHON=OFF \
  -DFAISS_ENABLE_C_API=ON \
  -DBUILD_SHARED_LIBS=ON
cmake --build build --target faiss_c -j2
```

For CUDA, add `-DFAISS_ENABLE_GPU=ON`, provide a discoverable toolkit/nvcc,
and set `CMAKE_CUDA_ARCHITECTURES` to the deployment GPU compute
capabilities. For ROCm use `-DFAISS_ENABLE_ROCM=ON` and HIP/hipBLAS. For SVS
use `-DFAISS_ENABLE_SVS=ON`; for cuVS also use
`-DFAISS_ENABLE_CUVS=ON` and satisfy the RAPIDS dependencies. Do not enable
cuVS without GPU support.

When a native extension or application fails to load, compare: OS/architecture,
C++ compiler and libstdc++ ABI, C++20 mode, Debug/Release and `_GLIBCXX_USE_CXX11_ABI`
choices where applicable, BLAS implementation, CUDA major/minor compatibility,
GPU architecture flags, Python and NumPy ABI, and every transitive shared
library. Prefer one coherent environment and inspect `ldd`/`otool -L` (or the
platform equivalent) on the actual installed library. Use `LD_LIBRARY_PATH`,
`DYLD_LIBRARY_PATH`, or an rpath only for deliberate deployment configuration;
do not globally prepend unrelated toolkit versions.

## C API and FFI contract

The C surface uses `faiss_` function names, opaque `Faiss...` types,
`faiss_idx_t`/`idx_t` (64-bit), and `float` components/distances. Constructors
and operations that can fail return an integer `FaissErrorCode`; on failure,
call `faiss_get_last_error()` before another Faiss call because its returned
pointer is invalidated by the next Faiss function. Getter/free functions do not
return an error code. `OK` is zero; `FAISS_EXCEPT`, `STD_EXCEPT`, and
`UNKNOWN_EXCEPT` identify failure classes.

C callers own and manually free returned objects, including indexes, search
parameters, selectors, GPU resources, and cloner options. Do not free the same
opaque pointer twice, and do not use a child object after its owner is freed.
Use `free` for C heap buffers allocated by the caller. The C API does not turn
C++ exceptions into a safe zero-cost ABI: always check return codes around
constructors and operations.

GPU C callers include the GPU headers only in a GPU-enabled build and use
`faiss_get_num_gpus`, `faiss_StandardGpuResources_new`,
`faiss_index_cpu_to_gpu[_with_options]`, and the corresponding free functions.
`libgpufaiss_c` must be loaded with its CUDA/cuBLAS dependencies available; a
CPU-only `libfaiss_c` cannot provide those symbols.

## Torch and FFI interoperability

`faiss.contrib.torch_utils` patches selected Python methods to accept either
NumPy arrays or Torch tensors. Inputs in a call must be uniformly one kind.
Tensor helpers require contiguous tensors and exact dtypes: `float32` (or
explicitly supported `float16` for selected operations), `uint8`, `bfloat16`,
`int32`, or `int64` according to the method. A CUDA tensor requires a GPU index
with `getDevice`; a CPU index cannot consume a CUDA tensor.

The `using_stream` helper sets Faiss GPU resources to the current or supplied
Torch CUDA stream and restores the prior Faiss stream in a `finally` block.
The resource object does not own the supplied stream. Set the correct current
Torch device before selecting the resource/device; avoid sharing one resource
across concurrent work without an explicit stream/ownership plan. Synchronize
or retain tensor lifetimes according to the stream contract before releasing or
reusing buffers.

## RPC boundary

`contrib/rpc.py` is a simple socket protocol using restricted pickle for a
small allow-list of NumPy modules, but the server exposes object methods and
binds to all interfaces by default. The source explicitly says it lacks
security protections and is not for untrusted networks. Use it only on an
isolated/private network or loopback, behind authentication, authorization,
TLS, rate limits, request-size limits, and an allow-listed method facade. Never
expose the demo `run_server` directly to the Internet, send secrets in request
payloads, or assume restricted unpickling is equivalent to authentication.

`contrib/client_server.py` fans a query out to several servers and merges
results. Validate host/port/device ownership and index version on every shard;
secure each hop independently. RPC distribution is reference-only here, not a
claim of production durability or consistency.
