# PyPSA Troubleshooting

## Purpose

Read this when a PyPSA task fails before you know whether the cause is installation, optional dependencies, data/schema shape, solver behavior, power-flow convergence, plotting, or API migration.

## First triage

1. Run the root environment helper:

   ```bash
   python scripts/check_pypsa_environment.py --optional
   ```

2. If the problem is network construction, read [network-modeling troubleshooting](../sub-skills/network-modeling/references/troubleshooting.md).
3. If it is loading/saving data, read [network-io-data troubleshooting](../sub-skills/network-io-data/references/troubleshooting.md).
4. If it is a solve or power-flow failure, read [optimization-powerflow troubleshooting](../sub-skills/optimization-powerflow/references/troubleshooting.md).
5. If it is statistics, plotting, clustering, or scenario comparison, read [analysis-visualization troubleshooting](../sub-skills/analysis-visualization/references/troubleshooting.md).

## Install and import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'pypsa'` | PyPSA is not installed in the active Python. | Install `pypsa` in the environment that runs the code; then rerun `python -c "import pypsa"`. |
| Package imports but optional feature fails | Feature-specific extra is missing. | Install only the needed extra, such as `pypsa[excel]`, `pypsa[hdf5]`, `pypsa[cloudpath]`, `pypsa[cartopy]`, or the named package (`scikit-learn`, `tsam`). |
| A local editable install reports a `0.0...` development version | Git tags were not available when the version was resolved. | This affects version display/provenance more than core runtime. Fetch tags for release-accurate local versioning, or use a release package. |
| `pip check` reports broken requirements | Environment dependency conflict. | Create a fresh environment and install only base PyPSA plus required feature extras. Avoid broad `dev`/`docs` dependency groups unless maintaining the repo. |

## Data and schema failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Unknown bus/carrier warnings | Components reference buses or carriers that do not exist in their tables. | Add the missing `Bus` or `Carrier` rows, then rerun `n.consistency_check(strict=["unknown_buses", "unknown_carriers"])`. |
| Shape mismatch in `n.add(...)` | Static-vs-dynamic attribute shape is wrong. | For multiple components with time-varying data, pass a `DataFrame` indexed by `n.snapshots` and with columns exactly equal to component names. |
| CSV import ignores a time series | File naming or snapshots are misaligned. | Use `<component>-<attribute>.csv`; verify rows align with `snapshots.csv`; try `skip_time=True` to isolate static import. |
| pandas string dtype warning | PyPSA is preserving legacy object dtype behavior around pandas 3. | Set `pypsa.options.api.legacy_string_dtype` explicitly to document expected behavior. |

## Solver and optimization failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Solver not found | Requested solver is not installed/licensed. | Use `solver_name="highs"` for base checks or install/license the requested solver. |
| `n.optimize()` returns infeasible | Data/model constraints cannot all be satisfied. | Run consistency checks, reduce the model, add high-cost load shedding to locate shortages, and use Gurobi IIS only if Gurobi is installed and licensed. |
| Unit commitment is slow | MILP complexity and solver choice. | Reduce horizon/assets, use HiGHS for small checks, and use a commercial solver for large MILPs when available. |
| Objective/warning drift across versions | `include_objective_constant` default is changing. | Pass `include_objective_constant=False` or `True` explicitly. |

## Power-flow failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `n.pf()` does not converge | Bad units, ill-conditioned network, poor initial guess, or unsolvable operating point. | Check MW/kW and impedance units, run `n.lpf()`, seed PF with `use_seed=True`, reduce load/generation, and increase gradually. |
| Unexpected slack behavior | Slack bus or distributed slack settings differ from assumptions. | Specify `distribute_slack=True` and `slack_weights` deliberately, or inspect generator controls and bus types. |

## Plotting and clustering failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Static plotting fails on a server | Matplotlib GUI backend unavailable. | Use `matplotlib.use("Agg", force=True)` before plotting. |
| `geomap=True` fails | Cartopy is not installed or projection is invalid. | Install `pypsa[cartopy]` or use `geomap=False`. |
| spatial k-means/HAC clustering fails | `scikit-learn` missing. | Install `scikit-learn` or provide a manual busmap and use `cluster_by_busmap`. |
| temporal segmentation fails | `tsam` missing. | Install `tsam`, or use base `resample`/`downsample` workflows. |
| NetworkCollection comparison is confusing | Networks have mismatched dimensions or names. | Use explicit collection indexes, compare aggregated metrics first, and align snapshots/periods before raw time-series joins. |

## When to stop

Stop and ask for external input rather than guessing when the task requires:

- commercial solver credentials or licenses,
- cloud storage credentials,
- large downloads or private datasets,
- a specific optional solver/backend not installed in the runtime,
- full notebook or benchmark execution beyond a quick smoke check.
