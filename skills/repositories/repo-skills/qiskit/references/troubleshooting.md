# Qiskit troubleshooting

This page collects the cross-cutting failures that most often block Qiskit workflows.

## 1. Import errors or mixed old/new packages

**Symptoms**
- `import qiskit` fails immediately.
- The import complains about both `qiskit-terra` and `qiskit >= 1.0` being present.
- `qiskit._accelerate` or another compiled submodule is missing.

**Likely causes**
- A stale environment mixes pre-1.0 packages with the current package.
- A source checkout was installed editable but the Rust-backed extension was never built.
- The current Python is not the one that has Qiskit installed.

**Recovery**
- Recheck the active environment with `python -m pip check`.
- Install or reinstall in a fresh environment rather than repairing a mixed one.
- If you are in a source tree, rebuild the package with the supported Rust toolchain before retrying the import.

## 2. Missing optional dependencies

**Symptoms**
- `qasm3.load()` or `qasm3.loads()` complains about `qiskit_qasm3_import`.
- Circuit drawers fail because `matplotlib`, `pydot`, `Pillow`, `pylatexenc`, or `seaborn` is missing.
- Transpiler passes fail because `z3-solver` or `python-constraint` is missing.
- Legacy QPY archives fail around `symengine` compatibility.

**Recovery**
- Install the targeted extra instead of the whole optional stack.
- Re-run `python scripts/check_qiskit_environment.py --sections serialization visualization transpiler` after the install.
- For visualization drawers that use LaTeX or Graphviz, also confirm the system tools `pdflatex`, `pdftocairo`, and Graphviz are present.

## 3. QASM and QPY format issues

**Symptoms**
- `QASM2ParseError`, `QASM2ExportError`, `QASM3ExporterError`, or `QASM3ImporterError`.
- `UnsupportedFeatureForVersion` from `qpy.dump()`.
- QPY loads fail only for older archives or only when `use_symengine=True` was used in the generating environment.

**Recovery**
- Check whether the circuit really fits the target format; QASM2 is much more limited than QPY.
- For QASM3 import, prefer the helper package when you need the compatibility path, or use the experimental native parser when its feature coverage is enough.
- For legacy QPY archives, load them in a compatible environment and re-export with `use_symengine=False` if the compatibility notes point that way.

## 4. Transpiler and backend-target mismatches

**Symptoms**
- `TranspilerError` about incompatible basis gates, layout, routing, or target constraints.
- `CircuitTooWideForTarget`.
- A fake backend refuses a basis gate or qubit count.

**Recovery**
- Reconcile the circuit width with the target qubit count and coupling map.
- Check whether a custom `Target` or backend already supplies stage defaults that are being overridden.
- When a transpiler pass needs an optional package, install the named extra rather than loosening the whole environment.

## 5. Visualization rendering problems

**Symptoms**
- A drawer returns a text object when a figure was expected.
- LaTeX or image export fails.
- `Style JSON file ... not found` warnings appear.

**Recovery**
- Confirm the chosen output mode and backend-specific dependencies.
- Check the style path and the `circuit_drawer` options that select `text`, `mpl`, or `latex` output.
- Treat all drawing code as trusted-input only; the visualization module intentionally shells out to external tools in some modes.

## 6. Provider and simulator usage errors

**Symptoms**
- `QiskitBackendNotFoundError` from `BasicProvider.get_backend()`.
- `QiskitError` from invalid `GenericBackendV2` construction or invalid `run()` input.
- Shots validation errors or inconsistent backend option values.

**Recovery**
- Confirm the backend name and the number of qubits first.
- Check the backend's `target`, `basis_gates`, coupling map, and control-flow support.
- Use the bundled smoke helper with the `providers` section to verify the local simulation path before debugging a user workflow.

## 7. C API and source-build issues

**Symptoms**
- `qiskit.capi.get_include()` or `get_lib()` points to nothing useful.
- A downstream extension cannot find the Qiskit headers or shared library.
- A source build fails because the Rust extension or `setuptools-rust` is not available.

**Recovery**
- Rebuild from a clean environment with the supported toolchain.
- Use the `c-api` sub-skill for build-and-link details and the bundled smoke helper's `capi` section to confirm the paths.

If you cannot tell whether the issue is a missing dependency or a mixed environment, run the smoke helper first and inspect the failure section it prints for the exact workflow that broke.
