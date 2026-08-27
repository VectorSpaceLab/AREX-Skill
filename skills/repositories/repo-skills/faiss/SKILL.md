---
name: faiss
description: "Guides Researchers through Faiss installation, dense and binary
  similarity search, index training and composition, persistence and evaluation,
  and explicitly gated CPU/GPU interoperability workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Faiss

Faiss is a C++ library with Python/NumPy bindings for efficient similarity
search and clustering of dense vectors. Use this skill when a task involves
nearest-neighbor search, vector indexing, clustering, quantization, binary
search, index files, or Faiss CPU/GPU integration.

## Start with the environment gate

1. Identify the distribution and backend required by the task. Use
   `faiss-cpu` for the CPU baseline. Use a documented CUDA/ROCm/Metal/cuVS/SVS
   package or source build only when the requested capability needs it.
2. Run the bundled read-only probe before making backend claims. The
   backend-specific checker is bundled with the accelerated route:

   ```bash
   python path/to/faiss/sub-skills/accelerated-and-interoperable/scripts/check_backend.py --json
   ```

   It reports the imported version, compile options, available GPU symbols,
   device count, optional module status, NumPy availability, and tool/runtime
   signals. A visible GPU does not turn a CPU build into a GPU build.
3. Normalize float inputs to contiguous `float32` arrays of shape `(n, d)`.
   Binary indexes instead use packed `uint8` rows with a bit dimension that is
   divisible by eight. Establish the metric and preprocessing before selecting
   an index.
4. Validate an approximate or compressed index against an exact Flat baseline
   on a bounded fixture before tuning recall, memory, or latency.

For public installation, prefer the documented Conda packages: `faiss-cpu` for
CPU, `faiss-gpu` for CUDA, and `faiss-gpu-cuvs` for the cuVS variant. A source
build uses CMake and can enable Python, CUDA/ROCm, C API, Metal, cuVS, or SVS
independently; do not enable extras merely because they exist.

## Route by task

- [Index selection and search](sub-skills/index-selection-and-search/SKILL.md)
  covers Flat, IVF, HNSW/graph search, metrics, factory strings, result
  contracts, `nprobe`, `efSearch`, range search, and CPU search tuning.
- [Training and compression](sub-skills/training-and-compression/SKILL.md)
  covers train/add/code lifecycles, IVF-PQ, PQ, SQ, residual/additive/RaBitQ,
  transforms, fast scan, reconstruction, and binary/Hamming indexes.
- [Composition and filtering](sub-skills/composition-and-filtering/SKILL.md)
  covers ID maps, selectors, per-search parameters, transforms, refinement,
  child ownership, direct maps, shards, replicas, and advanced IVF inspection.
- [Persistence and evaluation](sub-skills/persistence-and-evaluation/SKILL.md)
  covers byte/file serialization, cloning, mmap/on-disk storage, merge,
  clustering, exact ground truth, recall/precision, and operating points.
- [Accelerated and interoperable](sub-skills/accelerated-and-interoperable/SKILL.md)
  covers CUDA and multi-GPU transfer, cuVS/ROCm/Metal/SVS gates, C++/C APIs,
  Torch buffers, FFI, dynamic-library diagnosis, and RPC boundaries.

If a workflow spans branches, keep the core CPU baseline in the first relevant
route, then follow its explicit sibling link for composition, persistence,
compression, or backend-specific work. Do not treat a benchmark result as
validated until its data, metric, exact baseline, and backend are recorded.

## Minimal CPU check

```python
import numpy as np
import faiss

xb = np.ascontiguousarray(np.random.default_rng(0).random((100, 16), dtype="float32"))
index = faiss.IndexFlatL2(xb.shape[1])
index.add(xb)
D, I = index.search(xb[:2], 4)
assert D.shape == I.shape == (2, 4)
print(faiss.__version__, index.ntotal, faiss.get_compile_options())
```

Read [cross-cutting troubleshooting](references/troubleshooting.md) for
installation/import failures, dtype and shape errors, missing optional
backends, unsafe index files, and thread/runtime problems. Read
[repository provenance](references/repo-provenance.md) before deciding whether
this graph is stale for a changed Faiss checkout.
