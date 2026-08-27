# Qiskit installation and feature selection

Use targeted installs. The base package already covers circuits, transpilation, primitives, providers, quantum information, and the C API.

## Core install

```bash
python -m pip install qiskit
```

## Optional workflows and extras

| Workflow | Install hint | Notes |
| --- | --- | --- |
| OpenQASM 3 import | `python -m pip install 'qiskit[qasm3-import]'` | Needed for the legacy `qiskit_qasm3_import` path used by `qasm3.load()` and `qasm3.loads()`. |
| Visualization | `python -m pip install 'qiskit[visualization]'` | Adds `matplotlib`, `pydot`, `Pillow`, `pylatexenc`, and `seaborn`; some drawers also rely on system tools such as Graphviz, `pdflatex`, and `pdftocairo`. |
| Crosstalk pass support | `python -m pip install 'qiskit[crosstalk-pass]'` | Pulls in `z3-solver` for transpiler passes that depend on it. |
| CSP layout support | `python -m pip install 'qiskit[csp-layout-pass]'` | Pulls in `python-constraint` for the CSP layout pass. |
| Legacy QPY compatibility | `python -m pip install 'qiskit[qpy-compat]'` | Adds `symengine` and a newer `sympy` range for older QPY archives and compatibility workflows. |

## Recommended smoke check

Use the bundled helper once the package is installed:

```bash
python scripts/check_qiskit_environment.py --sections core transpiler primitives serialization quantum-info providers capi
```

Add `visualization` when the optional plotting stack is installed and you want to confirm that the drawers work in the current environment.

## Source-build note

If you are working from a source checkout rather than an installed wheel, Qiskit builds a Rust-backed extension as part of its package. The public runtime skill does not depend on the original checkout, but build/install troubleshooting may still need a fresh environment with the supported Rust toolchain and `setuptools-rust`.
