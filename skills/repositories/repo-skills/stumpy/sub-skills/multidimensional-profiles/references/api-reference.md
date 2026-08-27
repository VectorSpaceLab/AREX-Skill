# API Reference

## What to remember first
- `T` is a 2-D array with shape `(d, n)`.
- Rows are dimensions and columns are time.
- Use `float64` values.
- `P` and `I` both have shape `(d, n - m + 1)`.
- Row `k` in `P` / `I` is the `(k + 1)`-dimensional profile.
- `subspace(..., k)` returns `k + 1` dimension indices.
- `mdl(...)` returns one bit-size value per `k`, where `k` is zero-based.

## Returned profile object
`mstump` and `maamp` return an `mparray`:

```python
mp = stumpy.mstump(T, m)
P, I = mp
# or:
P, I = mp.P_, mp.I_
```

## Core profile builders

### `mstump`
`stumpy.mstump(T, m, include=None, discords=False, normalize=True, p=2.0, T_subseq_isconstant=None)`

- Normalized multidimensional matrix profile.
- Self-join only.
- `include` is a zero-based list of dimension indices to force into the search.
- `discords=True` reverses the ranking so larger values become the target.
- `normalize=False` routes to the non-normalized family.
- `p` is ignored when `normalize=True`.

### `maamp`
`stumpy.maamp(T, m, include=None, discords=False, p=2.0)`

- Non-normalized multidimensional matrix profile.
- Self-join only.
- Same row/column layout and same `include` / `discords` semantics as `mstump`.
- Use this path for absolute distances or other non-normalized workflows.

## Query-window helpers
These are module helpers, not top-level convenience functions.

### Normalized helper
`from stumpy.mstump import multi_distance_profile`

`multi_distance_profile(query_idx, T, m, include=None, discords=False, normalize=True, p=2.0, T_subseq_isconstant=None)`

- Returns a distance matrix with shape `(d, n - m + 1)`.
- Each row is the distance profile for one dimension.
- Useful for checking how a single query window behaves before you commit to a `k` value.

### Non-normalized helper
`from stumpy.maamp import maamp_multi_distance_profile`

`maamp_multi_distance_profile(query_idx, T, m, include=None, discords=False, p=2.0)`

- Same shape and interpretation as the normalized helper.
- Use it when the rest of the workflow is non-normalized.

## Dimension-selection helpers

### `subspace`
`stumpy.subspace(T, m, subseq_idx, nn_idx, k, include=None, discords=False, discretize_func=None, n_bit=8, normalize=True, p=2.0, T_subseq_isconstant=None)`

- Returns the `(k + 1)` dimensions that best explain the pair `(subseq_idx, nn_idx)`.
- `k` is zero-based.
- `include` is respected first, then the remaining dimensions are ordered by distance.
- `discords=True` flips the ordering so large distances are favored.
- `normalize=False` routes to the non-normalized subspace search.

### `mdl`
`stumpy.mdl(T, m, subseq_idx, nn_idx, include=None, discords=False, discretize_func=None, n_bit=8, normalize=True, p=2.0, T_subseq_isconstant=None)`

- Returns `(bit_sizes, subspaces)`.
- `bit_sizes[k]` is the MDL score for the `k`-dimensional candidate.
- `subspaces[k]` is the dimension list for that same candidate.
- Pick `np.argmin(bit_sizes)` when you want the most compressible subspace.
- `normalize=False` routes to the non-normalized MDL path.

## Motif handoff helpers

### `mmotifs`
`stumpy.mmotifs(T, P, I, min_neighbors=1, max_distance=None, cutoffs=None, max_matches=10, max_motifs=1, atol=1e-8, k=None, include=None, normalize=True, p=2.0, T_subseq_isconstant=None)`

- Motif-only handoff from a normalized multidimensional profile.
- Returns `motif_distances`, `motif_indices`, `motif_subspaces`, and `motif_mdls`.
- Use it only with motif-oriented `P` / `I`.
- Do not feed it a discord-specific profile.

### `aamp_mmotifs`
`stumpy.aamp_mmotifs(T, P, I, min_neighbors=1, max_distance=None, cutoffs=None, max_matches=10, max_motifs=1, atol=1e-8, k=None, include=None, p=2.0)`

- Motif-only handoff from a non-normalized multidimensional profile.
- Same return structure as `mmotifs`.
- Use it after `maamp`, not after `mstump`.

## Minimal selection chain
```python
P, I = stumpy.mstump(T, m, include=include)
motif_idx = np.argmin(P, axis=1)
nn_idx = I[np.arange(P.shape[0]), motif_idx]
mdls, subspaces = stumpy.mdl(T, m, motif_idx, nn_idx, include=include)
best_k = int(np.argmin(mdls))
S = stumpy.subspace(T, m, motif_idx[best_k], nn_idx[best_k], best_k, include=include)
```

## When to switch families
- Stay on `mstump` / `subspace` / `mdl` / `mmotifs` when the data is normalized.
- Switch to `maamp` / `normalize=False` / `aamp_mmotifs` when the data is not normalized.
- Keep the full chain in the same family so the subspace choice matches the profile that produced it.
