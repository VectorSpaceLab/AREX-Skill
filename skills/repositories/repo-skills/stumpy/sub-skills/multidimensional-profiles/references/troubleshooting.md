# Troubleshooting

## Wrong orientation
**Symptom:** The profile looks nonsensical, or the number of dimensions and time points feel swapped.

**Cause:** `T` is shaped like `(n, d)` instead of `(d, n)`.

**Fix:** Transpose the array so that rows are dimensions and columns are time. If you are starting from a table-like object, make sure you end up with one row per dimension before calling STUMPY.

## Integer or object dtype
**Symptom:** A type error complains about the array dtype.

**Cause:** The multidimensional profile functions expect floating-point input, not integers or mixed object columns.

**Fix:** Convert to `np.float64` before calling `mstump` or `maamp`.

## Window-size errors
**Symptom:** The call fails with a window-size `ValueError`, or the window feels obviously too large.

**Cause:** `m` must be at least `3`, and it must not exceed the length of the time axis.

**Fix:** Use `m >= 3` and `m <= n`. If the series is short, reduce `m`.

## `include` does not behave as expected
**Symptom:** The chosen subspace is not the one you meant to force.

**Cause:** `include` was changed in one call but not reused in the downstream calls, or the indices were interpreted as time positions instead of dimensions.

**Fix:**
- Treat `include` as zero-based dimension indices.
- Pass the same `include` to `mstump` / `maamp`, `mdl`, `subspace`, and `mmotifs` / `aamp_mmotifs`.
- If you want to exclude a dimension outright, remove that row from `T` before profiling.
- If you pass duplicate indices, STUMPY removes them and warns.

## `discords=True` is mixed with motif logic
**Symptom:** The result looks inverted or the motif handoff is meaningless.

**Cause:** A discord-specific profile was selected with `discords=True`, but the next step used motif logic.

**Fix:**
- Use `np.argmax(P, axis=1)` for discord candidates.
- Keep `discords=True` on `subspace` and `mdl` when you are exploring discords.
- Do not feed a discord-specific profile into `mmotifs` or `aamp_mmotifs`.
- If you want motifs later, recompute the profile with `discords=False`.

## Mixed normalized and non-normalized calls
**Symptom:** The selected dimensions do not match the profile that produced them.

**Cause:** `mstump` output was combined with non-normalized downstream calls, or `maamp` output was combined with normalized downstream calls.

**Fix:** Keep the full chain in one family:
- Normalized: `mstump` -> `mdl` -> `subspace` -> `mmotifs`
- Non-normalized: `maamp` -> `mdl(normalize=False)` -> `subspace(normalize=False)` -> `aamp_mmotifs`

## Interpreting `P`, `I`, and `k`
**Symptom:** The returned arrays do not seem to match the verbal description of the motif.

**Cause:** The zero-based row convention is easy to miss.

**Fix:**
- Row `0` is the 1-D profile.
- Row `1` is the 2-D profile.
- In general, row `k` is the `(k + 1)`-dimensional profile.
- `subspace(..., k)` returns `k + 1` dimensions, not one dimension.
- `mdl` returns one bit-size per row and `np.argmin(mdls)` is the usual best-k choice.

## Constant or invalid windows
**Symptom:** The profile has unexpected infinities or flat distances.

**Cause:** Constant subsequences or NaN / Inf windows need special handling.

**Fix:** Clean the data first when possible. If you need custom constant handling on the normalized path, supply a matching `T_subseq_isconstant` object. For non-normalized work, the finite-mask handling happens inside the preprocessing path.

## Need to inspect one query window
**Symptom:** You cannot tell which dimension is causing a strange profile row.

**Fix:** Use `multi_distance_profile` or `maamp_multi_distance_profile` on a single `query_idx` before you change the full profile chain.
