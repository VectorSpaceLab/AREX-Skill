# Troubleshooting motifs, matches, chains, snippets, and segmentation

Use this reference when an analysis API runs but returns empty, surprising, or hard-to-interpret results. If profile computation itself fails, route to `matrix-profile-basics` first.

## Column and input checklist

| API | Correct input | Common wrong input |
| --- | --- | --- |
| `motifs(T, P, ...)` | raw 1-D `T` plus 1-D profile distances `P = mp[:, 0]` or `mp.P_` | full `mp` array, index column, raw `T` only |
| `match(Q, T, ...)` | raw query `Q` and raw target `T` | matrix profile `P` instead of the target series |
| `mmotifs(T, P, I, ...)` | multidimensional raw `T` plus multidimensional `P` and `I` | ordinary 1-D `P`, wrong row/column orientation |
| `ostinato(Ts, m, ...)` | list of raw 1-D series | concatenated profile arrays or a 2-D feature matrix |
| `mpdist(T_A, T_B, m, ...)` | two raw 1-D series | precomputed profile only |
| `snippets(T, m, k, ...)` | raw 1-D `T` | profile distances instead of the series |
| `atsc(IL, IR, j)` | left and right index columns `mp[:, 2]`, `mp[:, 3]` | `mp[:, 0]` or `mp[:, 1]` |
| `allc(IL, IR)` | left and right index columns | profile distances or nearest-neighbor index only |
| `fluss(I, L, n_regimes, ...)` | nearest-neighbor index column `mp[:, 1]` or `mp.I_` | profile distances `mp[:, 0]` |
| `floss(mp, T, m, L, ...)` | full 4-column `mp` plus raw `T` | only the `P` or `I` vector |

## Thresholds, `max_distance`, and `max_matches`

Symptoms:
- `motifs` returns no rows or fewer rows than `max_motifs`.
- `match` returns only the query itself or fewer occurrences than expected.
- The first motif is plausible but additional motifs are missing.

Likely causes:
- `max_distance` is too strict.
- `cutoff` is too low for the profile values.
- `min_neighbors` is too high for the number of repeated subsequences.
- `max_matches` clips the returned rows.
- Neighboring matches are hidden by the exclusion zone around each selected match.

Fixes:
- For exploration, temporarily use `cutoff=np.inf`, a larger `max_distance`, and a small `min_neighbors`, then tighten after checking results.
- Use `max_matches=None` when you need every match that passes the threshold.
- If using a callable `max_distance`, ensure it accepts one argument, the distance profile `D`, and returns a scalar threshold.
- For AB-join-style query matching, leave `query_idx=None`; use `query_idx` only when `Q` is a subsequence of the same `T`.

## Motif / discord interpretation looks wrong

Symptoms:
- The lowest profile value points to an uninteresting flat region.
- The highest profile value is at an edge or around missing data.
- Peaks and valleys move when `m` changes.

Fixes:
- Check that `m` captures the actual pattern duration; a wrong window size can make both motifs and discords meaningless.
- Inspect nearby local minima / maxima, not only the single global extremum.
- For guided motif search, build an annotation vector with the same length as `P` and use `corrected_P = P + (1 - AV) * np.nanmax(P)` before `motifs`.
- Treat profile maxima as candidate discords, then confirm against domain context and raw subsequence plots or statistics.

## Segmentation with FLUSS / FLOSS

Symptoms:
- `fluss` returns a boundary at the edge.
- The regime location is far from the visible change point.
- `floss` updates but `cac_1d_` is flat or unstable.

Likely causes and fixes:
- Wrong column: `fluss` needs `mp[:, 1]`, not `mp[:, 0]`.
- Wrong regime count: `n_regimes` is one more than the number of boundaries. For one boundary, use `n_regimes=2`.
- Poor `L`: choose `L` near a natural period or motif duration. Too-small `L` makes the corrected arc curve noisy; too-large `L` can hide short regimes.
- Over-aggressive `excl_factor`: large values suppress edge artifacts but can also mask real nearby boundaries. Try a smaller value such as `1` for tiny synthetic data.
- FLOSS input mismatch: initialize `floss` with the full 4-column matrix profile and the raw initial `T` produced with the same `m` and normalization mode.

## Constant, clipped, NaN, or infinite data

Symptoms:
- Many zero distances appear for flat subsequences.
- Constant regions dominate the motif output.
- `mpdist`, `match`, or `snippets` behave unexpectedly around missing values.

Fixes:
- Constant subsequences are special: when normalized, two constant subsequences may have distance `0`, while a constant-vs-nonconstant pair may behave like a `sqrt(m)` distance case.
- Provide `T_subseq_isconstant`, `Q_subseq_isconstant`, `Ts_subseq_isconstant`, or `T_subseq_isconstant_func` when the default constant-subsequence detection is not right for clipped or domain-specific data.
- Do not treat NaN/inf-heavy regions as reliable anomalies without inspecting which subsequences were finite.
- If an undesirable but finite region should be penalized rather than removed, use an annotation vector and corrected profile.

## Normalized vs non-normalized routing

Symptoms:
- Downstream motifs or matches disagree with profile minima.
- `p` appears to have no effect.
- A non-normalized profile gives poor FLUSS / chain results after a normalized call.

Fixes:
- Keep the normalization mode consistent end to end.
- If the profile came from `stumpy.stump`, use default `normalize=True` in `motifs`, `match`, `ostinato`, `mpdist`, and `snippets`.
- If the profile came from `stumpy.aamp` or another non-normalized route, pass `normalize=False` and the same `p` where supported.
- Remember that `p` is ignored when `normalize=True`.
- `atsc`, `allc`, and `fluss` do not take `normalize` because they use already-computed index arrays; the upstream profile still determines those indices.

## MPdist and snippets surprises

Symptoms:
- MPdist says two series are similar even though the order differs.
- `snippets` raises a window-size error or returns unexpected regimes.

Fixes:
- MPdist intentionally ignores the order of matching subsequences; use another method if temporal order must be preserved.
- For `mpdist`, `k` overrides `percentage`.
- For `snippets`, ensure `m <= len(T) // 2` and choose `k` small enough to inspect manually.
- In `snippets`, `s` overrides `percentage`; `mpdist_k` overrides `mpdist_percentage` inside the MPdist subroutine.

## Multidimensional `mmotifs` handoff issues

Symptoms:
- `mmotifs` returns surprising dimensions or no motifs.
- The `include` constraint seems ignored or over-constraining.

Fixes:
- Verify the upstream multidimensional profile orientation: rows are dimensions and columns are time.
- Ensure `P` and `I` came from the same `mstump` / `maamp` call and window size.
- Relax `cutoffs`, `max_distance`, and `include` before concluding no motif exists.
- Route detailed subspace, MDL, and multidimensional profile debugging to `multidimensional-profiles`.
