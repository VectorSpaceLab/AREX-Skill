# API reference

This reference covers the 1-D basic profile path only.

## Public signatures

```python
stumpy.stump(T_A, m, T_B=None, ignore_trivial=True, normalize=True, p=2.0, k=1, T_A_subseq_isconstant=None, T_B_subseq_isconstant=None)
stumpy.aamp(T_A, m, T_B=None, ignore_trivial=True, p=2.0, k=1)
stumpy.mass(Q, T, M_T=None, Σ_T=None, normalize=True, p=2.0, T_subseq_isfinite=None, T_subseq_isconstant=None, Q_subseq_isconstant=None, query_idx=None)
```

## What each API returns

| API | Main use | Return type | Shape / layout | Notes |
| --- | --- | --- | --- | --- |
| `stump` | Z-normalized 1-D matrix profile | `mparray` | `len(T_A) - m + 1` rows; `2 * k + 2` columns | Self-join by default. AB-join when `T_B` is provided with `ignore_trivial=False`. `p` is ignored while `normalize=True`. |
| `aamp` | Raw 1-D matrix profile | `mparray` | Same layout as `stump` | Non-normalized path. `p` is honored. |
| `mass` | Distance profile for one query | `numpy.ndarray` | `len(T) - m + 1` float64 values | Returns a distance profile, not a profile object. `query_idx` is optional when `Q` is a known subsequence of `T`. |

## Matrix-profile object layout

For `stump` and `aamp`, the returned object is an object-dtype `mparray`.

- `k = 1` rows are laid out as `[P, I, left_I, right_I]`.
- `k > 1` rows are laid out as `[P_1, ..., P_k, I_1, ..., I_k, left_I, right_I]`.
- `P_` returns the profile distances as `float64`.
- `I_` returns the nearest-neighbor indices as `int64`.
- `left_I_` and `right_I_` return the top-1 left/right indices.
- For AB-joins, left/right indices are sentinel `-1` values.

Use the named properties for interpretation instead of assuming the whole object can be treated as one numeric matrix.

## Parameter semantics

### `ignore_trivial`

- `True` means self-join semantics with an exclusion zone.
- `False` means AB-join semantics.
- If the chosen setting does not match the input relationship, STUMPY may warn and auto-correct it.

### `normalize`

- `stump(..., normalize=True)` computes the z-normalized profile.
- `stump(..., normalize=False)` routes to the raw-distance implementation.
- `mass(..., normalize=True)` computes the z-normalized distance profile.
- `mass(..., normalize=False)` routes to the raw-distance implementation.
- `aamp` has no `normalize` argument because it is already the raw-distance API.

### `p`

- `p` is the Minkowski norm for raw-distance calculations.
- It is typically `1.0` or `2.0`.
- It is ignored when the normalized path is active.

### Constant subsequence flags

- `T_A_subseq_isconstant`, `T_B_subseq_isconstant`, and `Q_subseq_isconstant` can be boolean arrays or callables for exact profile computations.
- Any subsequence containing `NaN` or `inf` is automatically treated as non-constant.
- These flags are used for normalized logic; raw-distance paths rely on finite-value masks.

### `query_idx`

- Use `query_idx` only when `Q` is a known subsequence of `T`.
- It zeros the self-distance at the matching index and helps confirm the query alignment.
- If the slice does not match the provided query, STUMPY warns.

## Input handling

- `check_dtype` requires floating-point arrays for these basic APIs.
- pandas and polars `Series` are accepted and converted to NumPy.
- DataFrames are transposed before conversion, so a one-column DataFrame is not the preferred 1-D input shape.
- If the input is not 1-D after preprocessing, the 1-D APIs raise a dimension error and you should route to the multidimensional skill instead.

## Finite and constant subsequences

- A subsequence containing `NaN` or `inf` is marked non-finite.
- Non-finite subsequences produce `inf` distances.
- Normalized constant subsequences are handled specially rather than treated as ordinary numeric windows.
- A large number of tiny distances in a self-join usually means you should re-check `ignore_trivial`, periodicity, or the chosen window size.

## Routing boundaries

Route out of this skill when the request is really about:

- multidimensional profile shapes or dimension selection -> `multidimensional-profiles`
- motifs, matches, discords, snippets, or segmentation -> `motifs-anomalies-segmentation`
- approximate, streaming, or pan profiles -> `approximate-streaming-pan`
- Dask, Ray, or CUDA execution -> `distributed-gpu-acceleration`

## Evidence summary

This reference was distilled from the public STUMPY basics and AB-join guidance, the public API surface, the matrix-profile object implementation, and the installed function signatures for `stump`, `aamp`, and `mass`.
