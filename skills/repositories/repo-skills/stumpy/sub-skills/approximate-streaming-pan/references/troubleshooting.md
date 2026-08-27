# Troubleshooting Approximate, Streaming, FLOSS, and Pan Workflows

## Symptom-to-fix table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `TypeError` on integer input | STUMPY streaming/approximate tests exercise rejection of integer arrays. | Convert to `np.asarray(T, dtype=np.float64)` before construction. |
| Many `inf` values in `scrump.P_`/`scraamp.P_` | The anytime object has not processed enough diagonals, or invalid subsequences exist. | Call more `.update()` steps, increase `percentage`, enable `pre_scrump`/`pre_scraamp`, and check NaN/inf windows. |
| Approximate motif/discord index changes after every update | Incomplete anytime convergence. | Treat current result as a shortlist only. Continue updates or validate candidates with exact `stump`/`aamp`. |
| `pre_scrump=True` did not make the answer exact | PreSCRIMP is a seeding step, not a completion guarantee. | Increase updates/percentage or run exact matrix-profile workflow. |
| `.update()` appears to do nothing | All chunks/window-size rows may already be processed, or state is being read before updates. | Count requested updates, print finite values in `.P_`, and avoid assuming more than full coverage. For pan profiles, compare processed rows against `len(pmp.M_)`. |
| Streaming output length is not what the user expected | `egress=True` drops the oldest sample; `egress=False` grows history. | Choose egress deliberately and inspect `stream.T_.shape` after each update. |
| Old observations disappear from `stream.T_` | Default `stumpi`/`aampi` behavior is egressing. | Use `egress=False` if full history must remain in state. |
| Memory or latency grows in a stream | `egress=False` grows the series and profile. | Use `egress=True` for fixed-size monitoring, or periodically reinitialize with a bounded window. |
| User passes a vector to `.update(t)` | Streaming update methods expect one scalar observation. | Loop over incoming values: `for t in values: stream.update(float(t))`. |
| `floss` raises an index/shape error during initialization | `mp` is not the full 4-column matrix profile array, or it was computed from different `T`/`m`. | Pass `stumpy.stump(T, m)` or `stumpy.aamp(T, m, p=p)` computed from exactly the same initial `T`. |
| FLOSS `.I_` values look outside the current window | FLOSS right-neighbor indices are in full stream index space, including egressed data. | Use `.T_` for current-window values and interpret `.I_` as historical right-neighbor ids; `-1` means no valid right neighbor. |
| Online segmentation overreacts near the edges | `L` or `excl_factor` masks too little edge area. | Increase `L` or `excl_factor`; route boundary interpretation to the segmentation sub-skill. |
| `stimp`/`aamp_stimp` pan looks blocky | Too few window-size rows have been processed; transformed `.PAN_` repeats available rows. | Call more `.update()` steps and inspect raw `.P_` plus `.M_` before interpreting the view. |
| Candidate window size missing from pan scan | `step` is too large or `min_m`/`max_m` exclude the target scale. | Narrow the range around domain-informed lengths and reduce `step`. |
| `min_m` is too small | Matrix-profile window sizes below ordinary lower bounds are not meaningful and may fail validation. | Use `min_m >= 3`; for exact window checks route to matrix-profile fundamentals. |
| `max_m` seems ignored or swapped | STUMPY sorts provided `min_m`/`max_m` and clamps to feasible maximum sizes. | Print `pmp.M_` immediately after construction and use it as the source of truth. |
| Non-normalized distances disagree with normalized results | `scraamp`, `aampi`, and `aamp_stimp` use raw p-norm distances. | Do not compare these distances directly with z-normalized outputs. Decide normalization based on task semantics. |
| AB-join produces trivial/self matches | `ignore_trivial` is wrong for the join type. | Self-join: omit `T_B`, keep `ignore_trivial=True`. AB-join: pass `T_B` and set `ignore_trivial=False`. |
| Results differ across new anytime object construction | SCRIMP/SCRIMP++ samples randomized diagonal orders. | For reproducible diagnostics, fix STUMPY's RNG state around construction/update; for real decisions, check stability across updates or exact validation. |

## Update-order checklist

Before debugging values, verify this order:

1. Build a 1-D `float64` input array.
2. Choose the object and normalization once.
3. Construct the object with the intended `m`, `percentage`, `pre_*`, and egress/range settings.
4. Call `.update()` or `.update(t)` the required number of times.
5. Read object properties after updates, not before.
6. Route downstream motif/discord/segment interpretation to the owning sub-skill.

## Egress state checklist

For `stumpi`/`aampi`:

- `egress=True`: `len(stream.T_)` remains equal to the initial length; indices refer to the current rolling state.
- `egress=False`: `len(stream.T_)` increases by one after each update; historical subsequences stay searchable.
- `.left_P_`/`.left_I_` only consider left/historical nearest neighbors and are useful for online novelty logic.

For `floss`:

- FLOSS always performs ingress plus egress.
- `.T_` is the current sliding time series.
- `.cac_1d_` is the online corrected arc curve; low values are candidate regime boundaries, not final interpretation by themselves.

## Pan-state checklist

For `stimp`/`aamp_stimp`:

- Print `pmp.M_` to learn the processed window-size order.
- Track how many raw `.P_` entries contain finite values.
- Use raw `.P_` for analytical comparisons; use `.PAN_`/`.pan(...)` for transformed visualization.
- Re-run a narrower exact or higher-percentage scan before committing to a window size.
