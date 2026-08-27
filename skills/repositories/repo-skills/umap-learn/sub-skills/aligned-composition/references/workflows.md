# AlignedUMAP and Composition Workflows

Use this reference when a task involves ordered slices, changing membership,
online alignment updates, per-slice settings, or fitted-UMAP model operators.
For one ordinary dataset, route to the sibling core embedding sub-skill instead.
For plotting the results, route to the plotting diagnostics sub-skill.

## Build Relations from Stable IDs

Most real datasets have stable sample IDs, not row-index relations. Convert IDs
to row positions after final sorting/filtering. Each relation dictionary maps
rows from one slice to rows in the immediately following slice.

```python
ids_t0 = ["a", "b", "c"]
ids_t1 = ["b", "a", "d", "c"]
index_t1 = {sample_id: i for i, sample_id in enumerate(ids_t1)}
relation_0_to_1 = {
    i: index_t1[sample_id]
    for i, sample_id in enumerate(ids_t0)
    if sample_id in index_t1
}
# relation_0_to_1 == {0: 1, 1: 0, 2: 3}
```

Repeat this for every adjacent pair: slice 0 to 1, slice 1 to 2, and so on.
For `n` slices, pass exactly `n - 1` dictionaries. Missing keys are allowed and
mean that a row has no known correspondence in the next slice; do not include a
made-up key to force continuity.

## Fit Aligned Slices

```python
import umap

model = umap.AlignedUMAP(
    n_neighbors=10,
    alignment_regularisation=0.01,
    alignment_window_size=3,
    random_state=42,
).fit([X0, X1, X2], relations=[rel_0_1, rel_1_2])

embeddings = model.embeddings_
for X_slice, embedding in zip([X0, X1, X2], embeddings):
    assert embedding.shape == (X_slice.shape[0], 2)
```

Compare each aligned embedding to its raw slice structure. Too much alignment
can hide real slice-specific change; too little alignment lets known shared
samples drift.

## Online Update

Fit an initial sequence, then append one new slice at a time. The update
relation still uses the adjacent forward convention: rows in the previously
fitted last slice map to rows in the new slice.

```python
model = umap.AlignedUMAP(random_state=42).fit([X0, X1], relations=[rel_0_1])
rel_1_to_2 = build_relation_from_stable_ids(ids_t1, ids_t2)
model.update(X2, relations=rel_1_to_2)
new_embedding = model.embeddings_[-1]
```

Before update, validate that the relation map connects the previous slice to
the new following slice and that all indices are in range. If the map was built
from new slice rows back to previous slice rows, invert it before calling
`update`.

## Per-Slice Parameters

Use list-valued parameters when slices need different settings:

```python
model = umap.AlignedUMAP(
    n_neighbors=[10, 15, 20],
    min_dist=[0.05, 0.1, 0.2],
    alignment_window_size=2,
    alignment_regularisation=1e-3,
    random_state=42,
)
model.fit([X0, X1, X2], relations=[rel_0_1, rel_1_2])
```

Keep `n_components` scalar; the implementation rejects varying component counts.
Document why settings differ, because accidental list-length mismatches are a
common source of confusing assertions.

## Alignment Strength and Window Size

- Increase `alignment_regularisation` when known corresponding samples drift too
  much across embeddings.
- Decrease it when time-specific or batch-specific changes are being flattened.
- Increase `alignment_window_size` only when it is meaningful for non-adjacent
  slices to influence each other; relations are still specified only between
  adjacent slices and then chained internally.
- For high-stakes analyses, compare aligned output with independent per-slice
  UMAP fits and with a few known trajectories.

## Compose Feature Views

For the same samples measured in different feature spaces, fit one UMAP mapper
per view and compose the fitted models. The row order must be exactly the same
in every view.

```python
left = umap.UMAP(random_state=42).fit(left_features)
right = umap.UMAP(random_state=42).fit(right_features)
common_structure = left * right      # intersection
expanded_structure = left + right    # union
left_minus_right = left - right      # contrast, directional
embedding = common_structure.embedding_
```

Use `*` when you need neighbourhood structure common to both views. Use `+`
when either view should contribute neighbourhoods. Use `-` for contrastive
exploration and record operand order because `A - B` is not `B - A`.

## Validation Ideas

- Nearest-neighbour preservation within each aligned slice.
- Smooth movement of known corresponding samples across adjacent embeddings.
- Relation coverage percentage for each adjacent pair.
- Sensitivity to `alignment_regularisation` and `alignment_window_size`.
- For composition, compare composed output with each individual view and a
  simple concatenated-feature baseline when feasible.
