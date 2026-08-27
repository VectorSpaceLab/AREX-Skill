# Algorithms API reference

All imports below are public package imports. The model classes are re-exported
from `qiskit_machine_learning.algorithms`; subpackage imports are also public.
Use the installed package's signatures as the authority when a release changes.

## Public model constructors

```python
from qiskit_machine_learning.algorithms import (
    VQC, VQR, QSVC, QSVR, PegasosQSVC,
    NeuralNetworkClassifier, NeuralNetworkRegressor, QBayesian,
)
```

The verified current signatures that matter for model construction are:

```text
VQC(num_qubits=None, feature_map=None, ansatz=None,
    loss='cross_entropy', optimizer=None, warm_start=False,
    initial_point=None, callback=None, *, sampler=None,
    interpret=None, output_shape=None, pass_manager=None)

VQR(num_qubits=None, feature_map=None, ansatz=None, observable=None,
    loss='squared_error', optimizer=None, warm_start=False,
    initial_point=None, callback=None, *, estimator=None,
    pass_manager=None)

QBayesian(circuit, *, limit=10, threshold=0.9, sampler=None,
          pass_manager=None)
```

`QSVC` and `QSVR` take `quantum_kernel` as a keyword-only model option and
forward the remaining supported keyword arguments to scikit-learn `SVC` or
`SVR`. `PegasosQSVC` takes `quantum_kernel`, `C`, `num_steps`, `precomputed`,
and `seed`.

`VQC` and `VQR` derive `num_qubits` from a supplied feature map or ansatz when
possible. If none of `num_qubits`, `feature_map`, or `ansatz` identifies a
problem size, construction raises a Qiskit Machine Learning error. Defaults
are a feature map appropriate to the qubit count and a real-amplitudes ansatz;
pass explicit circuits when dimensions or parameter counts matter.

## Data, targets, and outputs

| Model | Training input | Target contract | Typical prediction |
|---|---|---|---|
| `VQC` | `X.shape == (N, D)` | default one-hot `(N, C)`; integer/string labels can be encoded | one-hot or decoded labels, depending on target encoding |
| `VQR` | `X.shape == (N, D)` | scalar `y.shape == (N,)` for a scalar QNN output | expectation array commonly `(N, 1)` |
| `QSVC` | raw `(N, D)` or train matrix `(N, N)` in precomputed mode | 1D class labels | `(N,)` class labels |
| `QSVR` | raw `(N, D)` or train matrix `(N, N)` in precomputed mode | 1D numeric targets | `(N,)` numeric predictions |
| `PegasosQSVC` | raw `(N, D)` or train `(N, N)` if `precomputed=True` | 1D labels with exactly two unique values | labels, plus `(N, 2)` `predict_proba` |

For a VQC sampler output, `output_shape` is generally the number of classes.
`interpret` maps a measured integer to a class index (or tuple); if custom
interpretation is used, set a compatible `output_shape`. With one-hot labels,
VQC trains on rows containing exactly one `1`; multi-label rows such as
`[1, 1, 0]` are rejected. Sparse `X`/`y` are converted to dense for the
objective math, but sparse output support belongs to the QNN/data routes.

A scalar estimator output is an expectation of the selected observable. Keep
regression targets in a scale reachable by that observable (the default
Pauli-Z tensor observable has a bounded expectation). `VQR.observable` must be
a public Qiskit `BaseOperator` with the correct qubit count; a circuit is not
an observable and raises `ValueError`.

## Fit, score, state, and labels

- `fit(X, y)` returns the same model instance. Before fitting, `predict`,
  `weights`, and `fit_result` raise a not-fitted error where implemented.
- `predict(X)` uses the fitted weights. `predict_proba(X)` is available on
  neural-network classifiers and `PegasosQSVC`; it is not a generic VQR API.
- `score(X, y)` is mean accuracy for classifiers and `R^2` for regressors.
  `sample_weight` is accepted by the scikit-learn-like classifier/regressor
  score interfaces where supported.
- `weights` is a NumPy view of the optimizer's `fit_result.x`. The optimizer
  result also contains the final objective and optimizer metadata.
- `warm_start=True` makes a later fit use the previous fitted point. It does
  not make incompatible circuits, output widths, or changing class counts
  compatible.

## Loss selection

`TrainableModel` accepts one of these strings or an instance of public `Loss`:

- `absolute_error` → `L1Loss`, robust absolute residuals;
- `squared_error` → `L2Loss`, the VQR default and a smooth squared residual;
- `cross_entropy` → `CrossEntropyLoss`, the VQC default for probability vectors
  and one-hot targets.

`Loss` evaluates per sample and validates identical prediction/target shapes.
Cross entropy clips probabilities before `log2`; it still needs probability-like
outputs and correctly shaped targets. `SVCLoss`, `SVRLoss`, `MSRLoss`, `MARLoss`,
and `HuberLoss` are `KernelLoss` implementations for trainable kernel workflows,
not drop-in VQC/VQR losses; route that use to `kernels-fidelity`.

If `optimizer=None`, trainable models use the package's `SLSQP` default. A
callable minimizer must follow the public minimizer protocol and return an
optimizer result. A model callback receives `(weights, objective_value)` for
objective evaluations when the selected optimizer path supports model-level
callbacks; optimizer-specific callbacks have different signatures.

## Kernel model sharp bits

`QSVC(quantum_kernel=qkernel)` and `QSVR(quantum_kernel=qkernel)` use the
kernel object's public `evaluate` method. When `quantum_kernel=None`, each
constructs a default `FidelityQuantumKernel` (an optional `feature_map` may be
forwarded through the constructor). Passing `kernel=...` is not the supported
API; the implementation discards it with a package warning.

For `quantum_kernel="precomputed"`, fit with `K_train.shape == (N, N)` and
predict/score with `K_test.shape == (M, N)`, where the second axis is aligned to
the training rows. Do not pass raw features in this mode. `PegasosQSVC` uses
`precomputed=True` instead and requires `quantum_kernel=None` at construction.
It supports exactly two labels and runs all requested `num_steps`.

## QBayesian

The circuit represents a binary Bayesian network. Every quantum register must
contain exactly one qubit. Register names are variable labels, and the circuit's
last qubit is the most significant bit in returned bit-string keys. Evidence and
query dictionaries map those labels to `0` or `1`.

```python
samples = qb.rejection_sampling(evidence={"A": 1}, format_res=False)
probability = qb.inference(query={"B": 1}, evidence={"A": 1})
```

`rejection_sampling` returns normalized probabilities keyed by fixed-width
binary strings; `format_res=True` returns variable-labelled probability keys.
`inference` marginalizes unspecified variables. If `evidence=None`, it reuses
previous samples and raises `ValueError` when no samples exist. `limit` bounds
amplification powers (`2**limit`), `threshold` controls evidence acceptance,
and `converged` reports whether the requested evidence was reached before the
limit. A low-probability or high-threshold evidence event may remain
unconverged; inspect that property rather than treating the number as exact.
