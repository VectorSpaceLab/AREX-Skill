# AlignedUMAP and Composition API Reference

Use this reference for signatures, relation schemas, and model-composition
semantics. For step-by-step recipes, read the bundled workflows reference.

## `umap.AlignedUMAP` Constructor

Verified signature:

```python
umap.AlignedUMAP(
    n_neighbors=15,
    n_components=2,
    metric="euclidean",
    metric_kwds=None,
    n_epochs=None,
    learning_rate=1.0,
    init="spectral",
    alignment_regularisation=0.01,
    alignment_window_size=3,
    min_dist=0.1,
    spread=1.0,
    low_memory=False,
    set_op_mix_ratio=1.0,
    local_connectivity=1.0,
    repulsion_strength=1.0,
    negative_sample_rate=5,
    transform_queue_size=4.0,
    a=None,
    b=None,
    random_state=None,
    angular_rp_forest=False,
    target_n_neighbors=-1,
    target_metric="categorical",
    target_metric_kwds=None,
    target_weight=0.5,
    transform_seed=42,
    force_approximation_algorithm=False,
    verbose=False,
    unique=False,
)
```

Methods:

```python
model.fit(X, y=None, **fit_params)
model.fit_transform(X, y=None, **fit_params)
model.update(X, y=None, **fit_params)
```

For aligned workflows, `X` is normally a list of arrays, one per slice.
`fit_transform` returns the list of embeddings directly. `update` mutates the
existing aligned model in place and returns the updated estimator.

## Relation Schema

`relations` is a list of dictionaries. For `n` data slices, provide exactly
`n - 1` relation dictionaries:

```python
relations[t] = {row_index_in_slice_t: row_index_in_slice_t_plus_1}
```

Example:

```python
relations = [
    {0: 0, 1: 2},   # slice 0 -> slice 1
    {0: 1, 2: 3},   # slice 1 -> slice 2
]
```

Rules:

- Keys and values are integer row indices, not sample IDs. Convert stable IDs to
  row positions after sorting/filtering each slice.
- Each relation dictionary links adjacent slices only.
- Missing keys represent no known correspondence, but accidental omissions can
  weaken alignment.
- Validate relation indices against slice lengths before fitting or updating.
- Different slices may have different row counts; each dictionary only needs to
  cover valid row positions for its own adjacent pair.

## Per-Slice Parameters

AlignedUMAP can accept list-valued parameters in some workflows, such as one
`n_neighbors` or `min_dist` value per slice. The list length must match the
number of slices or the update call being made. Use scalar values unless
per-slice variation is intentional and tested.

## Update

`update(new_slice, relations=relation_from_previous_to_new, **params)` adds a new
slice to an existing aligned model. Provide the relation map from rows in the
previously fitted last slice to rows in the new slice, along with any per-slice
parameter values needed for the new slice.

If your source IDs were expressed in the opposite direction, invert the map
before calling `update`.

## Composition Operators on `UMAP`

Fitted `UMAP` models support graph-composition operators:

| Operator | Meaning | Use when |
| --- | --- | --- |
| `a * b` | Intersection of fuzzy topological representations | You need structure common to two feature views. |
| `a + b` | Union of representations | You need neighbourhoods supported by either view. |
| `a - b` | Contrast against the second representation | You need what the first view emphasizes beyond the second. |

Preconditions:

- Both models are already fitted.
- Both models represent the same samples in the same row order.
- Metrics/preprocessing for each view are documented.
- Contrast is directional and not commutative.

The result is a fitted-like UMAP mapper with an embedding of the combined graph.
Validate output quality; composition is powerful but experimental for many real
workflows.
