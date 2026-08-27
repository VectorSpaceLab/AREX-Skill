# Solve and CLI Troubleshooting

## Purpose

Read this when a `pyomo` command, solver invocation, or configuration-template
flow fails.

## Common failures

### `No solver specified!`

Symptoms:

- `pyomo solve` exits before running a model.

Likely causes:

- The command omitted `--solver` and the config file did not supply one.

Recovery:

- Pass `--solver=<name>` explicitly.
- Or add the solver name to the configuration file.

### `No executable found for solver 'glpk'`

Symptoms:

- The model builds, but the solver invocation fails immediately.

Likely causes:

- The solver executable is not installed in the active environment.
- The executable is installed but not visible to the environment prefix.

Recovery:

- Install the solver package that provides the executable.
- Re-run the tiny solver smoke helper.

### `pyomo convert` fails on output format

Symptoms:

- The command says the output format is unknown or unspecified.

Likely causes:

- `--format` and `--output` do not agree.
- The target suffix is missing or misspelled.

Recovery:

- Run `pyomo convert -h`.
- Generate a config template and inspect the output fields.

### `pyomo model-viewer` reports missing Qt support

Symptoms:

- The command prints `qt not available`.

Likely causes:

- `qtconsole` is missing.
- A Qt binding such as PySide6, PyQt5, or PyQt6 is missing.

Recovery:

- Install the GUI extras only when the viewer is part of the selected workflow.
- Otherwise use the CLI or API route.

## Next step

If the issue is actually a model-construction problem or a structured modeling
workflow, move to the matching sub-skill first.
