# C++ troubleshooting

Use the smallest reproducer that preserves the failing contract. Check the
space, index, query, filter/stop object, and file lifetimes before tuning recall
or threads.

## Compiler standard and language errors

**Symptoms:** missing `nullptr`, `override`, `std::atomic`, or template errors;
headers fail before the application code.

**Checks and fixes:**

- Compile with `-std=c++11` or the compiler's C++11 mode. Set
  `CMAKE_CXX_STANDARD 11` and `CMAKE_CXX_STANDARD_REQUIRED ON` on the consuming
  target rather than relying on a toolchain default.
- Use a compiler/runtime combination that supplies C++11 `<thread>`, `<mutex>`,
  `<atomic>`, `<unordered_map>`, and `<random>`.
- Make sure the source is compiled as C++, not passed through a C compiler.
- Do not “fix” a signature error by adding an unobserved overload. Consult
  [api-reference.md](api-reference.md) for the exact 0.9.0 templates.

## Include paths and header discovery

**Symptoms:** `hnswlib/hnswlib.h` or one of its sibling headers cannot be found;
CMake sees an empty target.

**Checks and fixes:**

- The include argument must name the directory containing the `hnswlib/`
  directory, not the `hnswlib/` directory itself when using
  `#include <hnswlib/hnswlib.h>`.
- In a direct compile, inspect the expanded command and confirm `-I"${HNSWLIB_INCLUDE}"`
  is present before compiling.
- In CMake, use the installed/configured `hnswlib::hnswlib` interface target or
  attach the include directory to the client target. There is no `.a`, `.so`,
  or separate hnswlib link flag for the header-only implementation.
- Do not mix headers from different hnswlib revisions in one include search
  order. The saved index and optional signatures must come from a compatible
  header set.

## OpenMP, native flags, and CPU features

**Symptoms:** `omp.h` or OpenMP runtime link errors; unsupported instruction
faults on another machine; performance differs between builds.

**Checks and fixes:**

- OpenMP is not required for a simple header-only client. Remove OpenMP flags
  from a direct smoke compile unless the client uses OpenMP.
- If the client uses OpenMP, enable it consistently at compile and link time
  with the compiler's supported option and install the matching runtime.
- `-march=native` and similar flags target the build host. Omit them for a
  portable artifact or select an explicit CPU baseline supported by deployment.
- The headers choose SSE/AVX/AVX512 implementations conditionally. Do not
  claim that a failed native flag means the API is unavailable; first retry a
  portable C++11 build.
- `-pthread` (or the platform equivalent) is distinct from OpenMP and is the
  normal requirement for POSIX thread/mutex clients.

## Wrong result order or insufficient `k`/`ef`

**Symptoms:** a caller sees a distant result first, gets fewer results, or
recall is lower than expected.

**Checks and fixes:**

- `searchKnn` is a max-style priority queue: `top()` is the farthest retained
  result. Use `searchKnnCloserFirst` or drain into a vector from the back.
- `searchKnnCloserFirst` is still a vector of `(distance, external label)`;
  lower distance is closer for L2 and inner-product distance.
- Set `ef` before querying and normally keep it at least `k`. Higher `ef` can
  improve recall but costs query time. Loading resets `ef` to 10.
- A filter or deletion can legitimately leave fewer than `k` candidates. Check
  `.empty()`/`.size()` before reading a result and validate that enough labels
  are eligible.
- `BruteforceSearch` asserts `k <=` its total element count even if a filter
  will later reduce the output. Use a valid baseline `k`.
- Do not interpret one tiny smoke run as a recall benchmark; graph quality and
  parameter tuning require a representative workload.

## Capacity and memory

**Symptoms:** insertion reports that the element limit is exceeded, replacement
does not add a point, or allocation fails.

**Checks and fixes:**

- `max_elements` is capacity, not a hint. Count unique labels and account for
  updates, deleted slots, and future replacement labels.
- Call `resizeIndex(new_max_elements)` before insertion only after quiescing
  readers/writers, and never set it below the current count.
- A save/load cycle can load into a larger capacity. Pass the larger capacity to
  the load constructor or resize a quiescent object.
- Replacement only reuses slots marked deleted and only when the index policy
  enabled it. It does not guarantee growth if no deleted slot exists.
- Reduce `M`, capacity, dimension, or worker count only as an intentional memory
  trade-off; do not hide an allocation failure by changing data layout.

## Space and object lifetime

**Symptoms:** crashes after a scope ends, nonsensical distances, corrupted
queries, or failures only after loading.

**Checks and fixes:**

- Declare the metric space before the index and destroy the index first. The
  index retains the space's distance-function parameter pointer.
- Match dimension and data bytes exactly: built-in spaces expect `dim` floats;
  multivector spaces append a document id to each stored record while the query
  remains the vector portion.
- Keep input/query storage valid during `addPoint`/search and do not mutate a
  shared buffer while another worker reads it.
- Keep filters and stop conditions alive and stable for the entire search call.
- For custom spaces, verify `get_data_size`, `get_dist_func`, and
  `get_dist_func_param` are internally consistent.

## Persistence and load failures

**Symptoms:** `Cannot open file`, “corrupted or unsupported”, wrong distances,
missing replacement behavior, or unexpectedly low recall after load.

**Checks and fixes:**

- Create the parent directory and pass a writable output filename to
  `saveIndex`; check exceptions and file existence before load.
- Load with a compatible `SpaceInterface` and dimension. The file is binary and
  is not a generic serialization of arbitrary vectors.
- The load form's `allow_replace_deleted` argument controls whether deleted
  slots are tracked for future replacement. Match the intended policy before
  calling `addPoint(..., true)`.
- Set `ef` after load because it is not persisted and the implementation resets
  it to 10.
- Keep the load space alive. Do not reuse a destroyed or temporary metric space.
- If a file was interrupted during save or comes from an incompatible header
  layout, regenerate it rather than bypassing validation.

## Deletion and replacement policy

**Symptoms:** `markDelete` says a label is missing/already deleted; replacement
throws that it is disabled; an undelete races with a new label.

**Checks and fixes:**

- `markDelete` requires an existing, currently non-deleted external label.
- `unmarkDelete` requires an existing, currently deleted label and is not safe
  as a general operation when replacement is enabled.
- Enable replacement in the constructor or load form before any replacement
  call. The call must be `addPoint(data, new_label, true)`.
- Do not confuse a regular repeated-label update with replacement of a deleted
  slot. Allocate replacement labels explicitly and coordinate each slot.
- Query after each lifecycle phase and assert the old label is omitted and the
  new label can be found; do not read a result without checking its size.

## Filters, epsilon, and multivector cases

**Symptoms:** filtered results contain unexpected ids, epsilon returns an empty
or oversized set, or documents are counted as vectors.

**Checks and fixes:**

- Filter functors receive external labels. If labels are offset or sparse,
  test the predicate against those labels rather than internal insertion order.
- A filter can yield fewer than `k`, including zero. The filter object must not
  be destroyed or mutated during the call.
- Epsilon thresholds use the metric's distance units; L2 is squared distance.
  Keep `min_num_candidates <= max_num_candidates` and use the exact stop
  constructor/signature.
- Multivector stored bytes are vector data followed by the document id. Set the
  id through the space helper and pass only vector bytes as the query. Use the
  multivector stop condition if the requested count is documents, not vectors.
- These optional paths are C++-only in the scoped 0.9.0 evidence. Do not route
  them through Python `Index` assumptions.

## Stress and benchmark exclusions

**Symptoms:** a smoke gate times out, runs out of memory, or is treated as a
performance/recall claim.

**Checks and fixes:**

- Keep the default check small and deterministic: compile, add, search, filter,
  save, reload, and assert invariants.
- Exclude long-running stress tests, large external datasets, and throughput
  comparisons from the smoke wrapper. Run them separately with a declared
  timeout, memory budget, dataset, thread count, and CPU target.
- A passing small program proves API usability, not high recall, native SIMD
  safety, allocator scalability, or mixed-operation race freedom.
