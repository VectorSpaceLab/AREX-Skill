# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| PSO equality constraints appear to do nothing | `constraint_eq` is not implemented | Move the problem to DE or encode equality as a penalty or projection. |
| Candidate shape errors or array-valued comparisons | The objective expects a batch, but the optimizer passes one candidate at a time, or vice versa | Rewrite the objective to return one finite scalar for one `x`; keep vectorized objectives in the separate speedup workflow. |
| `nan` / `inf` in `best_y` or history | The objective or a penalty is non-finite | Clip inputs, guard denominators and logs, and return a large finite penalty instead of `inf` / `nan`. |
| Bounds assertion or broadcast failure | `lb` and `ub` do not match `n_dim`, or only one of them was given to SA | Pass scalars or length-`n_dim` sequences; for SA provide both `lb` and `ub` together. |
| PSO stops too early or never stops | `precision` or `N` is too strict or too loose for the noise level | Tune `precision` and `N`, or skip the precision stop and use `max_iter`. |
| PSO record mode uses too much memory | Every `X`, `V`, and `Y` snapshot is stored | Keep `record_mode=False` unless the run is tiny. |
| SA cools too slowly or too quickly | `T_max`, `T_min`, `L`, or the schedule knobs are off | Keep `T_max > T_min > 0`, raise `L` for more search, and tune `quench`, `hop`, or `learn_rate`. |
| AFSA barely moves or oscillates | `step`, `visual`, `q`, or `max_try_num` are mismatched | Reduce `step`, widen `visual`, soften `q`, or raise `max_try_num`. |

Notes:

- DE supports both equality and inequality constraints.
- PSO only supports inequality constraints.
- SA and AFSA have no constraint callbacks; use penalties or projection.
- AFSA in this release has no explicit box-bound arguments.
- Do not confuse SAFast's `quench` with AFSA's `q`.
- `n_processes` alone does not parallelize a plain objective; it only matters after the objective has been prepared for a parallel mode in the speedup workflow.
