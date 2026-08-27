---
name: cpp-header-api
description: "Operate hnswlib's C++11 header-only API for HNSW and brute-force
  indexes, filters, persistence, deletion/replacement, stop conditions,
  multivector search, and bounded concurrency."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# C++ header API

Use this sub-skill when the task is about the C++ or header-only interface: including
`hnswlib/hnswlib.h`, constructing `HierarchicalNSW`, `searchKnn`,
`searchKnnCloserFirst`, `BaseFilterFunctor`, `markDelete`, `addPoint`,
`saveIndex`, CMake, epsilon search, multivector search, or C++ concurrency.
This skill covers the 0.9.0 header API and the installed CPU-native extension
facts; it does not expand the Python binding surface.

## Operating contract

- Require an include root containing the public `hnswlib/` headers. Do not assume
  a particular checkout layout, build directory, virtual environment, or dataset.
- Treat the library as header-only. A C++11 compiler compiles the implementation
  into the client; there is no hnswlib binary or CUDA API to link against.
- Keep the `SpaceInterface` object alive until every index using it has been
  destroyed. The index retains its distance function and parameter pointer.
- Use `float` with `L2Space` or `InnerProductSpace` for the normal vector API.
  Read [api-reference.md](references/api-reference.md) before selecting an
  optional stop-condition or multivector signature.

## Standard workflow

1. **Normalize the request.** Identify dimension, metric, capacity, whether labels
   can be deleted/replaced, query ordering, filter requirements, and whether the
   request is optional epsilon or multivector search.
2. **Check the build boundary.** Include `<hnswlib/hnswlib.h>`, compile as C++11,
   add the include root, and use `-pthread` (or the platform equivalent) for code
   using the library's mutexes/threads. Use [workflows.md](references/workflows.md)
   for direct compiler and CMake patterns.
3. **Create the space before the index.** Construct `L2Space(dim)` for squared
   Euclidean distance or `InnerProductSpace(dim)` for `1 - inner product`.
   Construct `HierarchicalNSW<float>` with capacity, `M`, `ef_construction`,
   seed, and replacement policy. Prefer stack ownership or an RAII owner.
4. **Populate deliberately.** Pass a contiguous vector pointer and a stable,
   unique external label to `addPoint`. A repeated label updates its existing
   item. Increase capacity with `resizeIndex` before inserting, or use the
   persistence-based capacity extension described in the references.
5. **Query with the intended ordering.** `searchKnn` returns a priority queue
   whose `top()` is the farthest member of the retained result set. Drain and
   reverse it, or call `searchKnnCloserFirst` for a vector ordered closest first.
   A filter is a live pointer to a functor that accepts external labels.
6. **Apply mutation preconditions.** `markDelete` only marks; it does not remove
   graph connections. Replacement requires construction/load with
   `allow_replace_deleted=true` and `addPoint(..., true)`. Do not call
   `unmarkDelete` as a recovery mechanism while replacement is enabled.
7. **Persist and reload safely.** Call `saveIndex(file)`, destroy the index if
   desired, then construct the load form with the same compatible space. Set
   `ef` again after loading: it is not saved and loading initializes it to 10.
8. **Verify a small invariant.** Assert result count/order, filter acceptance,
   and a post-load query. Run the bundled smoke wrapper with an explicit include
   root; do not use a large stress or benchmark as the basic API gate.
9. **Escalate optional APIs.** For epsilon or multivector work, use the exact
   declarations and data layout in [api-reference.md](references/api-reference.md)
   and the recipes in [workflows.md](references/workflows.md). Do not infer a
   Python equivalent or invent a convenience overload.
10. **Bound concurrency.** Concurrent read-only searches are the normal safe
    pattern; concurrent insertion/update calls are demonstrated and internally
    label-serialized. Coordinate structural operations, persistence, resizing,
    destruction, and mixed read/write phases externally. See
    [concurrency.md](references/concurrency.md).

## API routing map

- Metric and memory layout: [api-reference.md](references/api-reference.md).
- Construction, query, filter, persistence, and mutation recipes:
  [workflows.md](references/workflows.md).
- Threads, compiler flags, OpenMP, native SIMD flags, and ownership:
  [concurrency.md](references/concurrency.md).
- Failure diagnosis, including low `ef`, capacity, paths, deletion policy, and
  benchmark exclusions: [troubleshooting.md](references/troubleshooting.md).
- Executable smoke check: `scripts/run_cpp_smoke.sh --include-dir <include-root>`.

## Hard guardrails

- Do not claim CUDA support, GPU kernels, a compiled library ABI, or a required
  OpenMP dependency. The exposed C++ API is CPU-native and header-only.
- Do not treat a priority-queue pop sequence as closest-first. The queue's
  further-first behavior is intentional; the vector helper reverses it.
- Do not pass `replace_deleted=true` unless the index was created or loaded with
  replacement enabled. Do not use a filter to make an unavailable `k` appear
  available: filtering can legitimately return fewer than `k` items.
- Do not let a temporary query buffer, metric space, filter, stop condition, or
  data backing an in-flight operation go out of scope.
- Do not use the smoke result to make recall, latency, SIMD portability, or
  multi-thread stress claims. Those require a separately chosen workload and
  compatible hardware.

## Completion checklist

Before handing off a C++ solution, confirm:

- the include root and compiler standard are explicit;
- the space outlives the index and matches the data dimension/metric;
- `M`, `ef_construction`, capacity, and query `ef` have an intentional value;
- queue versus closer-first semantics are documented at the call site;
- filters inspect external labels and tolerate fewer than `k` matches;
- deletion/replacement flags match the requested lifecycle;
- persistence reloads with a compatible space and resets `ef` explicitly;
- optional stop-condition signatures were copied from the bundled reference;
- no operation is concurrently resizing, saving, loading, or destroying the index;
- the smoke program compiles and passes with assertions.
