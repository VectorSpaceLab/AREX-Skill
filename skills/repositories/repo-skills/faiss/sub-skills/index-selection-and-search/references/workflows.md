# Selection, construction, and tuning workflows

## Choose an index from the target

Start with an exact baseline. It gives a trustworthy recall target and catches
metric, normalization, shape, and data-quality errors before approximation is
introduced.

| Need | First choice | Why / trade-off |
| --- | --- | --- |
| Small or moderate corpus, strict exactness, simple debugging | `IndexFlatL2` or `IndexFlatIP` | No training and exact results, but scans every stored vector per query. |
| Large CPU corpus, full-precision vectors, controllable speed/recall | `IndexIVFFlat` | Coarse partitioning reduces scanned vectors; requires representative training and `nprobe` tuning. |
| Low-latency approximate search with full vectors and graph memory available | `IndexHNSWFlat` | No coarse training; graph build can be expensive and graph links add memory. Tune `efConstruction` before add and `efSearch` at query time. |
| Graph alternatives worth benchmarking | `IndexNSGFlat`, `IndexNNDescentFlat` | Available CPU graph families with different construction/search behavior. Do not copy HNSW parameters or completeness assumptions without testing. |
| Memory itself is the limiting resource | Route to `training-and-compression` | Codec choices change the storage/accuracy contract and are deliberately outside this route. |

The correct choice depends on corpus size, dimensionality, update pattern,
latency SLO, recall target, and available RAM. Search speed is not a substitute
for a measured recall/latency curve.

## Common lifecycle

```python
import faiss
import numpy as np

# Validate at the boundary; retain this contract throughout the pipeline.
xb = np.ascontiguousarray(xb, dtype="float32")
xq = np.ascontiguousarray(xq, dtype="float32")
assert xb.ndim == xq.ndim == 2 and xb.shape[1] == xq.shape[1]
d = xb.shape[1]

# For cosine, mutate copies and normalize both sides before construction/search.
# faiss.normalize_L2(xb)
# faiss.normalize_L2(xq)

index = faiss.IndexFlatL2(d)  # exact baseline
assert index.is_trained
index.add(xb)
D, I = index.search(xq, k)
assert D.shape == I.shape == (xq.shape[0], k)
```

For IVF, split a representative training matrix from the database or use a
representative sample; it must be `(ntrain, d)`, float32, and match the metric
and preprocessing used for add/search:

```python
quantizer = faiss.IndexFlatL2(d)
index = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_L2)
assert not index.is_trained
index.train(xtrain)
assert index.is_trained
index.add(xb)
index.nprobe = min(chosen_nprobe, index.nlist)
D, I = index.search(xq, k)
```

Training does not populate the database. Calling `add` before successful IVF
training is a lifecycle error. Keep the quantizer alive while constructing the
index; the Python Faiss wrapper retains the needed reference, but keeping an
application reference can make ownership intent clearer.

For HNSW, configure build parameters before adding vectors:

```python
index = faiss.IndexHNSWFlat(d, 32, faiss.METRIC_L2)
index.hnsw.efConstruction = 40
index.add(xb)
index.hnsw.efSearch = max(64, k)
D, I = index.search(xq, k)
```

`M` is a graph connectivity choice and `efConstruction`/`efSearch` are
candidate-expansion budgets. Larger values generally trade CPU time (and graph
construction cost) for recall; confirm that relationship on the actual data.

## 64D memory-conscious factory decision

For a 64-dimensional CPU workload that must retain full-precision vectors but
should avoid an exhaustive scan, start with:

```python
index = faiss.index_factory(
    64, "IVF256,Flat", faiss.METRIC_L2
)
```

`Flat` here means full float32 storage: the vector payload alone is 64 * 4 =
256 bytes per vector, plus list/centroid/index overhead. This is
memory-conscious relative to a more elaborate or exhaustive search plan because
it limits search to selected lists while preserving exact stored vectors; it is
not compressed storage. If the 256-byte payload is too large for RAM, route to
[training-and-compression](../../training-and-compression/SKILL.md) rather than
pretending `nprobe` reduces memory.

A disciplined setup is:

1. Estimate corpus size and select `nlist=256` as a starting point, not a
   universal optimum. Ensure training data are representative and sufficient
   for that coarse partition count; use the package's training warnings as a
   signal to increase or revise the sample.
2. Train once on `xtrain` after applying the same float32 conversion,
   normalization (if cosine/IP), and filtering used for `xb`.
3. Add the database only after `index.is_trained` is true.
4. Sweep `nprobe` from a small value such as `1`, `4`, `16`, and higher values
   appropriate to the latency budget. More probes visit more lists and usually
   improve recall while increasing query work; `nprobe=nlist` approaches an
   exhaustive IVF scan and is a useful diagnostic, not a speed target.
5. Compare each candidate's labels with an exact Flat index using the same
   queries, metric, and `k`; report recall@k and latency, not only a single
   result. Keep a Flat reference for a small validation slice.
6. If recall is poor even at high `nprobe`, investigate training coverage,
   preprocessing, dimensionality, duplicates, and query/data distribution
   before increasing `nlist`.

For cosine, construct the factory with `METRIC_INNER_PRODUCT` and normalize
both matrices before training/add/search:

```python
faiss.normalize_L2(xtrain)
faiss.normalize_L2(xb)
faiss.normalize_L2(xq)
index = faiss.index_factory(64, "IVF256,Flat", faiss.METRIC_INNER_PRODUCT)
```

Do not reuse normalized arrays as if they retained their original magnitudes.

## Recall/speed tuning loop

1. Fix a deterministic validation subset and one exact baseline.
2. Fix `k`, batch sizes, metric, normalization, and thread count.
3. Measure Flat first; assert result shapes and self-neighbor behavior where
   applicable.
4. Build the approximate candidate once, then sweep only one search knob at a
   time. For IVF sweep `nprobe`; for HNSW sweep `efSearch` with
   `efSearch >= k`.
5. Compute recall@k as the fraction of approximate top-k labels that overlap
   exact top-k labels (define tie handling consistently). Record p50/p95
   latency and memory separately.
6. Select the lowest-work setting meeting the recall SLO. Revalidate after
   changing the corpus, training sample, metric preprocessing, compiler/build,
   or thread count.

For graph indices, increasing `efSearch` cannot repair a graph built with a
poor `M`/`efConstruction` choice in every workload. Rebuild and compare when
build-time choices are suspect. NSG and NN-Descent should have their own
parameter experiments; this route does not assert HNSW controls for them.

## kNN, assign, and range search

Use top-k when every query needs a bounded number of neighbors:

```python
D, I = index.search(xq, k)
I_only = index.assign(xq, k)
```

Use range search when the threshold, not a fixed `k`, defines the result set:

```python
lims, D, I = index.range_search(xq, radius)
for q in range(xq.shape[0]):
    Dq = D[lims[q] : lims[q + 1]]
    Iq = I[lims[q] : lims[q + 1]]
```

Choose L2 radii as squared-distance thresholds and IP radii as similarity
thresholds. Range output is ragged; do not reshape `D` or `I` to `(nq, k)`.
For approximate indexes, use Flat range search to estimate missed neighbors if
completeness matters. Some index families only guarantee `search`, so check the
concrete class before selecting range search as a required API.

## Thread-safe smoke operation

```python
previous = faiss.omp_get_max_threads()
try:
    faiss.omp_set_num_threads(1)
    D, I = index.search(xq, k)
finally:
    faiss.omp_set_num_threads(previous)
```

Use a bounded thread count in CI and small tests. In a service, coordinate this
process-global setting with the service's worker pool and BLAS configuration to
avoid oversubscription. The bundled smoke helper sets a requested count only
for its process and restores it before exit.
