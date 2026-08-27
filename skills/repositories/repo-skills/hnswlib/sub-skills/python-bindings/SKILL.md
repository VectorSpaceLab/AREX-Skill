---
name: python-bindings
description: "Operate hnswlib 0.9.0 Python Index and BFIndex for typed vector
  search, filtering, mutation, persistence, pickle, and recall checks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Python bindings

Use this sub-skill when a Python task mentions `hnswlib.Index`, `hnswlib.BFIndex`,
NumPy vectors, `knn_query`, `add_items`, `save_index`, `load_index`, deletion,
replacement, pickle, filters, or recall. The contract covers the CPU-native
hnswlib 0.9.0 extension and its three exposed spaces: `l2`, `ip`, and
`cosine`. It does not provide a CUDA API.

## Operating contract

- Work with an installed `hnswlib` extension and NumPy arrays. The package's
  normal runtime dependency is NumPy; source builds additionally need the
  C++/pybind11 toolchain described in [troubleshooting.md](references/troubleshooting.md).
- Treat labels as integer, non-negative external identifiers. Use explicit,
  unique `np.int64` labels when persistence, updates, or external metadata must
  remain stable.
- Keep vectors as finite numeric data with shape `(rows, dim)` or a single
  vector of shape `(dim,)`. The binding force-casts input to contiguous
  `float32`, but applications should validate dimensionality before querying.
- Keep mutation, querying, resizing, and serialization phases coordinated. The
  extension releases the GIL around native work; Python-level safety is not a
  substitute for the operation compatibility rules in [workflows.md](references/workflows.md).

## Standard workflow

1. **Normalize the request.** Record `space`, `dim`, capacity, label policy,
   query `k`, filter cardinality, deletion/replacement needs, persistence path,
   and the target recall or exactness requirement.
2. **Check import/build state.** Import `hnswlib` and NumPy in the intended
   environment. If importing a source-built extension, use the compiler and
   native-linkage diagnosis in [troubleshooting.md](references/troubleshooting.md).
3. **Construct and initialize.** Create `Index(space, dim)`, then call
   `init_index(max_elements, M=16, ef_construction=200, random_seed=100,
   allow_replace_deleted=False)`. `Index` is not ready for insertion until
   `init_index` succeeds.
4. **Choose a stable data contract.** Convert vectors with
   `np.asarray(data, dtype=np.float32)` and assert `data.ndim in (1, 2)` and
   the trailing dimension equals `dim`. Use one scalar integer label only for
   one vector; otherwise pass one label per row. Omitted labels are assigned by
   the binding and are not a durable metadata scheme.
5. **Populate and tune.** Call `add_items(data, ids=None, num_threads=-1,
   replace_deleted=False)`. Reusing an existing label updates its vector.
   Set `index.ef` or call `set_ef`; choose `ef >= k` and increase it for recall
   at the cost of search time. Set `num_threads`/`set_num_threads` deliberately.
6. **Query and validate.** Call `knn_query(data, k=1, num_threads=-1,
   filter=None)`. The return is `(labels, distances)`, both shaped `(rows, k)`
   even for a single-vector query. A filter is a Python callable over external
   labels; use `num_threads=1` for filtered search and ensure every query has
   at least `k` eligible live items.
7. **Inspect data and metadata.** Use explicit label arrays with
   `get_items(ids, return_type="numpy"|"list")`; sort `get_ids_list()` before
   comparing it. Check `space`, `dim`, `M`, `ef_construction`, `ef`,
   `max_elements`, `element_count`, and their method equivalents as needed.
   In this binding, `get_items(None)` does not mean “all labels”; retrieve all
   vectors by passing `get_ids_list()` explicitly.
8. **Apply lifecycle mutations.** `mark_deleted(label)` hides a live label;
   `unmark_deleted(label)` restores it. For slot reuse, enable
   `allow_replace_deleted=True` at initialization or load, mark deletions, and
   pass `replace_deleted=True` with new labels. Without that policy, replacement
   raises; deletion alone does not create unbounded capacity.
9. **Persist or pickle safely.** Use a temporary/application-owned path with
   `save_index`, then create a fresh `Index` and `load_index(path,
   max_elements=0, allow_replace_deleted=...)`. Set `ef` again after
   `load_index`: index-file persistence does not preserve it. `pickle.dumps`
   and `pickle.loads` preserve the Python index state, including `ef`, but
   pickle/get-index-state operations must not overlap `add_items`.
10. **Measure recall when approximate results matter.** Build a same-space,
    same-dimension `BFIndex`, add the same labeled vectors, query both with a
    valid `k`, and compare label overlap. BFIndex is an exact linear-scan
    oracle, not a performance substitute. Use the bundled tiny checks first:
    `python scripts/python_lifecycle_smoke.py --help` and then run the selected
    smoke script from outside the checkout.

## API routing map

- Exact signatures, result shapes, properties, and BFIndex: [api-reference.md](references/api-reference.md).
- Build/query/persistence/mutation/recall recipes: [workflows.md](references/workflows.md).
- Shape, labels, dtype, metrics, normalization, and distances:
  [data-and-distance-semantics.md](references/data-and-distance-semantics.md).
- Installation, import, native flags, errors, concurrency, and recovery:
  [troubleshooting.md](references/troubleshooting.md).
- Deterministic executable checks:
  `scripts/python_lifecycle_smoke.py`, `scripts/python_filter_smoke.py`,
  `scripts/python_mutation_smoke.py`, and `scripts/python_pickle_smoke.py`.

## Hard guardrails

- Do not claim GPU or CUDA support. The exposed extension is CPU-native.
- Do not use `k` greater than the live/filtered population, or interpret an
  exception about a contiguous result array as a partial result.
- Do not assume `ef` is automatically adequate; set `ef >= k` after every
  index-file load and tune it against BFIndex when recall is material.
- Do not use negative labels, mismatched label counts, wrong vector dimensions,
  or a scalar label for multiple rows. Validate query dimensions too: the
  observed binding checks dimensions on insertion but does not provide the same
  explicit query-dimension guard.
- Do not call `mark_deleted` twice, unmark a label that is not marked, replace
  without the initialization/load policy, or insert beyond capacity without
  resizing/loading with a larger capacity.
- Do not compare cosine `get_items` output directly to the original unnormalized
  vectors; returned stored vectors are normalized.
- Do not overlap `add_items` with `knn_query`; concurrent additions are allowed
  with other additions, and concurrent queries with other queries. Python
  filters should run single-threaded. Resizing is not concurrent-safe with
  adding/querying, and pickle/getIndexParams is not concurrent-safe with
  adding.

## Completion checklist

Before handing off a Python integration, confirm:

- import and package/runtime facts were checked in the target environment;
- the metric, dimension, capacity, dtype, shapes, and labels are explicit;
- initialization precedes insertion and `ef >= k` is set for each query phase;
- result shapes and filter eligibility are asserted;
- explicit IDs are used for `get_items`, metadata, updates, and persistence;
- deletion/replacement flags match the intended lifecycle;
- file paths are temporary or application-owned and reload uses a compatible
  metric/dimension;
- `ef` is restored after file loading, while pickle behavior is tested separately;
- BFIndex is used for exact comparison when a recall claim is required; and
- no unsupported CUDA, malformed-query, unsafe-concurrency, or dependency claim
  has been smuggled into the integration.
