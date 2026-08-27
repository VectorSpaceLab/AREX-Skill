# Solver Extensions Troubleshooting

## Purpose

Read this when an optional Pyomo extension imports but cannot complete its
backend, solver, or GUI workflow.

## Common failures

### APPSI backend missing

Symptoms:

- The APPSI solver class imports, but solving fails because the backend is not
  available.

Likely causes:

- The requested solver wrapper is not installed.
- The underlying executable or Python package is absent.

Recovery:

- Select a backend that is actually installed.
- Re-check solver availability in the active environment.

### PyNumero or interior-point build issues

Symptoms:

- PyNumero imports fail, or the build helper cannot finish.

Likely causes:

- `numpy` or `scipy` is missing.
- CMake, a compiler, or an external linear solver dependency is missing.
- The requested compiled path needs ASL, HSL, MUMPS, MA27, or MA57 support.

Recovery:

- Install only the minimum backend set required by the selected workflow.
- Use the pure-Python path when the compiled extension is optional.

### Community detection import issues

Symptoms:

- The community detection package errors during import or execution.

Likely causes:

- `networkx` is missing.
- `python-louvain` is missing.

Recovery:

- Install the missing dependency pair and retry the import.

### Viewer startup fails

Symptoms:

- `pyomo model-viewer` reports that Qt is unavailable.
- UI files fail to load.

Likely causes:

- `qtconsole` is missing.
- No Qt binding such as PySide6, PyQt5, or PyQt6 is installed.
- The environment cannot load the UI toolkit.

Recovery:

- Install the GUI extras only when the viewer is needed.
- Otherwise use the non-GUI API route.

### Simplification or FBBT behaves differently than expected

Symptoms:

- Expression simplification changes more or less than expected.
- FBBT reports infeasibility or tightens bounds aggressively.

Likely causes:

- The model is actually inconsistent.
- A backend such as GiNaC is unavailable, so the fallback path is used.

Recovery:

- Inspect the model bounds and expressions first.
- Treat the fallback path as valid, not as a failure, unless the task truly
  requires a faster or compiled backend.

## Next step

If the issue is actually a base-model, data-loading, or CLI command problem,
move back to the corresponding sub-skill.
