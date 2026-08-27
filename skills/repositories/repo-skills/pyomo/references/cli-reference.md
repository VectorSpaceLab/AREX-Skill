# CLI Reference

## Purpose

Read this when the task is about the `pyomo` command-line interface, solver
selection, conversion templates, or solver/test subcommands.

## Verified subcommands in this checkout

`pyomo --help` reports these subcommands:

- `build-extensions`
- `convert`
- `download-extensions`
- `help`
- `install-extras`
- `model-viewer`
- `run`
- `solve`
- `test-solvers`

## Safe help checks

These are safe and useful before a real run:

```bash
pyomo --help
pyomo solve -h
pyomo convert -h
pyomo help --solvers
pyomo test-solvers -h
```

## `pyomo solve`

Use this to execute a model through a solver.

Key options observed in this checkout:

- `--solver`
- `--solver-manager`
- `--generate-config-template`
- `--namespace`
- `--model-name`
- `--transform`
- `--preprocess`
- `--logging`
- `--logfile`
- `--catch-errors`
- `--keepfiles`
- `--path`
- `--profile-count`
- `--report-timing`
- `--tempdir`

The command accepts either a Python model file or a YAML/JSON config file.
When the solver name is omitted, `pyomo` looks for it in the config file.

## `pyomo convert`

Use this to convert a Pyomo model to another output format.

Key options observed in this checkout:

- `--output`
- `--format`
- `--generate-config-template`
- `--namespace`
- `--model-name`
- `--symbolic-solver-labels`
- `--file-determinism`
- `--transform`
- `--preprocess`
- `--logging`
- `--logfile`
- `--catch-errors`
- `--keepfiles`
- `--path`
- `--profile-count`
- `--report-timing`
- `--tempdir`

## `pyomo run`

Use this to execute a command from the environment's `bin/` or `Scripts/`
directory through Pyomo's wrapper logic.

Useful flag:

- `--list` to show available commands.

## `pyomo test-solvers`

Use this to test installed solver interfaces.

Useful flags:

- `--csv-file`
- `--debug`
- `--verbose`

The command accepts optional solver names. If no solver names are provided, it
tries the available solvers it can find.

## `pyomo model-viewer`

Use this for the interactive model viewer when `qtconsole` and a Qt binding are
installed.

Observed behavior in this checkout:

- It reports a Qt support problem when `qtconsole` is missing.
- It needs a Qt binding such as PySide6 or PyQt5/PyQt6.

## `pyomo download-extensions` and `pyomo build-extensions`

These commands are available but are not safe default smoke checks because they
can download or compile extension packages.

Use them only when the workflow explicitly needs compiled extensions.

## `pyomo install-extras`

This legacy command exists, but the project docs now recommend installing the
needed optional dependencies directly.

## Good command shapes

```bash
pyomo solve --solver=glpk model.py data.dat
pyomo convert --output=model.lp --format=lp model.py data.dat
pyomo solve --solver=glpk --generate-config-template=template.yaml
```

## Common CLI failures

- `No solver specified!`
- `No executable found for solver 'glpk'`
- `qt not available`
- data or config file path errors
- transformation names that are misspelled or deprecated

## Related references

- Read `data-and-io.md` when the CLI consumes data files or config files.
- Read `troubleshooting.md` when a subcommand fails or a solver is missing.
- Read `solver-extensions.md` when a CLI error comes from optional backends or
  compiled extensions.
