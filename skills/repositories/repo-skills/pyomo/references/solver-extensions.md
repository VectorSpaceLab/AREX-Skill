# Solver Extensions

## Purpose

Read this when Pyomo itself imports, but the task depends on optional solver,
analysis, or GUI extensions.

## What it covers

- APPSI solver interfaces.
- Feasibility-based bounds tightening (FBBT).
- PyNumero and interior-point tooling.
- Community detection, simplification, and related analysis helpers.
- The model viewer and its Qt / `qtconsole` requirements.

## APPSI

APPSI is the `pyomo.contrib.appsi` family of fast persistent solver interfaces.

Observed solver classes:

- `Cbc`
- `Cplex`
- `Gurobi`
- `Highs`
- `Ipopt`
- `MAiNGO`

Observed configuration helpers:

- `SolverConfig`
- `MIPSolverConfig`

Useful config fields include `time_limit`, `warmstart`, `stream_solver`,
`load_solution`, `symbolic_solver_labels`, `report_timing`, `mip_gap`, and
`relax_integrality`.

APPSI is only useful when the corresponding solver backend is installed.

## FBBT

Key functions:

- `fbbt(comp, deactivate_satisfied_constraints=False, integer_tol=1e-05, ... )`
- `compute_bounds_on_expr(expr, ignore_fixed=False)`

FBBT tightens variable bounds by propagating expression bounds through the
model. It is often used before nonlinear solving or inside higher-level solver
strategies.

## Simplification

Key class:

- `Simplifier(suppress_no_ginac_warnings=False, mode=auto|sympy|ginac)`

The simplifier uses SymPy by default when GiNaC is unavailable. GiNaC is the
faster path, but it is optional and can require compiled components.

## Community detection

Key function:

- `detect_communities(model, type_of_community_map='constraint', with_objective=True, weighted_graph=True, random_seed=None, use_only_active_components=True)`

This workflow needs:

- `networkx`
- `python-louvain`
- `matplotlib` for plotting or graph visualization paths

It returns a `CommunityMap`-style object that can be used to reorganize a model
into blocks.

## PyNumero and interior point

PyNumero is Pyomo's nonlinear-optimization extension layer.

Important objects:

- `pyomo.contrib.pynumero`
- `PyomoNLP`
- `CyIpoptSolver`
- `PyomoCyIpoptSolver`
- `FsolveNlpSolver`
- `RootNlpSolver`
- `NewtonNlpSolver`
- `SecantNewtonNlpSolver`
- `InteriorPointInterface`
- `InteriorPointSolver`

Common support packages:

- `numpy`
- `scipy`
- a C/C++ compiler
- `cmake`
- ASL / HSL / MUMPS / MA27 / MA57 depending on the solver path

Practical build paths seen in the repository:

- `pyomo download-extensions`
- `pyomo build-extensions`
- `python -m pyomo.contrib.pynumero.build ...`

## Model viewer

The model viewer is the `pyomo model-viewer` subcommand and the
`pyomo.contrib.viewer` package.

Key API:

- `get_mainwindow(model=None, show=True, ask_close=True, model_var_name_in_main=None, testing=False)`

Runtime requirements:

- `qtconsole`
- a Qt binding such as `PySide6`, `PyQt5`, or `PyQt6`
- `pint`

Observed failure mode in this checkout:

- without `qtconsole`, `pyomo model-viewer` reports that Qt is not available
  rather than launching the window

## When to use this sub-skill

- A task mentions APPSI, PyNumero, FBBT, simplification, community detection,
  interior-point methods, or the model viewer.
- A solve path fails only after the base Pyomo package imports.
- An optional solver backend or GUI dependency is missing.

## Common gotchas

- Optional solver classes may import fine but still fail at runtime if the
  backend executable or Python wrapper is missing.
- PyNumero build failures often mean CMake or compiler prerequisites are not in
  the environment.
- Viewer failures usually mean `qtconsole` or the Qt binding is absent.
- Community detection often fails because `python-louvain` or `networkx` is
  missing.
- FBBT can raise infeasibility errors when a bound tightening step discovers a
  contradiction.

## Related references

- Read `structured-modeling.md` when the extension is part of a GDP, DAE,
  network, or MPEC workflow.
- Read `cli-reference.md` when the extension is exposed through a Pyomo command.
- Use `scripts/check_optional_backends.py` when you need a quick dependency
  report before digging into a failure.
- Read `troubleshooting.md` for dependency and backend failures.
