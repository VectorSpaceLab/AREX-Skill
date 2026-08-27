# Repository Provenance

- Schema: `disco.repo-provenance.v1`
- Source repository: public `qiskit-community/qiskit-machine-learning`
- Source commit: `3bdcce7e39aaca0700a7a7fcfba79230a8825a41`
- Branch at extraction: `main`
- Exact tag at extraction: none
- Package version: `1.0.0`
- Source checkout state at extraction: clean at the source snapshot; the
  generated skill and review artifacts were added afterward under `skills/`.
- Public remote: `https://github.com/qiskit-community/qiskit-machine-learning`
- Extraction date: 2026-08-22

## Evidence paths

- `qiskit_machine_learning/` — public implementation and import packages.
- `qiskit_machine_learning/algorithms/` — classifiers, regressors, inference,
  objective functions, and model infrastructure.
- `qiskit_machine_learning/neural_networks/` and `gradients/` — QNNs,
  effective dimension, gradients, QFI, and QGT.
- `qiskit_machine_learning/kernels/` and `state_fidelities/` — kernels,
  trainable kernels, trainers, and fidelity circuits.
- `qiskit_machine_learning/optimizers/` — optimizer families and support
  contracts.
- `qiskit_machine_learning/datasets/`, `circuit/`, `primitives/`,
  `connectors/`, and `utils/` — data, circuits, reference primitives,
  PyTorch integration, and validation utilities.
- `README.md`, `docs/getting_started.rst`, `docs/index.rst`,
  `docs/apidocs/`, `docs/tutorials/`, and
  `docs/migration/02_migration_guide_0.8.rst` — public installation, recipes,
  API organization, tutorials, and migration sharp bits.
- `test/` — behavior and edge-case evidence used for candidate verification;
  tests are not runtime dependencies of this skill.
- `setup.py`, `pyproject.toml`, `requirements.txt`, `tox.ini`, and
  `qiskit_machine_learning/VERSION.txt` — package metadata and dependency
  evidence.

## Refresh baseline

Refresh this skill when public modules, constructor signatures, primitive
versions, optional extras, V2 migration behavior, or tutorial contracts change.
Compare the current repository commit and `VERSION.txt` with this snapshot;
do not assume a source checkout is present when using the runtime skill.
