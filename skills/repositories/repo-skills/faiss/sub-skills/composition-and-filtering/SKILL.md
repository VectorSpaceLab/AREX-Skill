---
name: composition-and-filtering
description: "This skill teaches a Researcher to compose Faiss indexes, preserve
  external IDs and child lifetimes, apply selectors and per-search parameters,
  and choose safe shard, replica, refinement, and IVF inspection workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Composition and filtering

Use this branch when a working Faiss index must be wrapped, filtered, refined,
sharded, replicated, assigned external IDs, deleted by ID, or inspected through
IVF metadata. It owns **composition order, label translation, selector routing,
child ownership, direct-map prerequisites, and per-query parameter overrides**.
It does not choose the base index family, codec, persistence format, or optional
accelerator.

## Route first

- For metric, dimension, exact/approximate family, factory strings, ordinary
  `nprobe`, and baseline search behavior, read
  [index-selection-and-search](../index-selection-and-search/SKILL.md).
- For training, transforms used as codecs, PQ/SQ/RQ/AQ, code sizes, fast scan,
  and lossy reconstruction, read
  [training-and-compression](../training-and-compression/SKILL.md).
- For serialization, merge/persistence constraints, ground truth, recall, or
  evaluation, read [persistence-and-evaluation](../persistence-and-evaluation/SKILL.md).
- For RPC/network, C/C++ interop, CUDA, cuVS, ROCm, Metal, SVS, or GPU transfer,
  read [accelerated-and-interoperable](../accelerated-and-interoperable/SKILL.md).

## Operating procedure

1. Draw the data-flow before constructing anything. The outermost wrapper sees
   caller vectors and queries; each `IndexPreTransform` applies its transform
   chain in order; `IndexIDMap`/`IndexIDMap2` translates inner positions to
   caller IDs; IVF performs coarse assignment then list scanning; `IndexRefine`
   asks its base index for candidates and its refine index for final distances.
   Search parameters must be wrapped to match that same nesting order.
2. Make the ID policy explicit. Use `add_with_ids(x, ids)` for stable external
   labels; do not call `add()` on an `IndexIDMap*`. `IndexIDMap2` adds an
   external-ID reverse map and supports external-ID `reconstruct` when the
   wrapped index can reconstruct. A selector passed at the outer ID map is
   translated to inner positions. Verify that IDs are unique in a logical
   corpus; shards with `successive_ids=False` do not prevent cross-shard ID
   collisions.
3. Keep child objects alive. Python wrappers retain constructor children and
   children added through `add_shard`/`addIndex` in `referenced_objects` for the
   supported classes. Still retain references yourself when assigning raw
   pointer fields, replacing quantizers, or using custom extensions. Never
   delete or mutate a quantizer, transform, selector backing array, or refine
   child while a search can use it. `own_fields` is a C++ ownership flag, not a
   substitute for understanding Python SWIG references.
4. Choose composition order deliberately. Put a transform outside the index
   whose stored/search space it should change. Put an ID map outside the
   storage whose results need external labels. Put refinement outside the
   candidate index and add the same vectors to base and refine storage through
   the refinement wrapper. For a transformed refinement search, use
   `SearchParametersPreTransform(index_params=...)` when the inner parameter
   object must cross the transform; use `IndexRefineSearchParameters` for
   `k_factor` and `base_index_params`.
5. For IVF filtering, create an `IDSelector` in the same ID namespace as the
   parameter recipient. Use `IDSelectorRange` for a contiguous interval,
   `IDSelectorBatch` for a set, `IDSelectorBitmap` for a dense bounded mask, and
   `IDSelectorAnd/Or/XOr/Not` for boolean composition. Put the selector in
   `SearchParametersIVF(sel=selector)` (or the appropriate base parameter
   class), not in a global mutable setting. Check support for the concrete
   index: selector behavior is not a promise that every backend or wrapper
   accepts every selector type.
6. Override IVF search per call with `SearchParametersIVF`: `nprobe` controls
   lists, `max_codes` bounds work, `max_lists_num` limits fast-scan list visits,
   `ensure_topk_full` softens small post-selector budgets, and
   `max_empty_result_buckets` trades range-search recall for early stopping.
   `quantizer_params` routes parameters to a parameterized coarse quantizer.
   Compare against an unfiltered/unbounded baseline before interpreting a
   recall change.
7. Use direct maps only for a declared need. `IndexIVF.reconstruct(id)` and
   `update_vectors` require a maintained direct map; call
   `make_direct_map()` or `set_direct_map_type(...)` before those operations.
   Direct maps add memory and impose ID/merge constraints; `search_and_reconstruct`
   can avoid a direct map for supported IVF paths. An ID map does not make an
   arbitrary lossy or non-reconstructable child reconstructable.
8. Select shards versus replicas by semantics: shards partition stored vectors
   and merge candidates; replicas hold the same logical corpus and distribute
   query work. Keep dimensions, metrics, training state, and ID policy aligned.
   For implicit shard IDs, use `successive_ids=True`; for explicit IDs use
   `successive_ids=False` and prove global uniqueness. Do not use replicas to
   deduplicate conflicting IDs or to merge independently trained incompatible
   indexes.
9. For advanced IVF tooling, prefer read-only inspection of `nlist`, list sizes,
   quantizer state, `direct_map.type`, and `ntotal`. Preassigned add/search and
   quantizer replacement are expert-only operations: validate dimensions,
   list assignments, ownership, and trained state first. Do not expose raw
   inverted-list mutation, network/RPC, or destructive merge operations in a
   default smoke.
10. Run the bundled deterministic check from any directory:

    ```bash
    python /path/to/composition-and-filtering/scripts/smoke_composition.py --help
    python /path/to/composition-and-filtering/scripts/smoke_composition.py
    ```

    It validates external-ID translation/deletion, a transformed refinement
    chain, a selector route, and safe IVF metadata inspection. It is a CPU
    smoke, not a performance or backend certification.

## Recovery routing

Start with [troubleshooting.md](references/troubleshooting.md) for stale or
translated labels, deleted-child crashes, incorrect parameter nesting, empty
filtered results, failed reconstruction, shard collisions, or refinement
mismatches. Route a wrong base family or metric to the index-selection sibling,
codec/training errors to training-and-compression, persistence/merge/evaluation
to persistence-and-evaluation, and backend/network behavior to
accelerated-and-interoperable.

## Bundled references

- [Composition API and compatibility reference](references/api-reference.md)
- [Composition workflows and data-flow recipes](references/workflows.md)
- [Troubleshooting and recovery](references/troubleshooting.md)
- [Deterministic composition smoke](scripts/smoke_composition.py)
