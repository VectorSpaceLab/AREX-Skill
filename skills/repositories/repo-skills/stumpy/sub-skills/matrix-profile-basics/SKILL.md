---
name: matrix-profile-basics
description: "Compute and validate 1-D STUMPY matrix profiles and distance
  profiles, including normalized and non-normalized routes, AB-joins, top-k
  output, pandas/polars inputs, and profile interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# STUMPY matrix-profile basics

Use this sub-skill for 1-D profile computation, inspection, and smoke validation with `stumpy.stump`, `stumpy.aamp`, and `stumpy.mass`.

Do not use it for:
- multidimensional profiles or subspace selection -> `multidimensional-profiles`
- motifs, matches, discords, snippets, or segmentation -> `motifs-anomalies-segmentation`
- approximate, streaming, or pan profiles -> `approximate-streaming-pan`
- Dask, Ray, or CUDA setup -> `distributed-gpu-acceleration`

## Fast routing

- **Z-normalized matrix profile:** `stumpy.stump(T_A, m, ...)`
- **Raw matrix profile:** `stumpy.aamp(T_A, m, ...)`
- **Distance profile:** `stumpy.mass(Q, T, ...)`
- **AB-join:** pass `T_B` and set `ignore_trivial=False`
- **Top-k results:** set `k > 1` and read the `mparray` attributes

## Input rules

- Use floating-point inputs, usually `np.float64`, pandas `Series`, or polars `Series`.
- Keep 1-D inputs 1-D. DataFrames are transposed before conversion and are better suited to multidimensional workflows.
- Window size must be at least 3 and no larger than the shortest input series.
- Self-joins use `ignore_trivial=True`; AB-joins use `ignore_trivial=False`.
- If you already know constant subsequences, you can supply `T_A_subseq_isconstant` / `T_B_subseq_isconstant` / `Q_subseq_isconstant` to the exact API.
- If the task turns into motifs, matches, discords, snippets, or segmentation, stop after the profile and route out.

## Runtime handoff

- Verify the install/import path with `scripts/profile_smoke.py`.
- Default smoke command: `python scripts/profile_smoke.py --mode exact`
- Use `--mode ab-join`, `--mode aamp`, or `--mode mass` for the other basic routes.
- The smoke script uses tiny synthetic data only and does not touch the network or any files.

## Read the profile

- `stump` and `aamp` return an object-dtype `mparray`.
- For `k = 1`, each row stores `[P, I, left_I, right_I]`.
- Use `mp.P_`, `mp.I_`, `mp.left_I_`, and `mp.right_I_` instead of slicing when possible.
- Negative indices mean no eligible neighbor was found.
- `mass` returns a `float64` distance profile, not a matrix-profile object.
- If you need to interpret motifs or follow-on pattern matches, route to the downstream analysis sub-skill.

## Normalize or not

- `stump(..., normalize=False)` routes to the raw-distance implementation.
- `mass(..., normalize=False)` routes to the raw-distance implementation.
- `p` is only meaningful for non-normalized distance calculations.
