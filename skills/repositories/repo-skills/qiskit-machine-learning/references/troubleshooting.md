# Cross-Cutting Troubleshooting

## Installation and imports

**Symptom:** `ModuleNotFoundError: qiskit_machine_learning` or `qiskit`.

- Confirm the command is using the intended Python: `python -c "import sys;
  print(sys.executable)"`.
- Install the public distribution in that same environment:
  `python -m pip install qiskit-machine-learning`.
- Check dependency consistency with `python -m pip check` and run the bundled
  `scripts/check_env.py`.
- Do not repair a user-owned environment by blindly upgrading Qiskit; isolate a
  new environment when version constraints conflict.

**Symptom:** `ImportError` mentions Torch, sparse, or NLopt.

- `TorchConnector` requires the `torch` extra; sparse output additionally
  requires `sparse`.
- The NLopt optimizer family requires the separate `nlopt` distribution.
- Use `check_env.py` without a requirement flag to see optional status, then
  install only the needed public dependency. Do not claim the optional route is
  available from a base-only import.

## Shape and circuit validation

**Symptom:** a model says the number of features, parameters, or qubits does
not match. Inspect `X.shape`, the circuit's `num_qubits`, and the exact
`input_params`/`weight_params` lists. `X` is normally two-dimensional; labels
must match the classifier/regressor output contract. Use `qnn_circuit` to align
feature-map and ansatz qubits instead of silently padding data.

**Symptom:** `SamplerQNN` returns a surprising shape. Check `interpret`,
`output_shape`, `sparse`, and whether the interpretation maps every measured
integer into the declared output domain. A parity interpretation typically uses
`output_shape=2`; a tuple interpretation needs a matching tuple shape.

**Symptom:** `TorchConnector` raises a sparse mismatch error. A connector
configured with `sparse=True` must wrap a sparse QNN, and a sparse QNN needs the
`sparse` package. Use dense mode for a dense network or install the extra and
configure both sides consistently.

## Primitive and V2 issues

**Symptom:** an estimator rejects a circuit containing measurements. Remove
classical measurements from estimator circuits; retain them for sampler
circuits. Use the migration reference for the estimator/sampler split.

**Symptom:** an IBM Runtime or backend primitive rejects a circuit or gradient
job. Transpile with a pass manager for that backend; pass the manager into
QNN/gradient/fidelity objects that create circuits; apply the resulting circuit
layout to estimator observables.

**Symptom:** sampler output cannot be found. Use a stable classical register
name such as `meas` or `c`, add measurements before transpilation, and inspect
the returned data block rather than assuming a generic `counts` attribute.

## Model and kernel issues

**Symptom:** QSVC/QSVR rejects a precomputed matrix. A training matrix must be
square with one row and column per training sample; a test matrix has one row
per test sample and one column per training sample. Confirm sample order and do
not pass a feature matrix where a precomputed kernel is expected.

**Symptom:** a kernel matrix is not positive semidefinite. Decide whether
`enforce_psd=True` is appropriate for the workflow, inspect duplicate handling,
and distinguish numerical projection from a physically meaningful fidelity
calculation. Report the policy in the experiment record.

**Symptom:** `dill` load fails or behavior changes after loading. Persist and
restore the same package-compatible primitive/circuit assumptions, record
versions and preprocessing, and treat files as trusted executable artifacts.
Do not load untrusted files merely to inspect metadata.

## Runtime and reproducibility

Set `algorithm_globals.random_seed` before data/model construction when the
workflow documents seed support. A seed does not make shot noise, backend
scheduling, or every external primitive deterministic. Report the backend,
shots/precision, optimizer budget, and score variance.

A CPU run can validate public API shape and local numerical plumbing, but it
cannot prove CUDA/ROCm/vendor/cloud behavior. For `torch.cuda`, check
`torch.cuda.is_available()` and perform a tiny device allocation before a GPU
workflow; keep device-specific native tests separate from CPU evidence.
