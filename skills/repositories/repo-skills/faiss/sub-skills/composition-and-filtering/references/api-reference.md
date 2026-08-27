# Composition API reference

This reference is a compact operating table for the verified CPU package
`faiss-cpu` 1.15.0. It describes public Python/C++ concepts without requiring
the Faiss source checkout at runtime. Python examples assume `import faiss` and
contiguous NumPy arrays.

## Wrapper roles and data flow

| Wrapper | Input/output contract | Key state or caveat |
|---|---|---|
| `IndexIDMap(child)` | `add_with_ids(x, ids)` stores child positions but returns caller IDs on search | `add()` intentionally fails; selectors are translated from external IDs to child positions |
| `IndexIDMap2(child)` | Same ID translation plus `reconstruct(external_id)` lookup | Maintains a reverse map; call `check_consistency()` after expert mutations or merges |
| `IndexPreTransform(transform, child)` | Applies its transform chain to training, add, search, and range search before forwarding | `chain` order matters; `SearchParametersPreTransform.index_params` carries an inner parameter object |
| `IndexRefine(base, refine)` | Base produces candidates; refine computes final distances for those candidates | Children must have same `d`, metric, and `ntotal` at construction; both must represent rows in the same order |
| `IndexRefineFlat(base)` | Creates an exact `IndexFlat` refinement child | Construct while `base.ntotal == 0`, then train/add through the refine wrapper |
| `IndexShards` | Searches all shards and merges top-k results | `successive_ids=True` shifts implicit labels by shard offsets; explicit IDs require `False` |
| `IndexReplicas` | Sends train/add to every replica and partitions queries across them | Replicas should be equivalent logical copies; reconstruction is from the first replica |

A safe mental model for a chain such as
`IndexPreTransform(NormalizationTransform, IndexRefineFlat(IVF..., ...))`
is:

```text
caller float32 x / xq
  -> transform chain (in listed order)
  -> refinement wrapper
       -> base candidate search (possibly IVF + selector/params)
       -> refine child exact distances
  -> labels and distances
```

An ID map around the storage adds one more boundary:

```text
external IDs --IDMap translation--> child row positions
```

Do not infer that an outer wrapper automatically makes an inner operation
supported. Inspect the concrete downcast type and test a tiny input.

## IDs, deletion, and reconstruction

| Need | Recommended operation | Outcome check |
|---|---|---|
| Stable labels on add | `index.add_with_ids(x, ids.astype('int64'))` | `index.search(xq, k)` contains the supplied labels, not row numbers |
| Delete external labels | `index.remove_ids(np.asarray(ids, dtype='int64'))` or a selector | Returned count equals the intended removals; deleted labels no longer search/reconstruct |
| Reconstruct by external ID | `IndexIDMap2(child).reconstruct(external_id)` | Requires the child reconstruction path; catch `RuntimeError` for missing IDs or unsupported child reconstruction |
| IVF reconstruct/update | `ivf.make_direct_map()` or `ivf.set_direct_map_type(...)` first | `ivf.direct_map.type` is not `DirectMap.NoMap`; verify values/labels after update |
| Search plus reconstruction | `index.search_and_reconstruct(...)` where supported | Prefer this when a direct map is intentionally absent; compare returned labels to search |

`IndexIDMap` and `IndexIDMap2` translate selectors before forwarding them. A
selector passed to an ID-mapped index therefore names **external IDs**. A
selector passed directly to an unwrapped IVF names the IVF's stored labels.
Keep the selected namespace in the run record.

The ID map stores a mapping from child row to external ID. Do not reuse an
external ID in one logical index unless the concrete index's semantics and
caller policy explicitly allow it. After deletion, child rows can compact;
never cache child row positions as durable external IDs.

## Selectors

| Selector | Use | Lifetime/shape note |
|---|---|---|
| `IDSelectorRange(imin, imax, assume_sorted=False)` | `[imin, imax)` | `assume_sorted=True` is only an optimization when scanned IDs are sorted |
| `IDSelectorBatch(ids)` | Sparse set membership | One-argument Python form accepts an integer array/list and owns/copies the set |
| `IDSelectorArray(ids)` | Small direct array | Python convenience retains the backing array; raw C++ pointer must outlive the selector |
| `IDSelectorBitmap(bitmap)` | Dense bounded ID mask | Use packed `uint8` bits; Python convenience retains the backing bitmap |
| `IDSelectorNot(sel)` | Complement | Retains the child selector in Python |
| `IDSelectorAnd/Or/XOr(lhs, rhs)` | Boolean composition | Retain both children; test the resulting namespace and bounds |
| `IDSelectorTranslated(id_map, sel)` | Explicit ID-map translation | Usually let `IndexIDMap*` perform this translation; use directly only when the inner namespace is understood |

For an IVF query:

```python
sel = faiss.IDSelectorBatch(np.asarray([101, 105], dtype="int64"))
params = faiss.SearchParametersIVF(nprobe=4, sel=sel)
D, I = index.search(xq, 10, params=params)
```

The class-level `index.nprobe` remains a default. A per-call
`SearchParametersIVF(nprobe=...)` overrides it for that search. Use the
parameter class matching the concrete search implementation; a parameter
object of the wrong dynamic type can raise `RuntimeError` or be rejected.

## Search parameter nesting

| Outer index | Parameter route |
|---|---|
| Plain IVF | `SearchParametersIVF(nprobe=..., sel=..., quantizer_params=...)` |
| `IndexPreTransform(inner)` | `SearchParametersPreTransform(index_params=inner_params)`; passing the inner params directly can work for some paths but explicit wrapping is safer |
| `IndexRefine` / `IndexRefineFlat` | `IndexRefineSearchParameters(k_factor=..., base_index_params=...)` |
| Transform outside refinement | `SearchParametersPreTransform(index_params=IndexRefineSearchParameters(...))` |
| ID map outside a search index | Use the inner-compatible parameter object with selector IDs in the external namespace; the ID map translates the selector |

`IndexRefineSearchParameters.base_index_params` is non-owning at the C++
level. In Python, keep it reachable through the parameter object's attribute or
an explicit local variable for the whole call. When refinement wraps IVF,
place `SearchParametersIVF(nprobe=...)` in `base_index_params`; `k_factor`
controls how many candidates the base requests relative to the final `k`.
`IndexRefineFlat` rejects unrelated parameter types; do not pass a bare
`SearchParametersIVF` directly to it.

## Shards and replicas

### Shards

```python
shards = faiss.IndexShards(d, threaded=False, successive_ids=False)
shards.add_shard(shard_a)
shards.add_shard(shard_b)
```

- All children must share dimension and compatible metric behavior.
- `successive_ids=True` is suitable for `add()`-driven partitioning: labels
  are shifted by preceding shard sizes. Passing explicit IDs while requesting
  shifts is an error by design.
- `successive_ids=False` preserves explicit IDs and distributes explicit
  `add_with_ids` calls. Prove that IDs are globally unique if callers expect a
  single logical namespace; duplicate IDs are not deduplicated.
- `threaded=True` changes scheduling, not the ID policy. Use deterministic,
  non-threaded mode for a smoke and investigate ties before treating a label
  ordering difference as a regression.

### Replicas

Replicas receive the same train/add operations. Search queries are partitioned
among the replica children and results are joined. Use replicas when every
child holds equivalent rows and the goal is query parallelism or capacity;
use shards when each child owns a disjoint partition. Do not add independently
trained, differently ordered data as replicas and expect equivalent labels.

## IVF direct maps and advanced tooling

`IndexIVF` exposes `direct_map` and `set_direct_map_type`. The practical
choices are `DirectMap.NoMap`, `DirectMap.Array`, and
`DirectMap.Hashtable` (exact names can be checked with `dir(faiss.DirectMap)`).
A direct map enables ID-to-inverted-list lookup for reconstruction and updates,
but increases memory and can constrain arbitrary IDs or removal/merge paths.

Public advanced methods include `add_core(..., precomputed_idx=...)`,
`search_preassigned(...)`, and `reconstruct_from_offset(...)`. They bypass
part of the ordinary coarse-assignment path and require the caller to maintain
correct list assignments, coarse distances, dimensions, and codec assumptions.
Use them only after a tiny comparison with ordinary `add`/`search`; they are
not part of the default safe smoke.

Read-only inspection is safer:

```python
ivf = faiss.extract_index_ivf(index)  # if the wrapper contains an IVF
print(ivf.nlist, ivf.ntotal, ivf.nprobe, ivf.direct_map.type)
sizes = [ivf.invlists.list_size(i) for i in range(ivf.nlist)]
```

Do not call raw inverted-list replacement, permutation, removal, or network
helpers from a default workflow. Those operations can invalidate direct maps,
quantizer/list correspondence, or external IDs.

## Compatibility gates

- CPU facts verified for this graph: Faiss 1.15.0, Python >=3.10,
  `faiss-cpu`, NumPy float32 input contract, and compile options `OPTIMIZE DD
  AVX2`.
- CUDA hardware exists on the host, but no CUDA Faiss package was prepared for
  this graph. GPU, cuVS, ROCm, Metal, and SVS behavior is conditional and
  unverified; route those claims to the accelerated sibling.
- Refinement can improve ranking only when the base candidate set contains
  useful neighbors and the refine child stores rows in the same order. It does
  not recover candidates omitted by the base or repair incompatible metrics.
