# Workflows

## 1. Normalized multidimensional motif route
Use this when the data should be z-normalized.

```python
import numpy as np
import stumpy

T = np.asarray(..., dtype=np.float64)  # shape (d, n)
m = 3
include = np.array([0, 1], dtype=np.int64)

P, I = stumpy.mstump(T, m, include=include, discords=False)
motif_idx = np.argmin(P, axis=1)
nn_idx = I[np.arange(P.shape[0]), motif_idx]
mdls, subspaces = stumpy.mdl(T, m, motif_idx, nn_idx, include=include)
best_k = int(np.argmin(mdls))
S = stumpy.subspace(T, m, motif_idx[best_k], nn_idx[best_k], best_k, include=include)

motif_distances, motif_indices, motif_subspaces, motif_mdls = stumpy.mmotifs(
    T, P, I, include=include, k=best_k
)
```

What to read from the result:
- `P.shape` and `I.shape` should be `(d, n - m + 1)`.
- `motif_idx[k]` is the best subsequence start for row `k`.
- `subspaces[best_k]` is the winning dimension subset for that row.
- `S` is the direct `k + 1`-dimensional subspace.
- `mmotifs` is the final motif-match handoff once the dimensions are settled.

## 2. Non-normalized multidimensional route
Use this when the data should stay on its original scale.

```python
import numpy as np
import stumpy

T = np.asarray(..., dtype=np.float64)
m = 3
include = np.array([0, 1], dtype=np.int64)
p = 2.0

P, I = stumpy.maamp(T, m, include=include, discords=False, p=p)
motif_idx = np.argmin(P, axis=1)
nn_idx = I[np.arange(P.shape[0]), motif_idx]
mdls, subspaces = stumpy.mdl(
    T, m, motif_idx, nn_idx, include=include, normalize=False, p=p
)
best_k = int(np.argmin(mdls))
S = stumpy.subspace(
    T, m, motif_idx[best_k], nn_idx[best_k], best_k, include=include, normalize=False, p=p
)

motif_distances, motif_indices, motif_subspaces, motif_mdls = stumpy.aamp_mmotifs(
    T, P, I, include=include, k=best_k, p=p
)
```

What to read from the result:
- Keep the whole chain non-normalized.
- Do not mix `maamp` output with normalized `mdl` / `subspace` calls.
- `aamp_mmotifs` is the motif handoff for this family.

## 3. Discord route
Use this when you want the most unusual subsequences instead of motifs.

```python
P, I = stumpy.mstump(T, m, include=include, discords=True)
discord_idx = np.argmax(P, axis=1)
nn_idx = I[np.arange(P.shape[0]), discord_idx]
mdls, subspaces = stumpy.mdl(T, m, discord_idx, nn_idx, include=include, discords=True)
best_k = int(np.argmin(mdls))
S = stumpy.subspace(T, m, discord_idx[best_k], nn_idx[best_k], best_k, include=include, discords=True)
```

Important rules:
- Use `discords=True` everywhere in that profile chain.
- Use `np.argmax`, not `np.argmin`, when selecting the row-wise candidate.
- Do not feed a discord-specific profile into `mmotifs` or `aamp_mmotifs`.
- The same `discords` logic applies to `maamp`; keep the rest of the chain non-normalized if you started there.
- If you need motif discovery later, recompute a motif-specific profile with `discords=False`.

## 4. One-window debugging with a distance profile
Use the query-window helpers when one row is behaving strangely.

```python
from stumpy.mstump import multi_distance_profile
from stumpy.maamp import maamp_multi_distance_profile

D = multi_distance_profile(query_idx=2, T=T, m=m, include=include, discords=False)
# or:
D = maamp_multi_distance_profile(query_idx=2, T=T, m=m, include=include, discords=False, p=2.0)
```

What to read from the result:
- `D.shape` is `(d, n - m + 1)`.
- Each row is one dimension's contribution for the same query window.
- This is the fastest way to check whether `include` or `discords` is changing the dimension ranking as expected.

## 5. Inclusion workflow
If you need to force one or more dimensions into the answer:
1. Pass `include` to `mstump` or `maamp`.
2. Pass the same `include` to `mdl`, `subspace`, and `mmotifs` / `aamp_mmotifs`.
3. If you really need to exclude a dimension, drop that row from `T` before profiling.

Remember:
- `include` is a zero-based list of dimension indices.
- It is a constraint on dimensions, not on subsequence positions.
- Reusing the same `include` across the full chain avoids invalid or meaningless results.
