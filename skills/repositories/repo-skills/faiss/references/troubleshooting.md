# Cross-cutting troubleshooting

Read this reference when a Faiss workflow fails before a focused sub-skill can
classify the problem. Keep the first diagnostic small and deterministic; do not
download benchmark data or switch backends silently.

## Import and installation

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'faiss'` | The package is not installed in the active Python, or the wrong interpreter is being used. | Run `python -m pip show faiss-cpu` (or the selected distribution), then `python -c "import faiss; print(faiss.__version__)"`. Use the same Python for installation and execution. Prefer the documented Conda package. |
| `ImportError` mentioning `swigfaiss`, BLAS, OpenMP, or a shared library | Incomplete wheel/build, missing native runtime, or ABI mismatch. | Reinstall a matching wheel or rebuild with the documented compiler/BLAS prerequisites. Inspect `faiss.get_compile_options()` only after import works; do not paper over a loader error with arbitrary `LD_LIBRARY_PATH`. |
| `faiss.__version__` is absent or unexpected | A stale checkout/module shadows the installed package, or package artifacts are mixed. | Run from a neutral directory, inspect `importlib.metadata.version("faiss-cpu")`, and compare the imported package version. Remove only the unintended installation after identifying it. |
| CMake cannot find BLAS | BLAS development/runtime libraries are absent or not discoverable. | Install one supported BLAS implementation and pass its documented CMake discovery hints. Keep Python, compiler, BLAS, and NumPy ABI choices consistent. |

## Input and API contracts

- Float index methods expect two-dimensional, contiguous `float32` arrays with
  the index dimension `d`. Convert explicitly with
  `np.ascontiguousarray(x, dtype="float32")`; do not rely on an implicit cast
  when debugging a result mismatch.
- Binary indexes expect packed `uint8` rows and a bit dimension divisible by
  eight. Use the binary packing helpers in the training route; do not pass a
  float matrix to `IndexBinary*`.
- `Index.add` requires a trained index when `is_trained` is false. Call
  `train(training_vectors)` before `add(database_vectors)`, then assert
  `is_trained` and `ntotal`.
- `search(x, k)` returns `(D, I)`. A missing neighbor uses label `-1`; do not
  interpret an invalid label as a real database ID. `range_search` returns
  `lims` plus flat `D` and `I` arrays, so slice results per query with
  `lims[i]:lims[i+1]`.
- For cosine similarity, normalize both database and query vectors and use
  `METRIC_INNER_PRODUCT`. Comparing normalized queries with unnormalized data
  changes the task, not just the score scale.
- `k`, `nprobe`, `efSearch`, dimensions, list counts, subquantizers, and code
  bits are configuration contracts. Validate them before launching a long
  training run.

## Backend and optional dependencies

- A CPU distribution can import successfully while exposing no
  `StandardGpuResources`, `GpuIndex*`, or `index_cpu_to_gpu`. This is an
  expected build distinction, not an API typo. Run the bundled
  `sub-skills/accelerated-and-interoperable/scripts/check_backend.py --json`;
  choose CPU fallback or install a documented GPU variant in a separate
  compatible environment.
- A visible NVIDIA device is not proof that Faiss GPU symbols or CUDA runtime
  libraries are installed. Require package symbols, a positive device count,
  and a tiny CPU-to-GPU parity check before using a GPU index.
- cuVS, ROCm, Metal, and SVS are optional build/package variants. Treat a
  missing marker, import, toolkit, platform, or device as an explicit gate and
  do not claim runtime coverage from source documentation alone.
- `faiss.contrib` helpers may require SciPy, h5py, PyTorch, a GPU build, or
  external datasets. Import the specific helper and report the missing optional
  dependency; do not install every extra by default.
- PyTorch interoperability has dtype, contiguity, device, and CUDA-stream
  requirements. Do not mix NumPy and Torch inputs in a patched call, and do not
  pass CUDA tensors to a CPU index.

## Runtime, persistence, and safety

- Start with `omp_get_max_threads()` and a small smoke. Excessive OpenMP
  threads can make a tiny test appear hung or cause oversubscription; set a
  bounded thread count for a controlled trial and restore the caller's value.
- Treat serialized indexes and index files as untrusted artifacts. Bound file
  size, isolate deserialization, and verify metric, dimension, and expected
  index type. Keep mmap-backed files present and unchanged for the lifetime of
  the mapped index.
- Use temporary directories for smoke artifacts and atomic replacement for
  durable files. Do not use a fixed shared filename or overwrite an existing
  index without an explicit destination decision.
- If recall changes, compare against an exact Flat index built with the same
  metric, normalization, query set, and `k`. Separate candidate loss (`nprobe`,
  `efSearch`) from codec distortion and from a mismatched ground truth.

## Stop conditions

Stop and ask for an environment, permission, hardware, credentials, or data
change when the task requires a backend that is unavailable, a private dataset,
a network/RPC service, a large benchmark, or a destructive index mutation.
Record the exact unverified capability instead of silently replacing it with a
CPU result.
