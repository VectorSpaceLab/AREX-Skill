---
name: solve-and-cli
description: "Guides Pyomo users through the pyomo command, solver selection,
  config templates, and solver-backed smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Solve and CLI

Use this sub-skill when the task is about running Pyomo through the `pyomo`
command, selecting a solver, generating config templates, or checking installed
solver interfaces.

## What this sub-skill covers

- `pyomo solve`, `pyomo convert`, `pyomo run`, `pyomo help`, and
  `pyomo test-solvers`.
- Safe help/version checks and config-template generation.
- Solver selection, solver-manager selection, and result handling.
- Tiny solve-backed smoke checks for base installation validation.

## What to route elsewhere

- Model-construction questions go to `modeling-basics`.
- Data-file and `create_instance()` questions go to `data-and-io`.
- GDP, DAE, network, MPEC, and units go to `structured-modeling`.
- APPSI, PyNumero, FBBT, simplification, community detection, or viewer issues
  go to `solver-extensions`.

## Read these references

- `../../references/cli-reference.md` for the verified subcommands, flags, and
  safe help paths.
- `../../references/troubleshooting.md` for common solver and CLI failure modes.
- `../../references/data-and-io.md` when the CLI consumes a model/data file or
  config file pair.

## Use these helpers

- `../../scripts/check_import.py` for a quick install/import sanity check.
- `../../scripts/solve_tiny_milp.py` for a deterministic solver-backed smoke
  check against a tiny binary model.

## Typical workflow

1. Confirm the target package and solver are installed.
2. Run `pyomo --help` or the subcommand-specific help text.
3. Use `pyomo solve` for an optimization run or `pyomo convert` for a format
   conversion.
4. Use `pyomo test-solvers` when you need to inspect installed solver support.
5. Fall back to the tiny MILP helper to prove the solver path works.

## Common request patterns

- "What subcommands does `pyomo` have?"
- "How do I pass a solver name to `pyomo solve`?"
- "How do I generate a config template?"
- "Why does `pyomo solve` say no solver was specified?"
- "How do I check whether GLPK works with this install?"

## Common failure modes

- Solver executable missing from the environment.
- Solver name omitted from the CLI or config file.
- Conversion output format omitted or misspelled.
- `pyomo model-viewer` called without the optional GUI dependencies.
- A command points at a model file or data file that does not exist.

## Practical guidance

- Prefer the smallest safe CLI example that proves the desired path.
- Use `-h` or `--help` before attempting a risky option.
- Keep solver checks tiny and deterministic.
- Treat `download-extensions` and `build-extensions` as maintenance or
  extension workflows, not default runtime checks.

## Examples of what belongs here

- `pyomo solve --solver=glpk model.py data.dat`
- `pyomo convert --output=model.lp --format=lp model.py`
- `pyomo test-solvers glpk`
- `pyomo solve --generate-config-template=template.yaml`

## Examples of what does not belong here

- Component construction or file-loading details.
- GDP/DAE/network transformations.
- Optional solver backend internals.

## Related routes

- Move to `modeling-basics` when the question is really about constructing the
  model that the CLI will solve.
- Move to `data-and-io` when the issue is input data or config file loading.
- Move to `solver-extensions` when the CLI failure comes from an optional
  extension or backend package.
