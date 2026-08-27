---
name: aligned-composition
description: "Covers AlignedUMAP for related slices and fitted UMAP model
  composition with intersection, union, or contrast operators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Aligned UMAP and Model Composition

Use this sub-skill when embeddings must stay comparable across related slices,
time periods, batches, or feature views, or when a task asks to combine fitted
UMAP models with `*`, `+`, or `-`.

## Route Here For

- `umap.AlignedUMAP` on a list of related datasets.
- Relation dictionaries that map sample indices from one slice to the next.
- Online updates with a new slice and relation map.
- Per-slice parameter lists for `n_neighbors` or other AlignedUMAP parameters.
- Choosing `alignment_regularisation` or `alignment_window_size`.
- Combining two fitted `UMAP` models over the same samples using intersection
  (`*`), union (`+`), or contrast (`-`).

## Route Elsewhere

- Single-dataset fit/transform/sparse/precomputed workflows: read
  [core-embedding](../core-embedding/SKILL.md).
- Supervised labels or densMAP: read
  [supervised-density](../supervised-density/SKILL.md).
- Plotting aligned embeddings: read
  [plotting-diagnostics](../plotting-diagnostics/SKILL.md).
- Parametric neural embeddings are out of scope for this sub-skill.

## Quick AlignedUMAP Pattern

```python
import umap

# X_slices is a list such as [X_t0, X_t1, X_t2].
# relations[t] must map row indices in X_slices[t] to row indices in
# X_slices[t + 1]. Keep those row positions stable after filtering/sorting.
relations = [
    {0: 0, 1: 2, 2: 3},
    {0: 1, 2: 2, 3: 4},
]
model = umap.AlignedUMAP(
    n_neighbors=15,
    alignment_regularisation=0.01,
    alignment_window_size=3,
    random_state=42,
).fit(X_slices, relations=relations)
embeddings = model.embeddings_
```

Run [`scripts/aligned_composition_smoke.py`](scripts/aligned_composition_smoke.py)
for a tiny no-network aligned/composition check:

```bash
python scripts/aligned_composition_smoke.py --composition --json
```

For online updates, remember that `update` uses the same adjacent-slice row
index convention as `fit`: map rows in the previously fitted slice to rows in
the new slice you are adding.

## Quick Composition Pattern

```python
left_mapper = umap.UMAP(random_state=42).fit(left_view)
right_mapper = umap.UMAP(random_state=42).fit(right_view)
intersection = left_mapper * right_mapper
union = left_mapper + right_mapper
contrast = left_mapper - right_mapper
```

Only compose models trained on the same sample order and one-to-one sample
correspondence. Do not use these operators to combine unrelated datasets.

## Decision Points

1. **Slices versus views**: use AlignedUMAP for ordered related slices; use
   composition operators for different views of the same rows.
2. **Relations**: relation dictionaries map adjacent slices. Missing keys can
   represent absent correspondence, but accidental missing keys cause drift.
3. **Alignment strength**: stronger regularisation makes slices more comparable
   but can suppress real temporal or batch-specific change.
4. **Window size**: larger windows propagate alignment across more neighbouring
   slices; validate if distant slices should influence each other.
5. **Contrast is directional**: `A - B` is not the same as `B - A`.
6. **Update direction**: `update` uses the same forward slice-to-slice relation
   convention as `fit`; build the map from the existing last slice to the new
   slice.

## References

- Read [workflows](references/workflows.md) for aligned slices, updates,
  per-slice parameters, and model composition recipes.
- Read [API reference](references/api-reference.md) for signatures, relation
  schema, and operator semantics.
- Read [troubleshooting](references/troubleshooting.md) for relation and
  row-correspondence failures.
