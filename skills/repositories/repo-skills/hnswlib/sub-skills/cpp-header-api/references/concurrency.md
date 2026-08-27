# Concurrency and build boundaries

hnswlib is a header-only CPU implementation. Thread safety is a property of the
specific operation mix and caller-owned buffers; it is not a promise that every
method can run concurrently with every other method.

## Recommended operation matrix

| Operation mix | Guidance |
|---|---|
| Search with search | Supported pattern. Give each call its own query/result/filter state and do not mutate those objects during the call. |
| Add with add/update | The implementation has per-label operation locks and the native C++ examples use parallel insertion/update batches. Use unique labels where possible and still coordinate shared input generation and exception propagation. |
| Mark/delete with mark/delete | The implementation locks by label and the native stress coverage exercises disjoint label ranges. Do not race two lifecycle decisions for the same label. |
| Replacement with replacement | Use the replacement-enabled constructor/load policy. Coordinate deleted-slot ownership and label allocation; do not combine with an unsynchronized `unmarkDelete`. |
| Search with add/update/delete | Treat as a mixed read/write phase requiring external coordination unless the application has separately validated its exact operation mix and lifetime. Do not infer safety from per-label locks alone. |
| Resize with any search/mutation | Not safe to overlap. `resizeIndex` reallocates storage and replaces lock/visited-list structures. Quiesce all operations first. |
| Save/load with search/mutation | Quiesce the index for save; construct/load a separate object before publishing it. Do not destroy or replace the space while either object uses it. |
| Destruction/clear with anything | Never overlap. Join worker threads before destroying the index, space, filter, stop condition, or backing buffers. |

The C++ examples demonstrate parallel batches of `addPoint`, read-only search,
filtering, deletion, and replacement. They use a thread executor that joins
workers and rethrows a captured exception. Reuse that pattern or another
executor with the same properties: bounded workers, joined completion, and
failure propagation.

## Per-call ownership rules

- A `SpaceInterface` implementation must outlive every index that copied its
  distance function and parameter pointer. In particular, `L2Space::get_dist_func_param`
  points at its dimension member.
- A query buffer and an input vector must remain valid and immutable for the
  duration of its call. Give each worker a separate query slice or protect a
  shared mutable buffer.
- A filter functor and a custom stop condition are stateful call collaborators.
  Do not share one mutable instance across searches unless the caller supplies
  synchronization and the implementation is intentionally designed for it.
- Each worker should consume its own result object. Writing results into distinct
  vector slots is safe at the application layer; concurrent `push_back` on one
  vector is not.
- Join all worker threads before deleting the index or its space. A detached
  search may retain internal pointers after the caller returns.

The implementation uses internal locks for label operations, graph links, the
label lookup table, deleted-slot bookkeeping, and a visited-list pool. Those
locks serialize important pieces of add/update/delete work; they do not make
external data ownership, file publication, resize, or object destruction
implicitly safe.

## C++11 and native build flags

The minimum language level is C++11. A portable direct build can use:

```sh
"${CXX:-c++}" -std=c++11 -O2 -pthread \
  -I"${HNSWLIB_INCLUDE}" app.cpp -o app
```

The project CMake example/test branch configures compiler-specific options:

- GNU uses C++11, optimization/vectorization, `-fopenmp`, and `-march=native`.
- Clang uses C++11, optimization/vectorization and an OpenMP option, adding a
  supported native CPU option when available.
- MSVC uses C++11-compatible exception handling, optimization, `/openmp`, and
  `/EHsc`.

These are example-build choices, not a universal consumer requirement. Use
`-pthread` for POSIX C++ threading. Add `-fopenmp`/the platform equivalent only
when the client or selected build actually uses OpenMP and the compiler/runtime
are installed. OpenMP is not a required hnswlib API dependency.

The headers conditionally select SSE/AVX/AVX512 distance implementations when
compiler and CPU support are visible. `-march=native` can improve local
performance but may make a binary unsuitable for another CPU; omit it for a
portable deployment or choose an explicit compatible target. Do not promise
CUDA, a GPU backend, or a CUDA compiler flag: no CUDA API is exposed.

## Safe batch patterns

For a read-only query batch:

1. Finish construction and publish an immutable index.
2. Set `ef` before starting workers.
3. Partition query rows so each worker owns its input span and result slot.
4. Use a local filter/stop object or synchronize access to shared state.
5. Join every worker before changing or destroying the index.

For a build/update batch:

1. Allocate all input data and stable labels before launching workers.
2. Use one `addPoint` per label at a time; avoid racing updates to the same
   label unless the final winner is deliberately unspecified.
3. Capture the first worker exception and stop scheduling new work.
4. Join workers, then perform searches or persistence in a quiescent phase.

For deletion/replacement:

1. Establish a replacement-enabled index before any `addPoint(..., true)` call.
2. Assign each deleted label/slot to one replacement operation.
3. Do not concurrently call `unmarkDelete` on a slot that may be reused.
4. Join replacement workers before querying or saving unless the application has
   an independently verified mixed-phase protocol.

## Stress and benchmark boundary

Small smoke checks establish compilation, ownership, query ordering, filtering,
and persistence. They do not establish throughput, recall, SIMD portability,
allocator behavior at scale, or long-running race freedom. Large stress runs
also need a dataset, memory budget, timeout policy, and hardware-specific
compiler choices. Keep such runs out of the default smoke gate and report them
as a separate verification class.
