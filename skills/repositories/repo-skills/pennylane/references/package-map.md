# PennyLane package map

Use this map to pick the nearest sub-skill and API surface before reading deeper references.

## Core execution

- `pennylane.workflow`: `QNode`, `qnode`, `execute`, shot management, interface/diff resolution, transform program setup.
- `pennylane.devices`: device loading, built-in simulators (`default.qubit`, `default.mixed`, `default.clifford`, `default.tensor`, `reference.qubit`, `null.qubit`), execution configuration, tracker, preprocessing, device-test CLI.
- `pennylane.measurements`: `expval`, `var`, `probs`, `sample`, `counts`, `state`, density matrix, entropy, purity, mutual information, shadows, shot behavior.
- `pennylane.drawer`: text and Matplotlib circuit drawing.

Read `sub-skills/circuits-devices/` for these.

## Circuit content and transforms

- `pennylane.ops`: gates, channels, observables, symbolic op math (`sum`, `prod`, `s_prod`, `pow`, `adjoint`, `ctrl`, `cond`, `exp`), measurement operations, matrix/eigenvalue helpers.
- `pennylane.templates`: embeddings, layers, tensor-network templates, state preparations, subroutines, swap networks.
- `pennylane.transforms`: compile/decompose, batching, controlled-Q helpers, dynamic one-shot, Monte Carlo, Clifford+T decomposition, pattern matching.
- `pennylane.decomposition`: decomposition rules, gate sets, resource-aware decompositions.
- `pennylane.pauli`: Pauli words/sentences, decomposition, arithmetic utilities.

Read `sub-skills/operators-transforms/` for these.

## Differentiation and ML interfaces

- `pennylane._grad`: `grad`, `jacobian`, `value_and_grad`, `vjp`, `jvp`.
- `pennylane.gradients`: parameter-shift, finite difference, SPSA, metric tensor, VJP/JVP, higher-order derivatives.
- `pennylane.math`: interface-aware math dispatch via Autoray; prefer it inside PennyLane-facing code.
- `pennylane.optimize`: built-in optimizers for NumPy/Autograd-style workflows.
- `pennylane.qnn`: `TorchLayer` for PyTorch integration.
- `pennylane.compiler`: `qjit` facade for Catalyst-backed workflows when Catalyst is installed.
- `pennylane.capture` and `pennylane.control_flow`: program capture, JAX integration, `for_loop`, `while_loop`, dynamic-shape notes.

Read `sub-skills/gradients-interfaces/` for these.

## Domain and application modules

- `pennylane.qchem`: molecules, molecular Hamiltonians, tapering, symmetry generators, OpenFermion conversions.
- `pennylane.fermi`, `pennylane.bose`, `pennylane.spin`: algebraic operator representations and mappings.
- `pennylane.qaoa`: QAOA layers and cost/mixer helpers.
- `pennylane.kernels`: quantum kernels and postprocessing.
- `pennylane.qcut`: circuit cutting transforms.
- `pennylane.resource` and `pennylane.estimator`: resource specs and estimates.
- `pennylane.pulse`, `pennylane.shadows`, `pennylane.ftqc`, `pennylane.liealg`: advanced physical and algorithmic workflows.

Read `sub-skills/applications-qchem-resource/` for these.

## Data, I/O, debugging, and operations support

- `pennylane.io`: OpenQASM/QASM3, Qiskit/PyQuil/Quil/Qualtran conversion surfaces; optional converters require external packages.
- `pennylane.data`: datasets and dataset manager; remote dataset operations can require network/cache decisions.
- `pennylane.debugging`: `snapshots`, breakpoints, debug measurement helpers.
- `pennylane.logging`: TOML logging configuration and decorators.
- `pennylane.pytrees` and `pennylane.concurrency`: support utilities for advanced runtime integration.

Read `sub-skills/io-data-logging/` for these.

## Source checkout development

- Tests mirror `pennylane/` layout under `tests/`.
- Source lint uses `.pylintrc`; tests use `tests/.pylintrc`; formatting uses `black` and `isort` config from `pyproject.toml`.
- `tach.toml` enforces module boundaries.
- Development docs cover adding operators, plugins, testing, architecture, deprecations, and documentation.

Read `sub-skills/repo-development/` before editing source.
