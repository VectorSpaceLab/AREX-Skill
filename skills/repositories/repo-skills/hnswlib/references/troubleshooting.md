# Cross-cutting troubleshooting

## Import and build

- **`ModuleNotFoundError: hnswlib`**: install the public distribution into the
  same Python that will run the workload, then verify with `python -I`. For a
  source checkout, install from the package root rather than adding the
  checkout to `PYTHONPATH`.
- **Missing NumPy or pybind11 during build**: install the scoped build
  requirements in the active isolated environment and retry. Do not install
  unrelated extras or benchmark dependencies.
- **C++ standard/flag/compiler errors**: use a C++11-capable compiler. If
  `-march=native` is not accepted or the binary must be portable, set
  `HNSWLIB_NO_NATIVE=1`; if OpenMP or pthread link errors remain, use the
  platform's supported thread flags. Inspect the first compiler error rather
  than hiding it behind a retry.
- **Import succeeds in the checkout but fails elsewhere**: the current
  directory or an old extension may be shadowing the installed package. Run
  the isolated `python -I` import check from a neutral directory and inspect
  the package metadata without publishing local installation paths.
- **ABI/architecture failure**: rebuild for the target Python, compiler ABI,
  operating system, and CPU. A native-optimized artifact built on one CPU may
  not run on an older deployment CPU; disable native flags for a portable build.

## Data and API validation

- **Wrong dimension or shape**: normalize input to contiguous numeric arrays,
  accept only `(dim,)` or `(rows, dim)`, and check the final dimension before
  `add_items` and `knn_query`. Supply one label per row, or one scalar label only
  for a one-vector input. The insertion path has an explicit dimension guard;
  validate queries in application code too.
- **Invalid space**: use exactly `l2`, `ip`, or `cosine`. Use the same space and
  dimension for an HNSW/BFIndex comparison and for a compatible file reload.
- **Unexpected distances**: `l2` is squared L2, `ip` is `1 - dot`, and cosine
  uses normalized vectors. Do not compare cosine `get_items` output with raw
  unnormalized input.
- **Unexpected labels or retrieval**: labels are external integer identifiers.
  Use explicit stable labels for joins and persistence. `get_items` requires an
  explicit iterable of labels; use `get_ids_list()` when all current labels are
  needed. A marked-deleted label can remain in the ID listing even though search
  excludes it.
- **`k`/filter result exception**: HNSW returns rectangular Python arrays and
  cannot fill a row when fewer than `k` eligible items exist. Reduce `k`, widen
  the filter, add live items, or query without the filter. Treat the exception as
  a precondition failure, not as a partial result.
- **Full capacity**: deletion marks a slot but does not increase capacity. Resize
  before insertion, load with a larger capacity, or enable deleted-slot
  replacement and pass its explicit replacement flag.

## Persistence and mutation

- **`ef` appears too low after load**: file persistence resets it to the default
  (10 in this release). Call `set_ef`/`setEf` after every file load.
- **Cannot replace a deleted item**: the index must have been initialized or
  loaded with `allow_replace_deleted=True`, and insertion must pass
  `replace_deleted=True`. The policy is part of the lifecycle; set it before
  filling the index.
- **Deleted item still appears in IDs**: `get_ids_list` describes labels stored
  in the index, while normal search excludes marked-deleted items. Use
  `unmark_deleted` only for a deliberately reversible lifecycle and do not
  unmark a slot that may already have been reused.
- **Save/load failure**: use an application-owned writable path, finish all
  mutations before saving, and reload with a compatible metric/dimension. Ensure
  the destination has enough capacity for planned growth.
- **Pickle failure or inconsistent state**: do not pickle or copy an index while
  `add_items` is running. Pickle is a Python binding feature; C++ clients should
  use the binary index methods and their own lifecycle.

## Concurrency and scope

- Python queries may run with other queries, and additions may run with other
  additions, but do not mix `add_items` and `knn_query`. Resizing, persistence,
  pickle, and destruction require an external phase boundary.
- C++ read/write safety depends on the operation and version. Use an external
  lifecycle lock around mixed search, structural mutation, save/load, resize,
  and destruction. Keep spaces, filters, stop conditions, and backing buffers
  alive for the whole call.
- Do not infer GPU support from visible hardware. This package's selected
  backend is CPU; GPU-specific ANN APIs require another library.

## Deliberately deferred

Large BigANN/SIFT downloads, full-scale speed tests, plot generation, and
multithread stress cases are not default recovery steps. Run them only with a
separately approved dataset, resource budget, and safety plan.
