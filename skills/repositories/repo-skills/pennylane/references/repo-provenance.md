# Repo provenance

schema: `disco.repo-provenance.v1`  
Generated skill id: `pennylane`

## Source snapshot

- Repository: PennyLane
- Public repository URL: `https://github.com/PennyLaneAI/pennylane`
- Commit: `1e73316999c18d38940a4729b869049cbea71d5f`
- Branch: `main`
- Exact tag: none detected
- Working tree state at generation: dirty because generated `skills/` artifacts were untracked
- Package version from installed editable package: `0.46.0-dev73`
- Python support from package metadata: `>=3.12`

## Evidence paths used

Package metadata and policy:

- `pyproject.toml`
- `setup.py`
- `MANIFEST.in`
- `README.md`
- `AGENTS.md`
- `.pylintrc`
- `tests/.pylintrc`
- `tach.toml`
- `conftest.py`

Public source roots:

- `pennylane/__init__.py`
- `pennylane/workflow/`
- `pennylane/devices/`
- `pennylane/measurements/`
- `pennylane/drawer/`
- `pennylane/ops/`
- `pennylane/templates/`
- `pennylane/transforms/`
- `pennylane/decomposition/`
- `pennylane/pauli/`
- `pennylane/_grad/`
- `pennylane/gradients/`
- `pennylane/math/`
- `pennylane/optimize/`
- `pennylane/qnn/`
- `pennylane/compiler/`
- `pennylane/capture/`
- `pennylane/control_flow/`
- `pennylane/qchem/`
- `pennylane/fermi/`
- `pennylane/bose/`
- `pennylane/spin/`
- `pennylane/qaoa/`
- `pennylane/kernels/`
- `pennylane/qcut/`
- `pennylane/resource/`
- `pennylane/estimator/`
- `pennylane/pulse/`
- `pennylane/shadows/`
- `pennylane/io/`
- `pennylane/data/`
- `pennylane/debugging/`
- `pennylane/logging/`
- `pennylane/pytrees/`
- `pennylane/concurrency/`
- `pennylane/labs/` and `pennylane/ftqc/` were treated as restricted or experimental areas.

Documentation and tests:

- `doc/introduction/circuits.rst`
- `doc/introduction/operations.rst`
- `doc/introduction/measurements.rst`
- `doc/introduction/templates.rst`
- `doc/introduction/interfaces.rst`
- `doc/introduction/interfaces/numpy.rst`
- `doc/introduction/interfaces/jax.rst`
- `doc/introduction/interfaces/torch.rst`
- `doc/introduction/interfaces/tf.rst`
- `doc/introduction/chemistry.rst`
- `doc/introduction/data.rst`
- `doc/introduction/importing_workflows.rst`
- `doc/introduction/logging.rst`
- `doc/development/adding_operators.rst`
- `doc/development/plugins.rst`
- `doc/development/guide/tests.rst`
- `doc/development/guide/architecture.rst`
- `doc/code/qp*.rst`
- `tests/workflow/`, `tests/devices/`, `tests/ops/`, `tests/templates/`, `tests/gradients/`, `tests/qchem/`, `tests/resource/`, `tests/estimator/`, `tests/io/`, `tests/data/`, `tests/debugging/`, and focused top-level tests.

## Environment verification summary

Private construction-time inspection used an isolated Python 3.12 environment and verified:

- Editable `pennylane` import as version `0.46.0-dev73`.
- `default.qubit` device creation.
- A tiny QNode execution.
- `qp.grad` with a trainable `qp.numpy.array` input.
- `pl-device-test --help` console script.
- `pip check` reported no broken requirements.

The generated runtime skill does not require that private environment or checkout path.
