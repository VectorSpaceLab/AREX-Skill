# Parameters, spaces, and recall

## Distance spaces

`l2` returns squared Euclidean distance. `ip` returns `1 - dot(a, b)` and is a
distance-like ordering rather than a metric. `cosine` uses the inner-product
implementation after normalizing vectors; `get_items` returns normalized stored
vectors for this space. Distances are lower-is-closer in all three spaces.
Keep data and queries at the declared dimension and use the same space when
comparing an HNSW index with `BFIndex`.

## Construction

- `max_elements` is the initial capacity. Size it for the live population or
  use `resize_index`/`resizeIndex` before growth. It is also a memory decision.
- `M` is the maximum graph connectivity parameter. It affects memory and graph
  quality. The implementation caps it at 10,000 and raises
  `ef_construction` to at least `M`; the public guidance commonly starts around
  12--48, but the right value depends on intrinsic dimension and recall needs.
- `ef_construction` controls build time and graph quality. Increasing it usually
  improves quality until gains flatten. When changing `M`, retune
  `ef_construction` rather than assuming the old setting remains appropriate.
- `random_seed` makes construction initialization reproducible, but does not
  turn ANN quality into an exact guarantee.

## Search

- `k` is the number of neighbors requested and must not exceed the live eligible
  population. A filter can reduce eligibility; every query must still have at
  least `k` accepted items for the rectangular Python result.
- `ef` controls the dynamic candidate list during search. It must be at least
  `k`; larger values generally improve recall and increase query work. A loaded
  file resets it to 10, so restore it after `load_index`/C++ load.
- `num_threads` controls batch insertion/query work in Python. Choose it
  explicitly for reproducible resource use. Callable Python filters are slower
  with multiple threads; use one thread for filtered queries.

## Recall tuning recipe

1. Fix a representative, bounded sample of vectors and queries. Validate dtype,
   finite values, dimension, labels, and metric first.
2. Build HNSW and `BFIndex` with identical space, dimension, vectors, and labels.
3. Sweep a small grid of `M` and `ef_construction`, then set a range of query
   `ef` values with `ef >= k`.
4. Compare label overlap per query against the exact BF result. Report recall as
   matched returned labels divided by `k * number_of_queries`; also measure
   latency and memory for the actual deployment workload.
5. Pick the smallest configuration meeting the application's recall/latency
   target. Repeat after data distribution, dimension, or deletion/replacement
   behavior changes.

Recall thresholds in repository tests are workload-specific assertions, not
portable defaults. The tiny bundled smoke checks validate API invariants and
small exact comparisons, not production recall or latency.
