# Kernel and fidelity API reference

This reference reflects the inspected Qiskit Machine Learning implementation.
Check the installed package's public API for version-specific changes before
copying an example into a long-lived application.

## Common kernel contract

`BaseKernel` is an abstract interface with:

```python
BaseKernel(*, feature_map=None, enforce_psd=True)
```

The feature map is required in the current implementation: a missing map raises
`QiskitMachineLearningError`. `num_features` starts as
`feature_map.num_parameters`. `evaluate(x_vec, y_vec=None)` returns a 2-D
`(N, M)` matrix, with `y_vec=None` meaning the self/symmetric case. Inputs may
be one- or two-dimensional arrays. A one-dimensional input is reshaped as one
sample. Inputs with more than two dimensions, empty/shape-invalid arrays, or
incompatible `x_vec`/`y_vec` feature dimensions raise `ValueError`.

When the input width differs from the feature map's parameter count, the base
validation attempts to adjust `feature_map.num_qubits`; this only works for
feature maps that permit that assignment. If it cannot adjust the circuit, the
kernel raises a dimension `ValueError`. Treat explicit feature-map/input width
matching as the portable contract rather than depending on this adjustment.

`enforce_psd` applies only to symmetric evaluation. The implementation projects
the matrix by replacing negative eigenvalues with zero. This is especially
relevant for shot/noise-affected matrices. It is not a general repair for an
asymmetric train/test matrix.

## FidelityQuantumKernel

Current constructor:

```python
FidelityQuantumKernel(
    *, feature_map=None, fidelity=None, enforce_psd=True,
    evaluate_duplicates="off_diagonal", max_circuits_per_job=None,
)
```

- `fidelity` is a `BaseStateFidelity`. If omitted, the implementation creates
  `ComputeUncompute(sampler=QMLSampler())`.
- `evaluate_duplicates` is case-normalized and must be `"all"`,
  `"off_diagonal"`, or `"none"`; an invalid value raises `ValueError`.
- `max_circuits_per_job` is `None` or an integer at least 1. A positive value
  chunks fidelity calls; it does not change the matrix semantics.
- `evaluate(X)` recognizes a symmetric case and evaluates only the upper
  triangular non-trivial pairs, mirroring values into the lower triangle. If
  `y_vec` is supplied and is array-equal to `x_vec`, it is still treated as
  symmetric; otherwise the output is asymmetric with shape `(len(X), len(Y))`.
- Kernel entries are fidelity values
  `|<phi(x)|phi(y)>|**2`. Trivial entries are initialized to `1.0`.

Duplicate policy is applied during parameterization:

| Policy | Symmetric training (`evaluate(X)`) | Asymmetric/inference behavior |
|---|---|---|
| `all` | Evaluate every pair, including diagonal and duplicate samples; exposes sampling noise. | Evaluate every pair. |
| `off_diagonal` | Set the diagonal to `1`; evaluate other pairs, including duplicate off-diagonal samples. | Evaluate every pair. |
| `none` | Set diagonal and all equal-sample pairs to `1`; skip those fidelity calls. | Set equal `x_i`/`y_j` entries to `1`; skip them. |

The default `off_diagonal` is a useful noisy-training compromise: it avoids
noisy diagonal estimates while retaining duplicate off-diagonal estimates.

## FidelityStatevectorKernel

Current constructor:

```python
FidelityStatevectorKernel(
    *, feature_map=None, statevector_type=Statevector, cache_size=None,
    auto_clear_cache=True, shots=None, enforce_psd=True,
)
```

It evaluates statevectors from the feature map and computes exact overlap
squared with `abs(conj(x) @ y) ** 2`. Equal statevector arrays are left at `1`.
`statevector_type` must be a compatible `Statevector` subclass; optional Aer
statevectors require the separately installed Aer package and compatible
platform/runtime.

The per-instance statevector cache is an `lru_cache` keyed by parameter tuples:

- `cache_size=None` is unbounded; an integer bounds retained entries.
- `auto_clear_cache=True` clears the cache at the start of every `evaluate`.
- Set `auto_clear_cache=False` to reuse states across calls, and call
  `clear_cache()` after changing the feature map or when memory must be released.
- The implementation supports pickling by recreating the cache on unpickle.

If `shots` is `None`, fidelity is exact and `enforce_psd` has no effect on the
usual exact symmetric result. If `shots` is an integer, each nontrivial entry
is sampled from a binomial distribution with exact fidelity as probability and
then divided by `shots`; PSD projection is applied for symmetric calls when
`enforce_psd=True`. Shot emulation models compute-uncompute sampling, not an
arbitrary backend noise model.

## Trainable kernels

`TrainableKernel` adds:

```python
assign_training_parameters(values_or_mapping) -> None
parameter_values -> numpy.ndarray
training_parameters
num_training_parameters
```

A sequence must have exactly `num_training_parameters` values. A mapping may
bind a subset, but every parameter must be bound before `evaluate`; otherwise
`QiskitMachineLearningError` is raised. Unknown mapping keys raise `ValueError`.

`TrainableFidelityQuantumKernel` combines `TrainableKernel` and
`FidelityQuantumKernel`; `TrainableFidelityStatevectorKernel` combines it with
`FidelityStatevectorKernel`. Both require an explicit feature map and accept
`training_parameters` as a `ParameterVector` or sequence of `Parameter`s. The
remaining circuit parameters are the data features, so the effective
`num_features` is `feature_map.num_parameters - num_training_parameters`.
The feature and training parameter order is managed internally; pass data with
width equal to the effective feature count, not the total circuit parameter
count.

## ComputeUncompute

Current constructor:

```python
ComputeUncompute(
    sampler, *, options=None, local=False, pass_manager=None
)
```

`sampler` is the sampler primitive used for execution. `options` are default
runtime options; options passed to `run` take precedence over fidelity defaults,
which take precedence over sampler defaults. `local=False` estimates the global
probability of measuring all zeros after compute-uncompute. `local=True` averages
single-qubit zero projectors and is a different observable; it can be useful for
trainability but is not the standard global fidelity. `pass_manager`, when
provided, runs on each constructed compute-uncompute circuit before submission.

`run(circuits_1, circuits_2, values_1=None, values_2=None, **options)` returns an
asynchronous job. `circuits_1` and `circuits_2` may each be a circuit or equal-
length sequences. Parameter values accept one-dimensional or two-dimensional
sequences/NumPy arrays; left and right values are concatenated for the
reparameterized fidelity circuit. A circuit with free parameters requires
corresponding values. Mismatched list lengths or qubit counts raise `ValueError`.
The result is `StateFidelityResult` with truncated `fidelities` in `[0, 1]`,
`raw_fidelities`, `metadata`, and effective `options`.

`ComputeUncompute` removes final measurements from input circuits, composes the
first with the inverse of the second, measures all, optionally applies the pass
manager, and samples the resulting circuit. A zero-circuit list is invalid.
Runtime failures are wrapped as `AlgorithmError("Sampler job failed!")`.

## Kernel trainer and losses

`QuantumKernelTrainer` accepts:

```python
QuantumKernelTrainer(
    quantum_kernel, loss=None, optimizer=None, initial_point=None
)
```

`quantum_kernel` must be a `TrainableKernel`. `loss=None` defaults to `SVCLoss`;
accepted strings are `svc_loss`, `svr_loss`, `msr_loss`, `mar_loss`, and
`huber_loss`. A string creates the corresponding loss with default options; use
an explicit loss instance to pass options (for example `SVCLoss(C=0.8)`).
`optimizer=None` defaults to `SPSA`. The trainer docs explicitly caution that
analytical-gradient optimizers are not recommended because kernel losses do not
provide an analytical gradient. `initial_point`, if supplied, must have one
value per trainable parameter; otherwise the trainer samples an initial point
from `algorithm_globals.random`.

`fit(data, labels)` requires at least one trainable parameter. It repeatedly
binds parameters, evaluates a training kernel, and minimizes the selected loss.
The input trainable kernel is mutated in place to the optimized parameters. The
returned `QuantumKernelTrainerResult` exposes `optimal_point`,
`optimal_parameters`, `optimal_value`, `optimizer_evals`, and `quantum_kernel`.

Loss classes in `qiskit_machine_learning.utils.loss_functions`:

- `SVCLoss(**kwargs)`: fits sklearn `SVC(kernel="precomputed")` and evaluates
  the SVM dual objective proxy.
- `SVRLoss(**kwargs)`: fits precomputed-kernel `SVR` and returns its dual
  objective expression.
- `MSRLoss(**kwargs)` and `MARLoss(**kwargs)`: fit precomputed-kernel `SVR`
  and return mean squared or mean absolute training error.
- `HuberLoss(delta=1.0, **kwargs)`: fits precomputed-kernel `SVR` and computes
  Huber error with the given threshold.

These losses require scikit-learn and correctly shaped labeled data. They are
training objectives, not the same as held-out model metrics. Classical SVC/SVR
fit and model selection are outside this sub-skill; pass the optimized kernel to
the algorithms route for QSVC/QSVR use.
