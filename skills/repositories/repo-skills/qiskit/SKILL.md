---
name: qiskit
description: "Routes agents across Qiskit's circuit, transpiler, primitives,
  serialization, quantum-info, visualization, provider, and C-API workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qiskit

Use this repo skill when a task involves the Python package `qiskit`: building quantum circuits, transpiling to backend targets, running reference primitives or basic simulators, importing/exporting OpenQASM or QPY, using quantum-information objects, drawing circuits or results, working with provider interfaces, or consuming Qiskit's public C API.

## Start here

- Read `references/module-map.md` for the package modules, public entry points, and route boundaries.
- Read `references/installation.md` before choosing extras such as `qasm3-import`, `visualization`, `crosstalk-pass`, `csp-layout-pass`, or `qpy-compat`.
- Read `references/troubleshooting.md` for mixed-package imports, missing Rust-backed `_accelerate`, optional-dependency failures, QPY compatibility, and visualization system-tool issues.
- Read `references/repo-provenance.md` before deciding whether this skill is stale for a newer Qiskit checkout or release.
- Run `python scripts/check_qiskit_environment.py --help` to see source-free smoke checks for the active Python environment.

## Minimal install and smoke check

For normal package use:

```bash
python -m pip install qiskit
python -c 'import qiskit; print(qiskit.__version__)'
```

Add targeted extras only for the workflows you need:

```bash
python -m pip install 'qiskit[qasm3-import]'
python -m pip install 'qiskit[visualization]'
```

Then run the bundled smoke helper from this skill directory:

```bash
python scripts/check_qiskit_environment.py --sections core transpiler primitives serialization quantum-info
```

## Route by task

| User task | Read |
| --- | --- |
| Build, edit, compose, parameterize, or inspect `QuantumCircuit` objects, registers, bits, gates, control-flow operations, or circuit-library gates | `sub-skills/circuit/SKILL.md` |
| Compile circuits to a backend, `Target`, basis gate set, or coupling map; use preset pass managers; debug layout, routing, translation, scheduling, seeds, or pass plugins | `sub-skills/transpiler/SKILL.md` |
| Use `StatevectorSampler`, `StatevectorEstimator`, PUBs, `PrimitiveResult`, `DataBin`, `BitArray`, expectation values, shots, precision, or primitive result access patterns | `sub-skills/primitives/SKILL.md` |
| Import/export OpenQASM 2, OpenQASM 3, or QPY; choose between text interchange and full-fidelity binary serialization; handle parser/exporter/version errors | `sub-skills/serialization/SKILL.md` |
| Work with `Statevector`, `DensityMatrix`, `Operator`, `SparsePauliOp`, `Pauli`, Clifford, random operators/states/channels, fidelities, entropy, or matrix predicates | `sub-skills/quantum-info/SKILL.md` |
| Draw circuits, histograms, distributions, states, backend maps, timelines, pass managers, or diagnose `matplotlib`, Graphviz, Pillow, pylatexenc, seaborn, or LaTeX output | `sub-skills/visualization/SKILL.md` |
| Use or implement backend/provider abstractions, `BackendV2`, `Options`, `Job`, `BasicProvider`, `BasicSimulator`, or `GenericBackendV2` fake backends | `sub-skills/providers/SKILL.md` |
| Locate Qiskit C headers/library, use `qiskit.capi` ctypes bindings, build or consume the public C API, or diagnose Rust/C-extension build failures | `sub-skills/c-api/SKILL.md` |

## Common routing decisions

- Start with `circuit` before `transpiler` when the user has not yet built a valid abstract circuit.
- Start with `transpiler` when the problem involves basis gates, coupling maps, `Target`, `Layout`, `PassManager`, or hardware constraints, even if a fake provider appears in the example.
- Start with `primitives` for sampler/estimator jobs and result containers; start with `providers` for backend classes, `BasicSimulator.run`, `GenericBackendV2`, or provider implementation surfaces.
- Start with `serialization` for QASM/QPY even when the circuit construction is also involved; route back to `circuit` only if the circuit itself is invalid before serialization.
- Start with `quantum-info` when the task is mathematical analysis of states, operators, observables, channels, or fidelities rather than execution on a backend.
- Start with `visualization` whenever output format, style, image generation, or optional drawing dependencies are the main concern.
- Start with `c-api` for `qiskit.capi.get_include()`, `get_lib()`, native headers, ctypes functions, or standalone C-library build questions.

## Bundled helper

`scripts/check_qiskit_environment.py` performs quick, source-free checks for imports, a small circuit, transpilation with `GenericBackendV2`, `StatevectorSampler`/`StatevectorEstimator`, QASM/QPY round-trips, quantum-info objects, visualization, providers, and C-API paths. Use `--sections` to narrow the checks and `--json` for machine-readable output.

## What this skill does not cover

- It does not replace domain packages such as Qiskit Aer, Qiskit IBM Runtime, Qiskit Nature, or hardware-vendor provider packages when their package-specific APIs are the main subject.
- It does not teach quantum-computing theory beyond the Qiskit object and workflow contracts needed to complete software tasks.
- It does not require the original Qiskit source checkout for runtime use; all necessary operating guidance is distilled into this skill tree.
