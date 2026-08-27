# Persistence and evaluation troubleshooting

## The file or byte payload cannot be read

**Symptoms:** `read_index`/`deserialize_index` raises `RuntimeError`, reports a
short read, or fails after a process restart.

1. Check that the writer completed and the path is the intended file, not a
   temporary name or a text-mode copy.
2. Compare file size/byte-array length with the recorded manifest and compute a
   hash before reading. A truncated index is not recoverable by retrying the
   read.
3. Test the original index in the same process, then round-trip a tiny
   `IndexFlat`; this separates a bad artifact from an environment problem.
4. Do not ignore an exception just because the object was returned; search it
   and compare IDs/distances to a known baseline.

Use a same-directory temporary file and `os.replace` only after a successful
write. Never overwrite the only known-good artifact in place. A Faiss index
serialized by one incompatible build may not be a portable long-term format;
record Faiss version, CPU/GPU build, metric, dimension, and factory/configuration.

## Untrusted or unexpectedly large input

Faiss deserialization allocates according to fields in the payload. A file can
be syntactically shaped to consume excessive memory or CPU; IO flags and mmap
are not sanitizers. Before reading an external file:

- accept only a regular file or an explicitly bounded byte buffer;
- enforce an application byte limit and, where supported, set
  `set_deserialization_loop_limit`, `set_deserialization_vector_byte_limit`,
  and `set_deserialization_lattice_r2_limit` before concurrent reads;
- use a low-privilege worker with a wall-clock and address-space limit for
  hostile input;
- keep global guard setters out of a shared process unless their startup and
  thread-safety implications are understood;
- reject unexpected index type, dimension, metric, and `ntotal` after reading.

Never run arbitrary pickles or accept an index file from an untrusted source as
if it were a data-only format. If the source is not trusted, validate it in an
isolated process and copy only an approved result.

## mmap or OnDisk search fails after relocation

**Symptoms:** missing external file, mapping error, I/O error during search, or
an index that worked before cleanup no longer works.

- `IO_FLAG_MMAP` and `IO_FLAG_MMAP_IFC` support only subsets of index types.
  Retry without mmap for a small diagnostic artifact; do not silently make
  that the production policy if memory was the reason for mmap.
- An OnDisk IVF index has two artifacts: the index metadata and the external
  `ivfdata` mapping. Keep the exact path relationship expected by the writer,
  or read with `IO_FLAG_ONDISK_SAME_DIR` when both are intentionally colocated.
- Do not rename, truncate, rewrite, or delete the mapped `ivfdata` while an
  index or child object still references it. Delete the Python index and force
  collection before cleanup on platforms that hold file handles.
- `IO_FLAG_READ_ONLY` prevents mutation only for implementations that honor it;
  treat a read-only mapping as immutable and use a regular loaded copy for
  writes.
- OnDisk additions and resizes are slow. For bulk ingestion, create ordinary
  shard indexes and merge into a new OnDisk file; do not use a live OnDisk file
  as a temporary scratch database.

## Byte round trip differs from file round trip

Check that both paths use the same index, flags, and complete data. Compare
`d`, `metric_type`, `ntotal`, `is_trained`, `nprobe`/graph search settings,
result IDs, and distances. Some settings are mutable runtime state and some
precomputed tables may be intentionally skipped by an IO flag. Re-search the
same `float32` contiguous query array after each read. If a file is read with
an external OnDisk list, test the list file as well; bytes for the top-level
index do not necessarily embed a separately managed mapping.

`clone_index` is not a substitute for persistence testing. Clone and IO paths
can exercise different ownership and storage implementations. For an mmap or
optional index, verify clone parity explicitly and retain backing-file
references until all searches finish.

## Metric, shape, or ID mismatch produces misleading recall

A recall number is invalid if the exact and candidate indexes disagree on any
of:

- `d` or query/database row shape;
- L2 versus inner product;
- cosine normalization (all vectors must be normalized for cosine-IP);
- database row order and label offset after sharding;
- `k`, filtering/selector policy, or duplicate/missing IDs;
- transformed vectors (PCA/OPQ/PreTransform) used for training versus search.

Make the mismatch fail before search. Check `x.ndim == 2`, `x.shape[1] ==
index.d`, float32/contiguity, and `int(index.metric_type) == int(metric)`. A
reproducible synthetic test is `IndexFlatL2(d)` versus an expected IP metric,
and the same exact index with `xq[:, :-1]`; both should raise in a contract
checker. If the Faiss wrapper itself raises an assertion or runtime error,
retain the original error rather than converting it to a quality result.

For L2, compare squared distances and use `< radius`; for IP, compare larger
scores and use `> radius`. Do not apply an L2 threshold to IP output.

## IVF recall is zero or unexpectedly low

1. Verify the exact flat baseline independently and inspect the first query's
   vectors, metric, and IDs.
2. Confirm `candidate.is_trained`, `candidate.ntotal`, and that training data
   has the same dimension and preprocessing as added vectors.
3. Increase `nprobe` for a diagnostic; `nprobe >= nlist` should approach exact
   IVF-Flat candidate selection. If it does not, check IDs, metric, and a
   malformed or empty list.
4. Ensure `k <= ntotal` and handle `-1` labels rather than counting them as
   matches.
5. For compressed candidates, separate coarse-list misses from codec error:
   compare IVF-Flat at the same `nprobe` before diagnosing PQ/SQ.
6. Keep the query and database arrays fixed while changing one parameter at a
   time. Set a fixed OpenMP thread count for reproducible tiny checks.

A tiny random dataset is not a stable quality benchmark. Use a representative
local sample and an application-specific gate after the smoke passes.

## Precision/recall range results are wrong

Range results are flattened. Use `lims[q]` and `lims[q+1]`; never compare the
whole `I` arrays row-wise without unpacking. Sort IDs per query before set
comparison if ordering is not part of the contract. Make empty-reference and
empty-result behavior explicit: no returned results with no relevant results
is conventionally perfect for that query, while returned results with no
relevant results have zero recall.

`range_PR` compares IDs and not distances. Filtering candidate distances at a
new threshold changes `lims`; recompute both the flattened arrays and limits.
For several thresholds, keep the reference IDs sorted and candidate rows sorted
by distance before using `range_PR_multiple_thresholds`.

## Kmeans fails, is unstable, or has poor centroids

- Confirm `(n, d)` float32 input, `n >= k`, no NaN/Inf, and a matching
  assignment-index dimension.
- A request for more centroids than distinct or useful samples can produce
  duplicate/degenerate centroids. Reduce `k` or provide more representative
  rows; do not infer production quality from a one-point-per-cluster smoke.
- Fix `seed`, `niter`, `nredo`, thread count, and sample order when comparing
  runs. `nredo` can improve objective while increasing cost.
- Inspect `km.obj`, `iteration_stats`, centroid occupancy, and assignment
  distortion. For cosine, normalize data and use inner product/spherical
  settings consistently.
- `faiss.contrib.clustering` sparse helpers may need SciPy; core `Kmeans`
  should be tested separately from that optional path.

## Reconstruction or codes do not match original vectors

This is expected for lossy codecs. Check `codes.dtype == np.uint8`, code shape,
`sa_code_size()`, and the codec's trained state. Use the same trained codec for
`sa_encode` and `sa_decode`; do not decode codes with a different codebook.
Report reconstruction error separately from search recall. `IndexFlat` and
uncompressed IVF-Flat can reconstruct stored vectors, while PQ/SQ/residual
families generally reconstruct approximations. ID-mapped/composite indexes may
not support every reconstruction method; route ownership and IDs to the
composition branch.

## Merge or OnDisk merge fails

Compatible merge requires matching trained structure, dimension, metric,
coarse quantizer/codebook, code size, and compatible IDs. Start with two tiny
shards made from one cloned trained index. Validate shard row ranges and use
`add_id`/`shift_ids` deliberately; never guess offsets when explicit IDs are
already present. An output target must be empty for the on-disk merge workflow.

For `merge_ondisk`, confirm every shard exists, is readable with mmap, has
compatible inverted lists, and that the target `ivfdata` path is new or
explicitly disposable. If a merge fails, discard the partial output and rerun
from immutable shards; do not append to a partly merged file. Keep source
indexes alive until the merge operation completes, then verify final `ntotal`,
search results, and the external file manifest.

## Auto-tuning is too slow or results are not reproducible

`ParameterSpace.explore` may enumerate many combinations and measure noisy
wall-clock time. Inspect and cap `n_experiments`, reduce `nq`, use a fixed
OpenMP thread count, warm up each candidate, and impose a process-level timeout.
Use a manual explicit parameter list for a smoke. Record hardware/build, query
count, metric, criterion, parameter string, elapsed time, and recall. Keep
Pareto operating points; a faster point with lower recall is not a regression
unless the application gate says so. GPU timing and GPU ground truth require a
separately verified backend and belong to the accelerated branch.

## Temporary files remain after a failed run

Use `tempfile.TemporaryDirectory` or `NamedTemporaryFile(delete=False)` plus a
`finally` cleanup. Close file handles before `read_index`/mmap where the
platform requires it. Never use a fixed shared absolute filename, never place
scratch artifacts in the repository checkout, and never delete a path supplied
by a caller without checking it is the intended temporary path. For an OnDisk
workflow, clean the metadata index, external `ivfdata`, and any manifest as a
single set only after all mapped objects are released.
