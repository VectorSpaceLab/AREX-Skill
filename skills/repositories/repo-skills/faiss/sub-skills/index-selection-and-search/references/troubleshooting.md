# Index and search troubleshooting

## Input and shape failures

- **Assertion or dimension error:** inspect `x.ndim`, `x.shape`, `index.d`,
  and `x.dtype`. Every add, train, and query matrix must be 2-D with exactly
  `d` columns. Convert explicitly with
  `np.ascontiguousarray(x, dtype="float32")`; do not pass a 1-D row, ragged
  list, object array, or transposed `(d, n)` matrix.
- **Unexpected copies or slow calls:** check `x.flags["C_CONTIGUOUS"]` and
  `x.dtype`. A view, Fortran-order matrix, or float64 input may be copied by
  the wrapper. Normalize a contiguous float32 matrix because `normalize_L2`
  mutates its argument and is not a replacement for input validation.
- **Invalid `k`:** `k` must be positive. A request larger than `ntotal` is
  valid, but inspect `I == -1` and the corresponding worst-distance sentinels
  rather than treating padded rows as neighbors.
- **NaN or Inf data:** reject or repair non-finite values before training,
  adding, and searching. They can corrupt centroid assignment or graph
  ordering and make recall/ordering diagnostics meaningless.

## Metric and cosine failures

- **Cosine recall is unexpectedly poor:** verify that both `xb` and `xq` were
  normalized, after conversion to float32 and before `add`/`search`, and that
  the index uses `METRIC_INNER_PRODUCT`. Normalizing only queries (or only the
  database) leaves vector norms in the score and can actively harm results.
  Compare `faiss.pairwise_distances` or a normalized `IndexFlatIP` baseline.
- **Results appear reversed:** L2 is lower-is-better; IP is higher-is-better.
  Range thresholds follow the same direction: L2 returns values below the
  radius, IP returns scores above it. Do not sort IP distances ascending.
- **Self-neighbor is not first:** confirm query and database preprocessing are
  identical, the query is actually present, and the metric is correct. For
  approximate indexes, inspect recall against Flat rather than assuming a graph
  or IVF result is exact.
- **Unexpected ties:** duplicate vectors and finite-precision ties can make
  equal-score label order non-meaningful. Validate overlap/score correctness,
  not a particular tie ordering.

## Training and factory failures

- **`is_trained` is false or add fails for IVF:** call `train(xtrain)` first and
  confirm it returns with `index.is_trained` true. Training learns the coarse
  quantizer; it does not add `xb`. Use representative data with the same
  dimension, metric, normalization, and scale as the database.
- **Training warnings or poor IVF recall:** increase or improve the
  representative training sample, check that `nlist` is plausible for the
  sample/corpus, and measure recall while sweeping `nprobe`. Do not suppress a
  warning by blindly increasing `nprobe`; a poorly trained quantizer can remain
  poor at every search budget.
- **Factory string rejected:** confirm the description and metric are supported
  by the installed Faiss version, then inspect the resulting concrete class and
  `is_trained`. Keep codec, transform, refinement, and ID syntax on their
  sibling routes. Do not silently fall back from an intended approximate index
  to Flat.
- **64D factory exceeds RAM:** `IVF256,Flat` still stores 256 bytes of raw
  vector payload per item, plus overhead. Lowering `nprobe` changes query work,
  not payload memory. Use the compression route for a storage reduction.

## Approximate-search failures

- **IVF recall too low:** record `nlist`, `nprobe`, corpus/training sizes, and
  preprocessing. Start from a Flat baseline, sweep `nprobe` while keeping all
  else fixed, and test `nprobe=nlist` diagnostically. If the exhaustive IVF
  setting still differs materially from Flat, inspect training and metric
  consistency.
- **IVF is too slow:** lower `nprobe`, batch queries, and check that thread
  count and BLAS are not oversubscribed. Validate the recall loss before
  shipping. `parallel_mode` is advanced; change it only with a benchmark.
- **HNSW recall too low:** ensure `efSearch >= k`, then increase `efSearch` and
  measure. If the curve saturates below target, rebuild with a more suitable
  `M`/`efConstruction` and confirm the graph was built after those settings
  were applied. `efSearch` is a search budget, not a repair for missing or
  incorrectly preprocessed data.
- **HNSW build is too slow or memory-heavy:** lower `M` or `efConstruction`
  only after measuring recall, reduce OpenMP oversubscription, and consider
  IVF or compression for the target scale. Do not infer HNSW memory from Flat
  payload alone; graph links add overhead.
- **NSG/NN-Descent behavior differs from HNSW:** these are distinct graph
  implementations. Check their concrete constructor/factory support and use
  their own measured build/search settings; do not apply `efSearch` unless the
  concrete API exposes it.
- **Range search misses expected approximate neighbors:** Flat is the exact
  reference. IVF may not visit the list containing a neighbor when `nprobe` is
  small; HNSW graph traversal is approximate. Increase the relevant search
  budget and compare ragged slices using `lims`; do not reshape the result.
- **Range search returns no data:** verify radius direction and scale, inspect
  `lims[-1]`, and remember that an empty result is represented by valid `lims`
  with empty flat `D`/`I` arrays. L2 uses squared distances.

## Thread and runtime failures

- **Non-reproducible latency or CPU saturation:** `omp_set_num_threads` is
  process-global. Save and restore the prior count, coordinate it with worker
  pools and threaded BLAS, and use a fixed count in comparisons.
- **Tests affect later tests:** restore OpenMP count in `finally`; do not leave a
  temporary `nprobe`, `efSearch`, or metric preprocessing object shared across
  cases.
- **Import or GPU-only class failure:** this generated scope is verified with
  `faiss-cpu 1.15.0`. CUDA hardware may exist, but no CUDA Faiss package was
  prepared here. GPU, cuVS, ROCm, Metal, and SVS claims are conditional and
  unverified; route those requests to
  [accelerated-and-interoperable](../../accelerated-and-interoperable/SKILL.md).

## Validation checklist

Before blaming an index algorithm, run the bundled smoke helper and a controlled
comparison:

1. Check finite contiguous float32 `(n, d)` arrays.
2. Check metric and normalization on both database and queries.
3. Check lifecycle and `ntotal`/`is_trained`.
4. Check `(nq, k)` result shapes, `-1` sentinels, and ragged `lims` slices.
5. Compare approximate labels and latency to the same-metric exact Flat index.
6. Record `nprobe` or `efSearch`, thread count, and build settings.
