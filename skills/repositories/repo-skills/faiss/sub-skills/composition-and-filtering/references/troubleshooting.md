# Composition troubleshooting and recovery

Use this table to isolate one boundary at a time. Preserve the original chain,
parameter object type, IDs, and exception before changing anything.

| Symptom | Likely boundary | Recovery |
|---|---|---|
| `add()` fails on `IndexIDMap*` | The map requires caller IDs | Use `add_with_ids(x, int64_ids)` and verify label policy |
| Search returns row numbers instead of external IDs | The ID map is not the outer result boundary, or the query bypassed it | Search the wrapper, not its child; inspect `type`/downcast and compare child labels to wrapper labels |
| Selector returns unexpected/empty results through an ID map | Selector is in the wrong namespace | Pass external IDs at the ID map boundary; use `IDSelectorTranslated` only when deliberately addressing child positions |
| Deleted ID still reconstructs | Wrong ID namespace, stale reverse map, or deletion did not reach child | Check returned removal count, `ntotal`, `IndexIDMap2.check_consistency()`, and reconstruct a known neighbor; do not reuse cached child positions |
| `IndexIDMap2.reconstruct` raises | Missing ID or child lacks reconstructability/direct map | Confirm the ID exists; enable an IVF direct map when required, or use `search_and_reconstruct`/an exact side store |
| `IndexRefineFlat` rejects construction | Base already has vectors | Construct it while the base is empty, then train/add through the refinement wrapper |
| `IndexRefine` constructor rejects | Child dimensions, metrics, or `ntotal` differ | Compare `d`, `metric_type`, `is_trained`, and row counts; rebuild both children from one ordered data source |
| Refined result does not improve recall | Candidate set misses the true neighbor, `k_factor` is too small, or metric spaces differ | Increase candidate coverage (`nprobe`, then `k_factor`), verify transform/metric order, and compare to exact baseline |
| `IndexRefineFlat` says parameters have wrong type | A bare IVF/general parameter was sent to the refine wrapper | Use `IndexRefineSearchParameters`; put IVF parameters in `base_index_params`, and wrap with `SearchParametersPreTransform` when a transform is outermost |
| Per-call `nprobe` appears ignored | Parameter did not reach the inner IVF | Use `SearchParametersPreTransform(index_params=...)` for a transform wrapper and `IndexRefineSearchParameters(base_index_params=...)` for refinement; verify with a tiny changed-result or stats check |
| Filtered IVF result has `-1` labels | Fewer than `k` candidates survived the selector/budget | Increase `nprobe` or `max_codes`, use `ensure_topk_full` only where supported, and treat `-1` as underfill |
| `max_codes` changes results unexpectedly | It is a work cap, and selector filtering is applied to accepted candidates on supported paths | Compare unbounded and capped searches; record recall/underfill rather than assuming a bug |
| `max_empty_result_buckets` loses range results | Early stopping is intentionally enabled | Set it to zero for the baseline, then reintroduce it with an explicit recall/latency acceptance target |
| Selector construction fails for an array/bitmap | Wrong dtype, shape, or packed representation | Use contiguous `int64` IDs; for bitmaps use packed `uint8` and the supported constructor form; test membership before search |
| Search crashes after deleting quantizer/transform/child | A raw child pointer was not retained | Reconstruct through a public wrapper, keep a Python reference, and inspect `referenced_objects`; never rely on a local variable that has been deleted |
| Child is unexpectedly deleted twice | Conflicting `own_fields`, `thisown`, or explicit ownership transfer | Stop mutating ownership flags; use one clear owner and rerun in a fresh process |
| `IndexShards` rejects explicit IDs | `successive_ids=True` conflicts with explicit IDs | Construct with `successive_ids=False`; prove global ID uniqueness |
| Sharded labels collide | Different shards contain the same explicit ID | Change the allocation policy or namespace; shard merge does not deduplicate |
| Shard results differ only in tie order | Equal float distances or threaded merge ordering | Compare distance sets/recall and use non-threaded mode for deterministic diagnostics |
| Replica results are inconsistent | Rows/order/training differ across replicas | Clone or identically populate children; replicas are not a merge or conflict resolver |
| IVF reconstruction fails without an obvious error | `DirectMap.NoMap` or external-ID/internal-row confusion | Inspect `direct_map.type`, enable the appropriate map before adding/updating, and distinguish caller IDs from row positions |
| Preassigned search differs from ordinary search | Transform applied zero/twice, wrong list assignments, or wrong coarse distances | Apply the transform exactly once, validate `(n, nprobe)` assignment shape and dtype, and compare one query to ordinary search |
| Low-level IVF inspection changed results | Inverted lists and quantizer no longer correspond | Restore from a trusted persisted copy; do not use permutation/replacement/merge helpers as read-only inspection |

## Ownership repair checklist

1. Reproduce in a fresh process with a tiny index.
2. Keep explicit Python variables for the quantizer, transform, base child,
   refine child, shard/replica children, selector, selector backing arrays, and
   nested parameter objects until all calls complete.
3. For supported constructors and `add_shard`/`addIndex`, verify the wrapper
   has retained children; do not edit the list unless using a documented expert
   helper.
4. If a quantizer was replaced, verify its centroid count and order, retain it
   in `referenced_objects`, and keep the old quantizer alive until search and
   list checks pass.
5. Never call `this.disown()`, change `own_fields`, or transfer ownership as a
   speculative fix. These actions can cause leaks or double frees.

## Selector and parameter diagnosis

Use membership checks before search:

```python
for candidate in [external_id_a, external_id_b]:
    print(candidate, sel.is_member(int(candidate)))
```

Then run, in order:

1. the child or base without a selector;
2. the same index with `IDSelectorAll`;
3. the intended selector with unbounded search;
4. the intended selector plus one budget change;
5. the full nested composition.

At each stage record labels, `-1` count, `ntotal`, `nprobe`, and selector
namespace. If stage 2 differs from stage 1, the concrete implementation's
selector path may not be supported or a parameter was nested incorrectly.

## Safe stop conditions

Stop and route to another branch when:

- the desired behavior depends on an unverified CUDA/cuVS/ROCm/Metal/SVS
  implementation;
- a custom selector requires a compiled extension or Python callback at scale;
- a raw inverted-list mutation, network/RPC operation, or merge is required;
- a direct map must be rebuilt after persistence and the persistence contract
  has not been checked;
- exact reconstruction is required from a codec that only provides approximate
  decode.
