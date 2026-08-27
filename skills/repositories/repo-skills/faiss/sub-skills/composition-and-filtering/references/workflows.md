# Composition workflows

These recipes are intentionally small and CPU-oriented. They show the order of
operations and the checks that make a composed index trustworthy. Replace the
base child only after the [index-selection-and-search](../../index-selection-and-search/SKILL.md)
branch has established its metric, dimension, and search contract.

## 1. External IDs with safe filtering and deletion

Use this when application IDs must survive search and removal.

```python
import numpy as np
import faiss

d = 4
xb = np.asarray([[0, 0, 0, 0], [1, 0, 0, 0],
                 [0, 1, 0, 0], [0, 0, 1, 0]], dtype="float32")
ids = np.asarray([100, 110, 120, 130], dtype="int64")
index = faiss.IndexIDMap2(faiss.IndexFlatL2(d))
index.add_with_ids(xb, ids)

# The selector names external IDs because it is received by the ID map.
sel = faiss.IDSelectorBatch(np.asarray([110, 130], dtype="int64"))
D, I = index.search(xb[:1], 4, params=faiss.SearchParameters(sel=sel))
assert set(I[0]) <= {110, 130, -1}

removed = index.remove_ids(np.asarray([110], dtype="int64"))
assert removed == 1
try:
    index.reconstruct(110)
except RuntimeError:
    pass
```

Checks:

- IDs are contiguous `int64` input and are unique in the logical corpus.
- The filtered result contains no out-of-set label.
- Deletion count and `ntotal` change are recorded.
- `IndexIDMap2.reconstruct(external_id)` is used only when the child supports
  reconstruction. For a lossy or non-reconstructable child, use search or a
  separate exact store rather than assuming the wrapper changes that fact.

## 2. Transformed refinement with nested parameters

Use this when a transform defines the search space and a fast candidate index
needs exact reranking. Train and add through the outermost wrapper so both
children receive the same transformed rows.

```python
import faiss

base = faiss.IndexIVFFlat(faiss.IndexFlatL2(d), d, nlist)
refined = faiss.IndexRefineFlat(base)
composed = faiss.IndexPreTransform(faiss.NormalizationTransform(d), refined)
composed.train(xt)
composed.add(xb)

inner = faiss.IndexRefineSearchParameters(
    k_factor=2.0,
    base_index_params=faiss.SearchParametersIVF(nprobe=4),
)
params = faiss.SearchParametersPreTransform(index_params=inner)
D, I = composed.search(xq, k, params=params)
```

The outer transform changes the vectors seen by both the IVF base and the
exact refinement child. `k_factor >= 1` asks the base for a larger candidate
set; it cannot recover a neighbor never selected by the base. The base and
refine children must agree on row order and metric. `IndexRefineFlat(base)`
must be constructed before the base receives data; otherwise its constructor
rejects a nonempty base.

If the base is already trained, still call `train` on the outer wrapper only
when its `is_trained` state requires it. Confirm `ntotal` is equal across
`refined.base_index` and `refined.refine_index` after `add`.

## 3. Filter an IVF search with a per-call budget

```python
ivf = faiss.index_factory(d, "IVF16,Flat")
ivf.train(xt)
ivf.add_with_ids(xb, ids)

keep = faiss.IDSelectorRange(100, 140)
p = faiss.SearchParametersIVF(
    nprobe=4,
    max_codes=1000,
    ensure_topk_full=True,
    sel=keep,
)
D, I = ivf.search(xq, k, params=p)
```

Interpret `-1` labels as an underfilled result, not as a valid application ID.
A restrictive selector can make a small `max_codes` budget terminate before
`k` accepted results; `ensure_topk_full=True` makes the generic supported
paths treat `max_codes` as at least the number of post-selector scans needed
for top-k, but it is not universal across all implementations. `nprobe` and
budget behavior should be checked against the concrete index and backend.

When the coarse quantizer itself has parameters, put its parameter object in
`quantizer_params`; do not mutate a shared quantizer's global search setting
for one request.

## 4. Choose shards or replicas

### Disjoint shards

```python
shards = faiss.IndexShards(d, threaded=False, successive_ids=False)
for child, child_ids in partitions:
    child.add_with_ids(x_child, child_ids)
    shards.add_shard(child)
```

Use explicit IDs only when every partition has the same external namespace and
IDs are globally unique. If no explicit IDs are needed, let `successive_ids`
shift implicit row labels and record the resulting offset policy. A shard's
training method may broadcast or coordinate depending on the concrete shard
class; train a compatible plan and compare with a single-index baseline.

### Equivalent replicas

```python
replicas = faiss.IndexReplicas(threaded=False)
replicas.addIndex(clone_a)
replicas.addIndex(clone_b)
replicas.train(xt)
replicas.add(xb)
D, I = replicas.search(xq, k)
```

The same logical rows must be present in every replica in the same order. Use
`IndexIDMap2` inside each replica only if every copy receives identical external
IDs. A replica collection is not a merge operation and does not resolve ID
collisions.

For deterministic smoke tests use `threaded=False`. For production threading,
measure throughput and inspect tie behavior separately; equal distances can
legitimately reorder labels.

## 5. Direct map and reconstructability check

```python
ivf = faiss.index_factory(d, "IVF16,Flat")
ivf.train(xt)
ivf.add(xb)
try:
    ivf.reconstruct(0)
except RuntimeError:
    # Expected with DirectMap.NoMap on the relevant path.
    ivf.make_direct_map()
vector = ivf.reconstruct(0)
```

Record the direct-map type before and after. `make_direct_map()` is a stateful
mutation and may require IDs compatible with the selected direct-map type. For
an external-ID map, reconstruct through `IndexIDMap2` only after proving that
the child can reconstruct the corresponding internal row.

## 6. Preassigned IVF: expert, not default

`contrib`-style helpers can transform queries before calling an inner IVF's
`search_preassigned` when the outer index is `IndexPreTransform`. A safe
expert workflow is:

1. Confirm the outer transform chain and apply it exactly once.
2. Confirm transformed dimension, `nprobe`, list assignment shape, and coarse
   distance dtype.
3. Compare `search_preassigned` with ordinary `search` on the same query.
4. Use `add_core` only with assignments produced for this exact quantizer and
   trained codec; verify `ntotal`, list sizes, and search labels.
5. Keep the operation out of general user paths unless the assignment contract
   is persisted with the data.

Do not mutate inverted lists, replace quantizers, permute list storage, or
merge indexes merely to inspect them. Such changes need a separate persistence
and evaluation plan and can invalidate direct maps or ownership assumptions.

## 7. Repair a quantizer-lifetime failure

If a Python IVF wrapper still needs its coarse quantizer after the original
variable is deleted, rebuild the index through a public constructor and retain
the quantizer object. For an expert replacement helper, after assigning a new
quantizer also append it to the IVF wrapper's Python `referenced_objects` and
verify that its `ntotal == nlist` and centroid order matches the inverted lists.
Do not flip `own_fields` or SWIG `thisown` casually: those flags determine who
may delete the object. Re-run search, reconstruction, and list-size checks
before releasing the old object.

## 8. Outcome record

For every composed workflow record:

- outer-to-inner chain and data space at each boundary;
- metric, dimensions, training state, and `ntotal` for every child;
- external/internal ID namespace, duplicate policy, deletion count, and
  reconstruction assumption;
- selector class, selected IDs, parameter class, nesting, and per-call budgets;
- child ownership/reference policy and whether any raw pointer was assigned;
- shard/replica mode and tie/ordering tolerance;
- exact smoke command and observed labels/counts;
- unresolved backend or index-family limitations.
