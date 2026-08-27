# Approximate, Streaming, FLOSS, and Pan API Reference

This reference is distilled for runtime use and does not require access to the STUMPY source checkout. All examples assume `import numpy as np` and `import stumpy`.

## Normalized versus non-normalized routing

| Need | Z-normalized choice | Non-normalized p-norm choice | Notes |
| --- | --- | --- | --- |
| Anytime approximate profile | `stumpy.scrump(...)` | `stumpy.scraamp(...)` or `stumpy.scrump(..., normalize=False, p=...)` | Read `.P_`/`.I_` after one or more `.update()` calls. |
| PreSCRIMP-only profile | `stumpy.prescrump(...)` | `stumpy.prescraamp(...)` | Returns `(P, I)` directly; no update object. |
| Streaming incremental profile | `stumpy.stumpi(...)` | `stumpy.aampi(...)` or `stumpy.stumpi(..., normalize=False, p=...)` | Call `.update(t)` once per scalar observation. |
| Online segmentation state | `stumpy.floss(mp, T, m, L, normalize=True)` | `stumpy.floss(mp, T, m, L, normalize=False, p=...)` | Requires a full matrix profile array from `stump`/`aamp`, not only the distance column. |
| Pan matrix profile | `stumpy.stimp(...)` | `stumpy.aamp_stimp(...)` or `stumpy.stimp(..., normalize=False, p=...)` | Call `.update()` once per window-size row. |

## Anytime approximate matrix profile

### `scrump`

Signature:

```python
stumpy.scrump(
    T_A,
    m,
    T_B=None,
    ignore_trivial=True,
    percentage=0.01,
    pre_scrump=False,
    s=None,
    normalize=True,
    p=2.0,
    k=1,
    T_A_subseq_isconstant=None,
    T_B_subseq_isconstant=None,
)
```

Behavior:

- Returns an anytime object, not the final profile array.
- Call `.update()` to compute the next chunk of diagonal distances. The amount per update is controlled by `percentage`.
- Read `.P_` for the approximate matrix profile and `.I_` for nearest-neighbor indices. With `k=1`, these are 1-D arrays; with `k>1`, they are `(n - m + 1, k)` arrays.
- `.left_I_` and `.right_I_` expose top-1 left/right nearest-neighbor indices.
- For self-joins, omit `T_B` and keep `ignore_trivial=True`. For AB-joins, pass `T_B` and set `ignore_trivial=False`.
- `pre_scrump=True` runs a PreSCRIMP seed before SCRIMP updates; it can improve early approximations but does not make a low-percentage result exact.
- If `percentage=1.0`, one update can cover the full distance matrix; when exactness is the goal, route to the exact profile skill and consider `stump` instead.

Minimal pattern:

```python
T = np.asarray(T, dtype=np.float64)
approx = stumpy.scrump(T, m, percentage=0.05, pre_scrump=True)
for _ in range(5):
    approx.update()
P = approx.P_
I = approx.I_
```

### `scraamp`

Signature:

```python
stumpy.scraamp(
    T_A,
    m,
    T_B=None,
    ignore_trivial=True,
    percentage=0.01,
    pre_scraamp=False,
    s=None,
    p=2.0,
    k=1,
)
```

Use this when raw amplitude and a Minkowski p-norm matter more than z-normalized shape. Outputs and update behavior match `scrump`, but distances are not normalized and therefore scale with signal amplitude. Typical `p` values are `1.0` and `2.0`.

### `prescrump` and `prescraamp`

Signatures:

```python
stumpy.prescrump(T_A, m, T_B=None, s=None, normalize=True, p=2.0, k=1,
                 T_A_subseq_isconstant=None, T_B_subseq_isconstant=None)
stumpy.prescraamp(T_A, m, T_B=None, s=None, p=2.0, k=1)
```

These return `(P, I)` directly from the PreSCRIMP stage. Use them for a standalone fast seed or diagnostic, not for iterative refinement. For `pre_scrump=True`/`pre_scraamp=True`, the anytime classes use the same idea internally before their `.update()` loop.

## Streaming incremental profiles

### `stumpi`

Signature:

```python
stumpy.stumpi(
    T,
    m,
    egress=True,
    normalize=True,
    p=2.0,
    k=1,
    mp=None,
    T_subseq_isconstant_func=None,
)
```

Object attributes and methods:

- `.update(t)`: append one scalar observation and update profile state.
- `.P_`, `.I_`: current top-k matrix profile distances and nearest-neighbor indices.
- `.left_P_`, `.left_I_`: current left profile and left indices; useful when the newest subsequence should only look backward.
- `.T_`: current time series state.

Important parameters:

- `egress=True` keeps a fixed-length sliding window by dropping the oldest observation on each update. This is the default.
- `egress=False` grows the time series and preserves the full history.
- `mp` may provide a precomputed matrix profile of shape `(len(T) - m + 1, 2*k + 2)`. If omitted, STUMPY computes it internally.
- `normalize=False` reroutes to the non-normalized implementation and uses `p`.

### `aampi`

Signature:

```python
stumpy.aampi(T, m, egress=True, p=2.0, k=1, mp=None)
```

This is the non-normalized streaming counterpart. It has the same `.update(t)`, `.P_`, `.I_`, `.left_P_`, `.left_I_`, and `.T_` usage pattern. Use it when raw p-norm distances are intended.

## Online segmentation state with `floss`

Signature:

```python
stumpy.floss(
    mp,
    T,
    m,
    L,
    excl_factor=5,
    n_iter=1000,
    n_samples=1000,
    custom_iac=None,
    normalize=True,
    p=2.0,
    T_subseq_isconstant_func=None,
)
```

Use FLOSS when the user already has an initial batch profile and wants a streaming corrected arc curve for a fixed-size sliding window.

Inputs and state:

- `mp` must be the full matrix profile array with columns for profile, profile index, left index, and right index. Pass the result of `stumpy.stump(T, m)` or `stumpy.aamp(T, m)`, not just `mp[:, 0]`.
- `T` must be the same time series used to compute `mp`.
- `m` is the matrix-profile window size; `L` controls arc-curve edge effects and is often set near the period/window scale.
- `.update(t)` ingresses one scalar and egresses the oldest scalar.
- `.cac_1d_` is the online 1-D corrected arc curve. `.P_` and `.I_` expose the streaming right matrix profile state. `.T_` is the current sliding time window.
- `.I_` values are right-neighbor indices in the full stream index space, including egressed data; `-1` means no valid right neighbor.

For non-normalized profiles, initialize `mp = stumpy.aamp(T, m, p=p)` and call `stumpy.floss(mp, T, m, L, normalize=False, p=p)`.

## Pan matrix profile / window-size exploration

### `stimp`

Signature:

```python
stumpy.stimp(
    T,
    min_m=3,
    max_m=None,
    step=1,
    percentage=0.01,
    pre_scrump=True,
    normalize=True,
    p=2.0,
    T_subseq_isconstant_func=None,
)
```

Object attributes and methods:

- `.update()`: compute the next matrix profile row for the next breadth-first-ordered window size.
- `.M_`: window sizes in the order STUMPY processes them.
- `.P_`: list of raw, untransformed matrix profile arrays for each window size in `.M_` order. Rows not yet processed contain `inf` values.
- `.PAN_`: default transformed pan matrix profile with normalization, contrast, binarization, clipping, and repeated rows.
- `.pan(threshold=0.2, normalize=True, contrast=True, binary=True, clip=True)`: explicit transformed view.

Important parameters:

- `min_m` is the smallest candidate window size; use `min_m >= 3` for ordinary pan profiles.
- `max_m=None` asks STUMPY to use its maximum allowable size for the series. If both `min_m` and `max_m` are supplied, STUMPY sorts them and clamps to feasible bounds.
- `step` is the increment between candidate window sizes. Large steps may skip the useful motif length.
- `percentage < 1.0` uses `scrump` per window-size row. `percentage=1.0` uses exact `stump` per row.
- `pre_scrump=True` seeds approximate rows before SCRIMP updates; ignored when `percentage=1.0`.

### `aamp_stimp`

Signature:

```python
stumpy.aamp_stimp(T, min_m=3, max_m=None, step=1, percentage=0.01,
                  pre_scraamp=True, p=2.0)
```

This is the non-normalized pan counterpart. The object interface matches `stimp`; `percentage < 1.0` uses `scraamp`, and `percentage=1.0` uses exact `aamp` per candidate window size. Use the default `p=2.0` unless you have independently checked alternate-p behavior in the installed STUMPY version.

## Acceleration boundary

Distributed `stimped`/`aamp_stimped` and GPU `gpu_stimp`/`gpu_aamp_stimp` share pan semantics but add client/device lifecycle, dependency, and hardware requirements. Route those tasks to `../distributed-gpu-acceleration/` and keep this sub-skill focused on local CPU API semantics.
