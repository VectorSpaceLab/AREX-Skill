---
name: multidimensional-profiles
description: "Route multidimensional matrix-profile, subspace, and MDL requests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Multidimensional Profiles

Use this sub-skill for multidimensional matrix profiles, dimension ranking, and subspace selection.

## Route here when
- The input is a multidimensional series with shape `(d, n)` and `d > 1`.
- The user wants `mstump`, `maamp`, `multi_distance_profile`, `subspace`, or `mdl`.
- The user needs to interpret row-wise profile output or an `include`-constrained search.
- The user wants to hand off a multidimensional profile to `mmotifs` or `aamp_mmotifs`.

## Route away when
- Route 1-D matrix-profile basics, dtype checks, or window-size setup to matrix-profile-basics.
- Route Dask distributed `mstumped` / `maamped` setup or GPU backend setup to distributed-gpu-acceleration.
- Route general motif, anomaly, or segmentation interpretation after profiling to motifs-anomalies-segmentation.

## Operating rules
1. Treat rows as dimensions and columns as time.
2. Keep the array in `float64` form before calling STUMPY.
3. Use `mstump` for normalized distances and `maamp` for non-normalized distances.
4. Keep `include` and `discords` consistent across profile, subspace, MDL, and motif handoff calls.
5. Read row `k` in `P` / `I` as the `(k + 1)`-dimensional profile.
6. Use `np.argmin(P, axis=1)` for motifs and `np.argmax(P, axis=1)` for discords.
7. Use `mmotifs` / `aamp_mmotifs` only after the dimension choice is settled and only with motif-oriented profiles.

## Fast path
- Confirm the layout and dtype.
- Compute `P, I = stumpy.mstump(...)` or `P, I = stumpy.maamp(...)`.
- Inspect `P.shape` and `I.shape`; both should be `(d, n - m + 1)`.
- Pick candidate subsequences row-wise.
- Inspect a single query window with `multi_distance_profile` if one row needs debugging.
- Use `mdl` or `subspace` to choose the dimensions.
- Hand off to `mmotifs` or `aamp_mmotifs` only when you need the motif-match layer.

## Bundled files
- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/multidim_smoke.py`
