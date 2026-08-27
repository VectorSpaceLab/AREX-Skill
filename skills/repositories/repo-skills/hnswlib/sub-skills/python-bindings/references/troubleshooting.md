# Python bindings troubleshooting

Diagnose in this order: import, native build, input contract, index lifecycle,
query cardinality/quality, persistence, then concurrency. Keep the original
exception text and the space/dimension/capacity/label state in the report.

## Installation and import

**`ModuleNotFoundError: hnswlib`**

- Confirm that the intended Python interpreter is the one running the client.
- Install the package into that environment or expose the already-built native
  extension through the environment's normal package mechanism.
- Check that NumPy is available. NumPy is the runtime dependency used for the
  array bridge and result arrays.
- Do not “fix” an import by adding a source checkout to `sys.path` in a
  production integration; verify the package installation instead.

**`ImportError`/`undefined symbol`/native loader failure**

- The extension is a compiled CPU-native module, not a pure Python fallback.
- Inspect the loader's missing shared library and rebuild/install for the
  active Python ABI and platform.
- A CUDA toolkit, GPU driver, or CUDA-enabled package is not an alternative:
  this public binding exposes no CUDA API.

## Source-build prerequisites

The package metadata requires NumPy at runtime. A source build additionally
uses setuptools/wheel, pybind11 headers, a C++ compiler with C++11 or newer,
and the platform's native thread/runtime support. The observed build config
uses NumPy and pybind11 include directories and compiles `python_bindings` as
an extension named `hnswlib`.

On Unix-like builds, the normal flags include optimization, `-std=c++14` when
available (otherwise C++11), `-march=native` when supported, `-fopenmp`,
`-pthread`, and visibility options when supported. On Windows, the native
configuration uses MSVC exception, OpenMP, and optimization flags. macOS uses
libc++ and does not append the non-macOS OpenMP flags in this setup.

Distinguish absent from optional dependencies:

- NumPy is required at runtime and supplies headers during a source build.
- pybind11 is a build-time header dependency; a successful installed import
  does not require importing `pybind11` in the application.
- A C++ compiler and the flags selected by the build are required to compile
  from source. OpenMP/thread runtime support must match the generated native
  module on platforms where the build links it; it is not a Python-level
  feature that can be replaced by installing a CUDA package.
- `-march=native` is optional portability tuning. Set `HNSWLIB_NO_NATIVE` when
  the compiler or deployment CPU cannot use it; this does not remove the need
  for a compatible compiler or the platform's selected thread/OpenMP linkage.

**Compiler errors around `-std`, `-fopenmp`, `-pthread`, or `-march=native`**

Check each flag with the compiler, then use a compatible toolchain. If only
`-march=native` fails, use `HNSWLIB_NO_NATIVE`. If OpenMP or pthread linkage is
absent, resolve the platform compiler/runtime installation rather than treating
an incomplete binary as an optional dependency. Keep compiler and runtime
architectures consistent.

## Shape, dtype, and label failures

**`Input vector data wrong shape`**

Pass only `(dim,)` or `(rows, dim)`. A 1-D vector is one row. Do not pass a
ragged list, scalar data, or rank-three tensor.

**`Wrong dimensionality of the vectors`**

The insertion trailing dimension is not the constructor `dim`. Convert and
check with `np.asarray(data, dtype=np.float32)` and `data.shape[-1] == index.dim`
before insertion. Apply the same check to queries even though the observed
query binding does not explicitly raise for this condition.

**`input label shape ... does not match ...`**

Use one 1-D integer label per row. A scalar label is valid only for one vector.
Do not pass a `(rows, 1)` matrix, a label array with a different length, or
negative labels. Ensure IDs are unique for new items; repeat an existing ID
only when an update is intentional.

**Unexpected labels after omitted IDs**

Omitted IDs use the binding's internal sequential counter and are not an
external metadata mapping. Pass explicit stable IDs and maintain any object
metadata in the application.

## Space and distance errors

**`Space name must be one of l2, ip, or cosine.`**

Use exactly one supported lower-case name. Other metrics are not exposed by
this Python extension.

For `l2`, distances are squared L2, not Euclidean norm. For `ip`, values are
`1 - dot` and can be negative. For `cosine`, the extension normalizes both
stored and query vectors and `get_items` returns normalized vectors. Validate
finite data and prefer non-zero vectors for meaningful cosine direction.

**Distance expectations disagree**

Check the metric formula, float32 tolerance, query order, and whether the
cosine reference normalized both operands. Compare exact labels/distances with
BFIndex using identical IDs and data. Do not compare approximate HNSW ordering
to a brute-force ranking as exact when distances tie.

## Query, `ef`, and filters

**`Cannot return the results in a contiguous 2D array`** or BFIndex's
“not enough elements” error

The binding cannot produce `k` results for at least one query. Check all of:

1. `k <=` live element count;
2. every Python filter admits at least `k` live labels;
3. deleted labels are not the only candidates;
4. `ef >= k`; and
5. the graph was built with enough quality for the requested query.

A filter is applied to external labels and does not pad missing rows. Reduce
`k` or widen/populate the eligible set. Filtered Python queries should use
`num_threads=1`.

**Low recall or unstable approximate ranking**

Raise `ef` first, keeping `ef >= k`. Then revisit `M` and
`ef_construction` for the data's intrinsic dimension and target recall. Build a
same-space BFIndex oracle and measure label overlap. A tiny self-query only
checks wiring and is not a production recall claim.

## Capacity, updates, deletion, and replacement

**Capacity/full-index exception**

`max_elements` is a hard initial capacity for new slots. Updating an existing
label does not require a new slot, but a new label does. Call `resize_index`
in a quiescent phase, or save/load with a larger `max_elements`. Do not shrink
below the current element count. Deletions do not by themselves make ordinary
insertion unlimited.

**Replacement disabled or no reusable slot**

`replace_deleted=True` requires `allow_replace_deleted=True` at `init_index`
or `load_index`, a deleted slot, and a new insertion that fits the lifecycle.
If a deleted index was reloaded with the default false flag, replacement is
supposed to fail; reload it with `allow_replace_deleted=True` if reuse is
intended. Mark a live existing label before replacement. Do not mark the same
label twice. Avoid colliding with a live replacement label.

**Deleted items still appear or cannot be restored**

Call `mark_deleted` with the external label actually stored, not a row offset
from an unrelated array. It excludes the label from normal query results but
does not erase graph storage. `unmark_deleted` requires that the label is
currently marked and is unsafe as a general recovery mechanism after its slot
has been reused. Verify state with explicit IDs and a valid `k`.

## Persistence and pickle

**Load fails, returns an incompatible result, or cannot open a file**

Use a temporary/application-owned path that exists and is writable/readable.
The file is a native binary artifact: do not edit it or move it across
incompatible builds without a compatibility policy. Construct the wrapper with
the saved `space` and `dim`; use a larger `max_elements` only when growth is
needed. Preserve `allow_replace_deleted=True` on load for replacement state.

After `load_index`, set `index.ef` or call `set_ef` again: file persistence does
not save this query parameter and observed loads reset it to 10. File loading
also should occur in an exclusive lifecycle phase.

**Pickle round trip fails or loses expected behavior**

Use `pickle.dumps`/`pickle.loads` on `Index`, not BFIndex as if it had the same
pickle contract. Check explicit vectors, IDs, deletion state, and `ef` after a
round trip. Pickle state extraction/get-index-state is not thread-safe with
`add_items`; protect it with an application lock. Treat pickle bytes as
version/build-sensitive, not a durable interchange format.

## Concurrency and native safety

- `add_items` may run concurrently with other `add_items` calls, but not with
  `knn_query`.
- `knn_query` may run concurrently with other `knn_query` calls, but not with
  `add_items`.
- `resize_index` is not thread-safe with adding or querying.
- Python filters are slow in multi-threaded mode and should normally use one
  native thread; synchronize any state captured by the callback.
- Pickle/getIndexParams is not concurrent-safe with `add_items`.

If a crash or intermittent corruption remains, reduce the workload to one
thread, isolate structural/persistence operations, validate every buffer shape,
and reproduce with one of the deterministic smoke scripts before changing
algorithm parameters.
