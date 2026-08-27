---
name: pypsa
description: "Guides PyPSA power-system network modeling, data I/O,
  optimization, power flow, statistics, plotting, clustering, and
  troubleshooting workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyPSA repo skill

Use this skill when a task asks about PyPSA (Python for Power Systems Analysis) as a Python package for power-system or energy-system network modeling, optimization, simulation, data exchange, result analysis, plotting, or troubleshooting.

## First checks

- PyPSA is primarily a Python API package; there is no package-level console script to route through.
- Start from `import pypsa` and `pypsa.Network()` unless the task is specifically about loading an existing network file.
- Base PyPSA covers network modeling, CSV/netCDF I/O, HiGHS optimization, power flow, statistics, and no-geomap plotting.
- Optional extras are feature-specific: HDF5, Excel, cloud paths, Cartopy, Gurobi, scikit-learn spatial clustering, TSAM temporal segmentation, and external converters.
- If the current repository or package version may differ from this skill, read [repository provenance](references/repo-provenance.md).

## Install and environment

Read [install and environment guidance](references/install-and-environment.md) before changing dependencies, selecting solvers, or relying on optional extras.

Minimal import check:

```python
import pypsa
n = pypsa.Network()
n.add("Carrier", "AC")
n.add("Bus", "bus", carrier="AC")
```

Bundled helpers:

- [Check PyPSA environment](scripts/check_pypsa_environment.py) reports mandatory imports, optional-extra availability, and an optional tiny HiGHS solve.
- [PyPSA quickstart smoke](scripts/pypsa_quickstart_smoke.py) builds a tiny network and can optionally solve it.

## Route by task

### Build or fix a network model

Use [network-modeling](sub-skills/network-modeling/SKILL.md) for:

- `pypsa.Network`, `n.add`, `n.remove`, snapshots, investment periods, and stochastic scenarios.
- Component tables, time-varying attributes, standard line/transformer types, carrier rows, and schema/default lookup.
- Old/new Components API migration, `pypsa.options`, `n.consistency_check`, `n.sanitize`, `n.copy`, and `n.equals`.

### Load, save, or repair network data

Use [network-io-data](sub-skills/network-io-data/SKILL.md) for:

- `Network(import_name=...)`, CSV folders, netCDF, HDF5, Excel, URLs, and cloud object storage.
- Data layout, snapshots/time-series file alignment, metadata/CRS, round-trip validation, example cache behavior.
- PYPOWER and pandapower import converters and optional I/O dependency failures.

### Optimize, solve, or run power flow

Use [optimization-powerflow](sub-skills/optimization-powerflow/SKILL.md) for:

- `n.optimize`, `create_model`, `solve_model`, `extra_functionality`, custom Linopy constraints, and solver options.
- Capacity expansion, dispatch, storage, unit commitment, global constraints, stochastic or multi-investment planning, MGA, rolling horizon, piecewise curves, and transmission losses.
- `n.lpf`, `n.pf`, optimize-then-nonlinear-power-flow validation, solver failures, infeasibility, and convergence triage.

### Analyze, plot, compare, or cluster results

Use [analysis-visualization](sub-skills/analysis-visualization/SKILL.md) for:

- `n.statistics` / `n.stats`, metric filters, groupers, time aggregation, and custom groupers.
- Static and interactive statistics plots, network maps, `n.plot.map`, `n.plot.iplot`, and `n.plot.explore`.
- `NetworkCollection` scenario comparison and temporal/spatial clustering, including optional Cartopy, scikit-learn, and TSAM behavior.

## Shared references

- [Package overview](references/package-overview.md) maps public APIs, concepts, optional extras, and sub-skill ownership.
- [Install and environment guidance](references/install-and-environment.md) explains Python versions, solver defaults, extras, environment variables, options, offline use, and headless plotting.
- [Troubleshooting](references/troubleshooting.md) is the cross-cutting triage map for install/import, schema, solver, power-flow, plotting, clustering, and optional dependency failures.
- [Repository provenance](references/repo-provenance.md) records the source commit, package version, evidence paths, and refresh triggers.
- [Routing metadata](references/repo-routing-metadata.json) is structured metadata for managed repo-skills-router import.

## Core operating loop

1. Decide whether the network should be built in code or loaded from a file; route to modeling or I/O.
2. Validate carriers, buses, component names, snapshots, time-series shapes, and optional API settings before solving.
3. For optimization, start with `solver_name="highs"`, explicit `include_objective_constant`, and a small horizon before scaling.
4. For power flow, run a linear flow first when nonlinear convergence is uncertain.
5. Analyze solved outputs with statistics and plots; on unsolved networks, prefer input-side metrics such as installed capacity.
6. When optional features fail, install only the feature-specific extra or use the documented base fallback.

## Do not

- Do not tell future agents to open or run original PyPSA repository docs, tests, notebooks, examples, or scripts; this generated skill bundles the reusable guidance and smoke helpers needed for operation.
- Do not install all optional extras or dev/docs dependencies unless the task explicitly needs them.
- Do not treat a CPU import as proof that optional Cartopy, Gurobi, cloud, Excel, HDF5, scikit-learn, TSAM, pandapower, or PYPOWER workflows are installed.
- Do not run large notebooks, network downloads, cloud operations, or commercial-solver IIS checks without explicit task need and credentials/license availability.
