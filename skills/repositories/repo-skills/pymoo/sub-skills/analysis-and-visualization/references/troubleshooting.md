# Troubleshooting Analysis and Visualization

Use this file when metrics, selection, reference directions, convergence curves,
or plots produce surprising values or errors.

## Indicator and Pareto-front mistakes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `For Hypervolume a reference point needs to be provided!` | `HV()` was created without `ref_point` and without a Pareto front from which pymoo can derive one. | Pass `HV(ref_point=np.array([...]))`. Prefer an explicit reference point that is worse than every relevant minimization objective value. |
| Hypervolume is zero, tiny, or counterintuitive | The reference point is not dominated by the front, objective signs are wrong, or normalized and raw coordinates were mixed. | Confirm all objectives are minimization objectives. Check `np.all(F <= ref_point, axis=1)` for the relevant rows after applying the same normalization convention. |
| Hypervolume changes after passing `ideal`/`nadir` | `zero_to_one=True` normalizes `F`; by default `norm_ref_point=True` also normalizes `ref_point`. | If `ref_point` is already in normalized coordinates such as `[1.1, 1.1]`, use `norm_ref_point=False`. If it is raw, let pymoo normalize it and provide raw `ideal`/`nadir`. |
| `GD`, `IGD`, or epsilon errors with missing `pf` | These indicators compare against a true or accepted approximate Pareto front. | Provide `pf` with the same objective dimension, use `problem.pareto_front()` when available, build and label an approximation, or switch to HV/history analysis when no front exists. |
| Distance metrics look dominated by one objective | Objective scales differ strongly. | Use a common normalization, or pass `zero_to_one=True` with consistent `pf`/`ideal`/`nadir`. For MCDM, normalize before ranking. |
| Multiplicative epsilon gives invalid or meaningless values | Multiplicative ratios are not meaningful with zero or negative objective values. | Shift the compared objective values into a strictly positive range, or use additive epsilon. |
| Metric accepts a single row but later code breaks | A 1-D `F` row was mixed with 2-D matrices. | Normalize inputs explicitly: `F = np.asarray(F, dtype=float); F = F[None, :] if F.ndim == 1 else F`. |
| Shape mismatch or broadcasting error | `F`, `pf`, `ref_point`, `ideal`, or `nadir` has the wrong number of objective columns. | Assert `F.ndim == 2`, `pf.ndim == 2`, `pf.shape[1] == F.shape[1]`, and `ref_point.shape == (F.shape[1],)`. |
| `RMetric` asks for a Pareto front | Neither `pf` nor `problem.pareto_front()` is available. | Pass `RMetric(problem, ref_points, pf=approx_pf)` with an explicit approximation, or do not use R-metric for this problem. |
| R-metric returns `None` for R-HV | `calc_hv=True` but HV is unsupported/too high-dimensional or no translated points survived trimming. | Use `calc_hv=False` for R-IGD only, inspect `ref_points`/`delta`, or reduce to a lower-dimensional region of interest. |
| KKTPM fails on `dF`/`dG` or derivatives | The problem does not provide gradients, or the run did not evaluate derivative fields. | Use automatic differentiation for differentiable problems, include bounds constraints when needed, and evaluate `return_values_of=["F", "G", "dF", "dG"]`. For black-box/non-differentiable models, choose HV or distance/history metrics instead. |

## Reference direction mistakes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Reference directions factory not found` | Wrong factory name. | Use one of `uniform`, `das-dennis`, `energy`, `multi-layer`, `layer-energy`, `reduction`, or `incremental`. |
| Das-Dennis or incremental rejects `n_points` | The exact point count is not achievable for that dimension and lattice. | Use `n_partitions`, choose one of the suggested achievable counts, or switch to `energy`/`reduction` for arbitrary counts. |
| Too many directions for many objectives | Das-Dennis point count grows combinatorially with `n_partitions` and objectives. | Lower `n_partitions`, use layered directions, or use `energy`/`reduction` with a target count. |
| Reference direction rows do not sum to one | Directions were modified or concatenated incorrectly. | Check `np.allclose(ref_dirs.sum(axis=1), 1.0)` and clip only tiny numerical negatives; regenerate through `get_reference_directions` if the simplex contract is violated. |
| `multi-layer` duplicates or sparse interior | Layers share corners or scaling is not appropriate. | Combine outer and inner layers with different `scaling` values; duplicates are removed, so inspect the final count. |

## Decomposition and MCDM mistakes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Decomposition output has unexpected shape | `_type="auto"` inferred one-to-many, many-to-one, one-to-one, or many-to-many from `F` and `weights`. | Inspect `F.shape` and `weights.shape`; set `_type` explicitly when building matrices for ranking. |
| `AASF` raises that `rho` or `beta` is required | In this version, the augmented ASF constructor needs one of those parameters. | Use `AASF(rho=...)` or `AASF(beta=...)`; use plain `ASF()` if no augmentation parameter is chosen. |
| ASF compromise selection picks the opposite preference | ASF divides by weights; direct preference weights can invert intended priority. | Normalize positive preference weights and pass `1 / weights` for the common compromise-programming recipe. |
| Weighted sum misses a preferred non-convex front region | Weighted sums recover only supported convex regions. | Use ASF/AASF, Tchebicheff, PBI, pseudo weights, or high-tradeoff detection for postprocessing. |
| PseudoWeights result disagrees with weighted-sum optimization | Pseudo weights describe location on the observed front; they are not equivalent to optimizing a weighted sum on non-convex fronts. | Explain the distinction and report both methods when stakeholder preference is ambiguous. |
| HighTradeoffPoints returns `None` | No strong outlier/knee was detected or the set is too small/smooth. | Normalize `F`, increase the candidate set, tune `epsilon`, or use explicit stakeholder weights. |
| Compromise programming helper does not return a usable selection | The explicit class is not the safest selector in this version. | Use the decomposition route: normalize `F`, compute `ASF().do(nF, 1 / weights)`, and select `.argmin()`. |
| Selected index no longer matches `res.X` | MCDM was applied after filtering/sorting without preserving row mapping. | Store original indices, e.g. `idx = find_non_dominated(F); F_nd = F[idx]; selected_original = idx[i]`. |

## Convergence and history mistakes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `res.history` is empty or missing | The run did not use `save_history=True`. | Re-run with `save_history=True` if post-hoc state inspection is required, or record only needed values with a callback during optimization. |
| Memory usage grows too much | `save_history=True` deep-copies the algorithm each generation. | Use shorter runs, score every `stride` generations, or use `AnytimeCallback`/a custom callback to store only `(n_eval, score)`. |
| Convergence curve crashes on infeasible generations | `algo.opt.get("F")` may contain infeasible points or no feasible point yet. | Track `CV` separately, filter feasible rows when appropriate, and decide whether least-infeasible progress should be plotted. |
| HV and IGD curves move in opposite directions | Their optimization directions differ. | Use `mode="max"` for HV and `mode="min"` for distance/epsilon when creating attainment curves. |
| IGD curve overstates progress without true front | The final observed non-dominated set was used as `pf`, measuring convergence to the run's own endpoint. | Label it as an approximation and do not claim convergence to the true Pareto front. |

## Headless plotting and optional animation

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `cannot connect to display`, `TclError`, or plot hangs | An interactive Matplotlib backend was selected in a display-less environment. | Set `import matplotlib; matplotlib.use("Agg")` before importing `pyplot` or pymoo visualization modules, then call `.save(...)`. |
| `show()` does nothing | The backend is `Agg`, where pymoo intentionally avoids opening an interactive window. | Use `.save("file.png")` or `plot.get_figure().savefig(...)` and inspect the saved file. |
| Empty or cropped saved plot | Plot was not drawn yet or layout/bounding options are missing. | Use `plot.save(path, dpi=150)`; it calls `.do()` if needed and uses a tight bounding box by default. |
| Axes label count error | The provided `labels` list length does not equal the number of objectives in the added data. | Match label count to `F.shape[1]`, or use the default prefix label. |
| `Inputs with different dimensions were added` | One plot object received arrays with different objective counts. | Use separate plot objects for 2-D, 3-D, and many-objective matrices. |
| `matplotlib` import is missing | The runtime environment lacks Matplotlib despite plotting code requiring it. | Install or repair the base visualization dependency before plotting; non-plot metrics can still run without static plot creation. |
| `pyrecorder` import fails | Video support is optional and not part of the minimal static plotting path. | Install the optional recorder dependency only when video is required, or save static PNG frames/summary plots. |
| Video writer or streamer fails | External encoders or display streamers are unavailable. | Use `Video(...)` only with a working writer; avoid display streamers in headless sessions and save image sequences instead. |

## Quick bundled checks

- Run `scripts/check_indicators.py` to verify deterministic numeric indicator,
  reference-direction, decomposition, and MCDM behavior.
- Run `scripts/save_scatter_plot.py --out objective_space.png` to verify the
  non-interactive save path and image-file creation.
