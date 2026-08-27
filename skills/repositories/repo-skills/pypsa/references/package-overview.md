# PyPSA Package Overview

## Purpose

Read this reference when you need a compact map of PyPSA concepts, package entry points, optional extras, and how the sub-skills divide responsibility.

## What PyPSA is for

PyPSA (Python for Power Systems Analysis) is a Python framework for modeling, optimizing, simulating, and analyzing modern power and energy systems. It supports conventional generators, unit commitment, variable renewables, storage, sector coupling, elastic demand, linearized optimal power flow, security-constrained planning, multi-period pathway planning, stochastic optimization, and static/nonlinear power-flow validation.

The primary user interface is Python code or notebooks. This package does not expose a repo-level console script; route API tasks through `pypsa.Network` and its accessors.

## Main public entry points

| Entry point | Role | Owning route |
|---|---|---|
| `pypsa.Network()` | In-memory network container and main API surface. | [network-modeling](../sub-skills/network-modeling/SKILL.md) |
| `n.add(...)`, `n.remove(...)`, `n.set_snapshots(...)`, `n.set_investment_periods(...)`, `n.set_scenarios(...)` | Build and mutate model inputs. | [network-modeling](../sub-skills/network-modeling/SKILL.md) |
| `n.components` / `n.c` | Components store: static tables, dynamic time series, defaults, helper indexes. | [network-modeling](../sub-skills/network-modeling/SKILL.md) |
| `Network(import_name=...)`, `import_from_*`, `export_to_*` | Load/save CSV folders, netCDF, HDF5, Excel, cloud paths, PYPOWER, and pandapower imports. | [network-io-data](../sub-skills/network-io-data/SKILL.md) |
| `n.optimize`, `n.optimize.create_model()`, `n.optimize.solve_model()` | Linopy optimization model build/solve/write-back workflows. | [optimization-powerflow](../sub-skills/optimization-powerflow/SKILL.md) |
| `n.lpf()`, `n.pf()` | Linear and nonlinear power-flow calculations. | [optimization-powerflow](../sub-skills/optimization-powerflow/SKILL.md) |
| `n.statistics` / `n.stats` | Metrics such as installed capacity, capex, opex, supply, energy balance, prices, and system cost. | [analysis-visualization](../sub-skills/analysis-visualization/SKILL.md) |
| `n.plot` and `n.statistics.<metric>.plot` / `.iplot` | Static and interactive charts/maps. | [analysis-visualization](../sub-skills/analysis-visualization/SKILL.md) |
| `n.cluster.spatial`, `n.cluster.temporal` | Spatial and temporal clustering. | [analysis-visualization](../sub-skills/analysis-visualization/SKILL.md) |
| `pypsa.NetworkCollection` | Compare aligned collections of networks. | [analysis-visualization](../sub-skills/analysis-visualization/SKILL.md) |
| `pypsa.options`, `pypsa.option_context`, `pypsa.set_option`, `pypsa.get_option` | Session/global option control. | Root install/troubleshooting and [network-modeling](../sub-skills/network-modeling/SKILL.md) for modeling/API options. |

## Workflow lifecycle

1. **Model** — build or load a `Network`; define carriers, buses, components, snapshots, periods, and scenarios.
2. **Validate** — run `n.consistency_check(...)`; fix undefined buses/carriers, shape mismatches, bad bounds, and optional API migration issues.
3. **Persist or exchange** — choose CSV/netCDF/HDF5/Excel/cloud format and validate round-trips.
4. **Solve or simulate** — use `n.optimize(...)`, `create_model()` + `solve_model()`, `n.lpf()`, or `n.pf()`.
5. **Analyze and visualize** — use statistics, plots, maps, clustering, and `NetworkCollection` comparison.
6. **Troubleshoot** — distinguish data-shape/schema problems from solver/backend/optional dependency problems before changing dependencies or model formulation.

## Mandatory and optional dependencies

A base PyPSA install covers core network modeling, CSV/netCDF I/O, HiGHS optimization, power flow, statistics, and no-geomap plotting. Optional dependency families are feature-scoped:

| Feature | Extra or module | Use |
|---|---|---|
| HDF5 I/O | `pypsa[hdf5]` / `tables` | Read/write HDF stores. |
| Excel I/O | `pypsa[excel]` / `openpyxl`, `python-calamine` | Read/write small Excel workbooks. |
| Cloud paths | `pypsa[cloudpath]` / `cloudpathlib` plus provider clients | Read/write `s3://`, `gs://`, or `az://` URIs. |
| `.env` options | `pypsa[dotenv]` / `python-dotenv` | Load `PYPSA_*` options from `.env`. |
| Geographical maps | `pypsa[cartopy]` / `cartopy` | Cartopy `geomap=True` map layers and projections. |
| Gurobi API | `pypsa[gurobipy]` / `gurobipy` | Commercial solver and IIS infeasibility tracing, subject to license. |
| Spatial clustering algorithms | `scikit-learn` | k-means and HAC bus maps. |
| Temporal segmentation | `tsam` | TSAM-based variable-duration segments. |
| External converters/comparisons | `pandapower`, `pypower` | Optional import or validation against external power-system tools. |

Do not install broad `dev` or `docs` dependencies unless the task explicitly needs repo maintenance or documentation builds.

## Verification helpers bundled with this skill

- [scripts/check_pypsa_environment.py](../scripts/check_pypsa_environment.py) checks mandatory imports, optional-extra availability, and optionally a tiny HiGHS solve.
- [scripts/pypsa_quickstart_smoke.py](../scripts/pypsa_quickstart_smoke.py) builds a tiny network and optionally solves it.
- Each sub-skill also bundles focused smoke helpers for its own workflows.
