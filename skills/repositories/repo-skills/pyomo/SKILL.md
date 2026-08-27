---
name: pyomo
description: "Guides Pyomo optimization-modeling workflows, solver CLI use, data
  loading, structured modeling, and solver extensions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Pyomo

Use this skill when the task is about Pyomo algebraic optimization models,
Pyomo's `pyomo` command, data loading into models, or solver/analysis
extensions that build on Pyomo models.

## Start here

- Read `references/repo-provenance.md` when you need to check whether this skill
  still matches the current checkout.
- Read `references/troubleshooting.md` when imports, solvers, optional packages,
  Qt, or compiled extensions fail.
- Use `scripts/check_import.py` for a quick package/import sanity check.
- Use `scripts/solve_tiny_milp.py` when you need a safe solver-backed smoke test.

## Install and import

The public package name is `pyomo`.

Typical installs:

- `pip install pyomo`
- `conda install -c conda-forge pyomo`

For solver-backed checks, also install a solver such as `glpk`.
For GUI or advanced extensions, install only the optional packages that the
relevant sub-skill or reference calls out.

Minimal import check:

```bash
python -c "import pyomo, pyomo.environ as pyo; print(pyomo.__version__); print(pyo.ConcreteModel)"
```

## Route map

### `modeling-basics`
Read this for `ConcreteModel`, `Set`, `Param`, `Var`, `Constraint`,
`Objective`, `Block`, `Expression`, `Suffix`, `value()`, component traversal,
and small self-contained model construction.

### `data-and-io`
Read this for `AbstractModel`, `DataPortal`, `create_instance`, data-file
loading, `.dat` / `.tab` / Excel inputs, and tutorial-style data workflows.

### `solve-and-cli`
Read this for `pyomo solve`, `pyomo convert`, `pyomo run`, `pyomo help`,
`pyomo test-solvers`, config templates, solver selection, and CLI smoke checks.

### `structured-modeling`
Read this for GDP, DAE, network models, MPEC, model transformations,
discretization, ports/arcs, and other structured-modeling workflows.

### `solver-extensions`
Read this for APPSI, FBBT, PyNumero, simplification, community detection,
interior-point tooling, and the model viewer / optional-backend troubleshooting
surface.

## What this skill owns

- Pyomo modeling APIs and common component patterns.
- Pyomo data-loading workflows and tutorial-style examples.
- Pyomo CLI entry points and solver orchestration.
- Structured modeling extensions and their transformations.
- Optional solver/analysis extensions and their dependency boundaries.

## What this skill does not own

- Generic mathematical-optimization theory that is not Pyomo-specific.
- Solver installation instructions beyond the Pyomo-facing commands and
  dependency notes.
- External solver manuals.
- Original repository paths in runtime instructions.

## Bundled helpers

- `scripts/check_import.py` — run this when you need a fast import and metadata
  check from the target environment.
- `scripts/check_optional_backends.py` — run this when you need a quick report
  on optional scientific, GUI, and Pyomo extension dependencies.
- `scripts/solve_tiny_milp.py` — run this when you need a deterministic solve
  smoke test against a tiny binary model.

## References

- `references/core-modeling.md` — core component and expression overview.
- `references/data-and-io.md` — abstract models, data files, and input formats.
- `references/cli-reference.md` — Pyomo CLI commands and safe help paths.
- `references/structured-modeling.md` — GDP, DAE, network, and MPEC workflows.
- `references/solver-extensions.md` — APPSI, PyNumero, FBBT, viewer, and other
  optional extensions.
- `references/repo-routing-metadata.json` — structured router metadata used by
  repo-skills routing.
- `references/troubleshooting.md` — install, import, solver, Qt, and extension
  failures.

## Verified package facts

- `pyomo` installs a `pyomo` console command.
- `pyomo.solve`, `pyomo.convert`, `pyomo.run`, `pyomo.download-extensions`,
  `pyomo.build-extensions`, `pyomo.install-extras`, `pyomo.model-viewer`, and
  `pyomo.test-solvers` are available subcommands in this checkout.
- The package imports as `pyomo` and `pyomo.environ`.
- `SolverFactory('glpk')` works when the `glpsol` executable is available.
- `pyomo model-viewer` requires `qtconsole` plus a Qt binding and currently
  reports missing Qt support when those extras are absent.

## Selection hints

- If the task mentions building or debugging a model, start with
  `modeling-basics`.
- If the task mentions `.dat`, `.tab`, Excel, or `create_instance`, start with
  `data-and-io`.
- If the task mentions `pyomo solve`, `pyomo convert`, or solver selection,
  start with `solve-and-cli`.
- If the task mentions GDP, DAE, network, or complementarity models, start with
  `structured-modeling`.
- If the task mentions APPSI, PyNumero, FBBT, simplification, community
  detection, interior point, or the viewer, start with `solver-extensions`.
