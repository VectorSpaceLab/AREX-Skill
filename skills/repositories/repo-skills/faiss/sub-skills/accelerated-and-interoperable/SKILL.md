---
name: accelerated-and-interoperable
description: "This skill guides Faiss CPU/GPU acceleration, backend-gated
  interoperability, native C/C++ APIs, Torch buffers, and safe RPC boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Accelerated and Interoperable Faiss

Use this sub-skill when a task names `faiss-gpu`, `StandardGpuResources`,
`index_cpu_to_gpu`, `index_cpu_to_all_gpus`, CUDA or multi-GPU execution, cuVS,
ROCm, Metal, SVS, CMake/C++20, the C API, Torch tensors, FFI, or distributed
Faiss/RPC boundaries.

## Route here for

- Checking whether the **installed** Faiss binding was built with GPU, cuVS,
  SVS, or Metal support; distinguishing package/build support from visible
  hardware.
- Cloning a CPU index to one GPU or multiple GPUs, selecting replication versus
  IVF sharding, and copying GPU results back for parity checks.
- Building the optional CUDA, ROCm, cuVS, Metal, or SVS backends, with explicit
  prerequisites and no claims that an unverified backend works.
- C++20/CMake integration, C API/FFI naming and ownership, Torch tensor
  pointers, CUDA device/stream ordering, and dynamic-library/ABI diagnosis.
- Treating the repository's demonstration RPC as a trusted-network example,
  not an authenticated production service.

## Route away

- Generic CPU index construction, search parameters, and ordinary NumPy
  recipes: use [index-selection-and-search](../index-selection-and-search/SKILL.md).
- Codec, quantizer, memory-layout, or precision tuning: use
  [training-and-compression](../training-and-compression/SKILL.md).
- CPU composition, ID selectors, and ordinary shards/replicas: use
  [composition-and-filtering](../composition-and-filtering/SKILL.md).
- Persistence, serialization, and evaluation methodology: use
  [persistence-and-evaluation](../persistence-and-evaluation/SKILL.md).
- Benchmarks, CI, release engineering, and large benchmark datasets are out of
  scope here; use the appropriate sibling or project workflow.

## Operating order

1. Run [the backend checker](scripts/check_backend.py) in the target runtime.
   Treat `import faiss` failure, absent GPU symbols, and `get_num_gpus() == 0`
   as distinct signals.
2. Select the matrix row and gate in [the API reference](references/api-reference.md).
   The prepared inspection facts are CPU-only: `faiss-cpu 1.15.0`, Python
   >=3.10, NumPy `float32`, compile options `OPTIMIZE DD AVX2`, and zero
   reported GPUs. CUDA hardware on the host is not evidence that a CUDA Faiss
   package or runtime is usable.
3. For a GPU task, prove both package symbols and a visible device before
   allocating `StandardGpuResources`. If either gate fails, use the CPU
   fallback; do not install, mutate, or silently select a different backend.
4. Start with a small exact `IndexFlatL2` CPU baseline, clone only after the
   GPU gate passes, and compare labels and distances after copying results to
   host memory. Record tolerance and device IDs; parity is workload- and
   backend-dependent, not a universal guarantee.
5. For native integration, match C++ standard, compiler ABI, CUDA/ROCm toolkit,
   BLAS, Python/NumPy ABI, and shared-library search paths. Keep C API object
   ownership and error-code checks explicit.
6. For Torch, keep tensors contiguous, use compatible dtype/device pairs, and
   order Faiss work with the current CUDA stream. Never pass a CUDA tensor to a
   CPU index or mix NumPy arrays and Torch tensors in one patched call.
7. Treat RPC as an explicit trust boundary. The bundled pickle protocol has no
   authentication or transport encryption and is not safe on an untrusted
   network; isolate it or put an authenticated, encrypted, allow-listed service
   in front of it.

## Bundled resources

- [API and compatibility reference](references/api-reference.md) — package and
  source-build matrix, probes, public GPU/C++/C/Torch/RPC contracts, and ABI
  notes.
- [Workflows](references/workflows.md) — safe backend inspection, CPU fallback,
  tiny one-/multi-GPU transfer/parity, CMake/C API, Torch, and RPC boundary
  workflows.
- [Troubleshooting](references/troubleshooting.md) — CPU-build AttributeError,
  missing toolkit/backend gates, loader/ABI failures, device/stream errors, and
  RPC safety failures.
- [Backend checker](scripts/check_backend.py) — deterministic, no-allocation
  availability report that is safe to run from any working directory and
  gracefully handles missing optional dependencies.

## Verification stance

The CPU package and CPU smoke path were verified. GPU, cuVS, ROCm, Metal, SVS,
Torch-GPU, and network/RPC runtime behavior remain conditional until the target
package, build flags, dynamic libraries, device visibility, and a focused smoke
check all pass in the target environment.
