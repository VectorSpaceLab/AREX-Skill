# Troubleshooting

## Purpose

Read this when a Pyomo workflow fails to import, solve, load data, or use an
optional extension.

## Import and install failures

### Symptom: `ImportError` on `pyomo.environ`

Likely causes:

- The package was not installed into the intended environment.
- A stale editable install points at the wrong checkout.
- A dependency required by the selected workflow is missing.

Recovery:

- Run the bundled `scripts/check_import.py` helper.
- Re-run `python -m pip check` in the target environment.
- Confirm that `import pyomo, pyomo.environ as pyo` succeeds from the intended
  prefix.

### Symptom: metadata exists but import fails

Likely causes:

- The installation is broken even though the wheel or editable metadata exists.
- A different checkout or user-site package is masking the intended install.

Recovery:

- Use isolated-mode import checks from the target environment.
- Reinstall the package into the intended private prefix.

## Solver failures

### Symptom: `No executable found for solver 'glpk'`

Likely causes:

- The solver package is installed but the executable is not on PATH.
- The solver package was never installed into the target environment.

Recovery:

- Install the solver package that provides the executable.
- Re-run the tiny solver smoke in `scripts/solve_tiny_milp.py`.

### Symptom: `No solver specified!`

Likely causes:

- `pyomo solve` was called without `--solver` and the config file did not
  provide one.

Recovery:

- Pass `--solver=...` explicitly, or add a solver entry to the config file.

### Symptom: `qt not available`

Likely causes:

- `qtconsole` is missing.
- No Qt binding such as `PySide6`, `PyQt5`, or `PyQt6` is installed.

Recovery:

- Install the missing GUI extras only if the model viewer is part of the
  requested workflow.
- Otherwise, use the non-GUI Pyomo workflow instead.

## Optional extension failures

### APPSI backend missing

Likely causes:

- The specific solver backend is unavailable.
- The corresponding executable or Python wrapper is absent.

Recovery:

- Switch to a backend that is installed, or narrow the task to a backend that
  the environment actually supports.

### PyNumero build or import problems

Likely causes:

- `numpy` or `scipy` is missing.
- CMake or a compiler is unavailable for extension build paths.
- The ASL/HSL/MUMPS/MA27/MA57 prerequisites are incomplete.

Recovery:

- Install only the selected extension prerequisites.
- Use the pure-Python paths when the advanced extension is not required.

### Community detection import problems

Likely causes:

- `networkx` or `python-louvain` is missing.

Recovery:

- Install the missing optional dependency and retry the import or example.

### FBBT or simplification surprises

Likely causes:

- Infeasible bounds were detected.
- The expression structure is not compatible with the expected simplifier path.
- GiNaC is unavailable, so the code fell back to SymPy.

Recovery:

- Check the model constraints and bounds.
- Use the reference helper for the chosen workflow and inspect the returned
  expression or tightened bounds.

## Data and config problems

### Symptom: data file or namespace error during `create_instance`

Likely causes:

- The set/parameter structure in the data file does not match the model.
- A namespace is missing or misspelled.

Recovery:

- Re-read `data-and-io.md` and verify the index sets and parameter names.
- Use a smaller tutorial-style data file first.

### Symptom: CLI config generation or model conversion fails

Likely causes:

- The output format or solver name was omitted.
- A transformation name or input model path is wrong.

Recovery:

- Run the safe help commands in `cli-reference.md`.
- Regenerate the config template and inspect the solver/model entries.

## When to stop

Stop and ask for a solver, GUI, backend, or data artifact only when the workflow
truly requires it. Do not treat a plain import as proof that solver, GUI, or
compiled-extension workflows are ready.
