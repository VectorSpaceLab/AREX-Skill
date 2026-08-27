# Workflows for Approximate, Streaming, Online Segmentation, and Pan Profiles

## Choose the right workflow

| User intent | Use | Route elsewhere when |
| --- | --- | --- |
| Need a quick, progressively refinable matrix profile | `scrump` / `scraamp` | They need exact profile fundamentals or final exact distances. |
| Need to add one observation at a time | `stumpi` / `aampi` | They are recomputing a static batch profile or using multidimensional data. |
| Need an online segmentation curve over a fixed sliding window | `floss` | They need interpretation of segment boundaries rather than update mechanics. |
| Need to explore multiple candidate window sizes | `stimp` / `aamp_stimp` | They need Dask/GPU acceleration or exact single-window motifs. |

Always convert ordinary numeric input to a 1-D floating array before these APIs. Integer arrays commonly fail validation; object arrays lead to confusing downstream behavior.

## Anytime approximate matrix profile

Use this when an early approximate profile is useful and can be refined with more updates.

```python
T = np.asarray(T, dtype=np.float64)
m = 50
approx = stumpy.scrump(T, m, percentage=0.01, pre_scrump=True)
for _ in range(10):
    approx.update()
P, I = approx.P_, approx.I_
```

Decision points:

1. **Self-join or AB-join**
   - Self-join: `stumpy.scrump(T, m, ignore_trivial=True)`.
   - AB-join: `stumpy.scrump(T_A, m, T_B=T_B, ignore_trivial=False)`.
2. **Normalized or non-normalized**
   - Use `scrump` for z-normalized shape matching.
   - Use `scraamp` or `scrump(..., normalize=False, p=...)` for raw p-norm distances.
3. **Budget**
   - `percentage=0.01` means roughly one percent of the distance work per update.
   - Larger `percentage` converges in fewer updates but each update is more expensive.
   - `percentage=1.0` is effectively full coverage after one update; if exactness matters, prefer exact `stump`/`aamp` guidance.
4. **Preprocessing seed**
   - `pre_scrump=True` / `pre_scraamp=True` performs a PreSCRIMP seed before updates and often improves early minima.
   - `s` controls the PreSCRIMP fixed interval; leave `None` unless you have a reason to tune sampling.

Stop when one of these is true:

- the candidate motif/discord indices remain stable across several updates;
- the downstream task only needs a shortlist for later exact verification;
- the interactive budget is exhausted and uncertainty is reported.

Do **not** treat a low-percentage approximate profile as exact. Use approximate results for screening, visualization, monitoring, or candidate generation. Avoid them for strict thresholds, close rankings, publication-grade distances, or high-cost missed detections unless you validate selected candidates with exact profiles.

## Streaming incremental profile

Use this when observations arrive sequentially.

```python
T0 = np.asarray(initial_history, dtype=np.float64)
stream = stumpy.stumpi(T0, m=50, egress=True)
for t in incoming_values:
    stream.update(float(t))
current_T = stream.T_
P, I = stream.P_, stream.I_
left_P, left_I = stream.left_P_, stream.left_I_
```

Decision points:

- `egress=True` keeps memory and output length fixed by dropping the oldest sample at each update. This is best for rolling-window monitoring.
- `egress=False` grows history and lets old subsequences remain candidates. This is best when the full historical stream must remain searchable.
- `.left_P_`/`.left_I_` are useful when the newest subsequence should only be compared to earlier subsequences. This can support online anomaly screening without rewriting past nearest-neighbor decisions.
- Use `aampi(..., p=...)` or `stumpi(..., normalize=False, p=...)` when raw amplitude is meaningful.
- If supplying `mp=...`, compute it from exactly the same initial `T`, window `m`, normalization choice, and `k`; its expected shape is `(len(T) - m + 1, 2*k + 2)`.

Update rules:

- Feed exactly one scalar per `.update(t)` call.
- Preserve arrival order.
- Read `.T_`, `.P_`, and `.I_` after each update when making online decisions.
- Reinitialize only when the window size, normalization choice, or initial-history assumptions change.

## FLOSS online segmentation mechanics

Use this when the user wants an online corrected arc curve over a sliding window. This sub-skill covers the update mechanics; route segment-boundary interpretation to the segmentation sub-skill.

```python
old_data = np.asarray(old_data, dtype=np.float64)
mp = stumpy.stump(old_data, m)
stream = stumpy.floss(mp, old_data, m=m, L=m, excl_factor=1)
for t in incoming_values:
    stream.update(float(t))
    cac = stream.cac_1d_
```

Key points:

- `mp` must be the full output from `stump` or `aamp`; FLOSS uses right matrix-profile indices internally.
- FLOSS always performs ingress plus egress, so `stream.T_` is a fixed-size sliding window.
- `L` controls edge-effect handling for the corrected arc curve. It is often close to a period length or the profile window size, but it is not the same thing as the matrix-profile exclusion zone.
- Smaller `excl_factor` exposes boundaries nearer the edges; larger values mask more edge area.
- For deterministic lightweight checks, reduce `n_iter`/`n_samples` or provide a validated `custom_iac`; for real analysis, use a stable curve choice and document it.

## Pan matrix profile / selecting window sizes

Use this when the user does not know the best subsequence window size and wants a broad scan.

```python
T = np.asarray(T, dtype=np.float64)
pmp = stumpy.stimp(T, min_m=20, max_m=200, step=5,
                   percentage=0.01, pre_scrump=True)
for _ in range(25):
    pmp.update()
window_order = pmp.M_
raw_profiles = pmp.P_
view = pmp.PAN_
```

Decision points:

1. **Candidate range**
   - Start with domain knowledge if available: period length, expected motif duration, or sample-rate conversion.
   - Keep `min_m >= 3`; if `min_m` is too small, distances often become uninformative and some routines may reject the window.
   - Set `max_m` no larger than the useful motif scale; STUMPY clamps to feasible bounds, but an overly broad range wastes updates.
2. **Resolution**
   - `step=1` is detailed but expensive.
   - Larger steps are useful for coarse scans but may skip the best length.
3. **Approximation budget**
   - `percentage < 1.0` uses `scrump`/`scraamp` inside each row.
   - `percentage=1.0` computes exact per-window rows and is slower.
4. **Read state correctly**
   - `.M_` is breadth-first-ordered, not numerically sorted.
   - `.P_` is a list of raw profile rows in `.M_` order.
   - `.PAN_` is transformed for visualization; use `.pan(...)` to control normalization, contrast, binarization, and clipping.
   - Rows not processed yet are extrapolated/repeated in transformed views and may look blocky. Call more `.update()` steps before drawing conclusions.

A practical scan-and-validate loop:

1. Run `stimp`/`aamp_stimp` with a coarse `step` and a low `percentage`.
2. Call `.update()` until multiple window-size rows are processed.
3. Look for stable low-distance bands in raw profiles and map them back through `.M_`.
4. Re-run a narrower pan scan around candidate windows with a smaller `step` or higher `percentage`.
5. Validate selected windows using exact profile/motif workflows before making final claims.

## When approximate results are acceptable

Approximate results are acceptable when they are used to:

- rank or shortlist candidate motif/discord locations before exact verification;
- monitor a stream where immediate approximate alerts are better than delayed exact recomputation;
- choose a rough window-size range before a focused exact pass;
- visualize large-scale structure where small distance differences do not change the decision.

Approximate results are not enough when:

- the decision depends on close distance ties or hard thresholds;
- false negatives are costly;
- a report claims exact matrix-profile distances;
- a pan matrix profile has too few processed rows or changes materially after each update.
