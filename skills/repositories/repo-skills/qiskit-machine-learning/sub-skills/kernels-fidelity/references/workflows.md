# Fidelity-kernel workflows

The examples below use public imports and user-provided data. Replace
`X_train`, `X_test`, and `y_train` with arrays of shape `(N, D)`, `(M, D)`, and
`(N,)`; do not hard-code a checkout path.

## 1. Build and inspect a statevector kernel

Use this route when exact classical simulation is adequate and a sampler or
backend is not required.

```python
import numpy as np
from qiskit.circuit.library import zz_feature_map
from qiskit_machine_learning.kernels import FidelityStatevectorKernel

D = 2
feature_map = zz_feature_map(feature_dimension=D, reps=2, entanglement="linear")
kernel = FidelityStatevectorKernel(
    feature_map=feature_map,
    cache_size=1024,
    auto_clear_cache=False,
    shots=None,
    enforce_psd=True,
)

K_train = kernel.evaluate(X_train)
K_test = kernel.evaluate(X_test, X_train)
assert K_train.shape == (len(X_train), len(X_train))
assert K_test.shape == (len(X_test), len(X_train))
assert np.allclose(K_train, K_train.T)
```

The statevector implementation computes overlap squared exactly unless `shots`
is set. With persistent cache, clear it after changing the circuit or when a
large feature set has been processed:

```python
kernel.clear_cache()
```

Do not interpret `auto_clear_cache=False` as a cache across different kernel
instances. It is per instance, and cache keys are only parameter tuples.

## 2. Build a sampler-backed fidelity kernel

Use a Qiskit sampler primitive and `ComputeUncompute` when execution should use
sampling, a backend, runtime options, or a custom fidelity implementation.

```python
from qiskit.circuit.library import zz_feature_map
from qiskit.primitives import StatevectorSampler
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from qiskit_machine_learning.state_fidelities import ComputeUncompute

feature_map = zz_feature_map(feature_dimension=2, reps=2, entanglement="linear")
sampler = StatevectorSampler()  # substitute a compatible public sampler
fidelity = ComputeUncompute(sampler=sampler, options={"shots": 1024})
kernel = FidelityQuantumKernel(
    feature_map=feature_map,
    fidelity=fidelity,
    evaluate_duplicates="off_diagonal",
    enforce_psd=True,
    max_circuits_per_job=100,
)
K_train = kernel.evaluate(X_train)
K_test = kernel.evaluate(X_test, X_train)
```

A primitive-specific options shape may differ by Qiskit release; use the
sampler's documented options and pass only supported fields. The kernel's
`max_circuits_per_job` controls how many pair circuits each fidelity `run`
submits per chunk; it does not control sampler shots.

## 3. Use precomputed matrices correctly

A precomputed SVC/SVR-style consumer expects the training matrix to be square
and the evaluation matrix to have rows for query samples and columns for the
training samples:

```python
K_train = kernel.evaluate(X_train)            # (N, N)
K_test = kernel.evaluate(X_test, X_train)     # (M, N)

# The algorithms route owns QSVC/QSVR fitting. A classical illustration is:
from sklearn.svm import SVC
model = SVC(kernel="precomputed")
model.fit(K_train, y_train)
predictions = model.predict(K_test)
```

Never pass `kernel.evaluate(X_test)` as a test matrix for a precomputed model
trained on `X_train`; that produces `(M, M)` instead of `(M, N)` and is the
wrong coordinate system. The common difficult case is a matrix that happens to
be square while representing the wrong sample set: compare both dimensions and
track the row/column sample identities.

## 4. Choose duplicate and PSD policies

Start by deciding whether diagonal/duplicate values should be measured or
forced to one:

```python
raw = FidelityQuantumKernel(
    feature_map=feature_map, fidelity=fidelity,
    evaluate_duplicates="all", enforce_psd=False,
)
stable = FidelityQuantumKernel(
    feature_map=feature_map, fidelity=fidelity,
    evaluate_duplicates="none", enforce_psd=True,
)
```

Use `all` for experiments that explicitly study sampling on identical states.
Use `off_diagonal` when training noisy kernels and you want exact unit diagonal
but still measure duplicate samples off the diagonal. Use `none` when duplicate
samples are known to represent the same state and should be skipped. Remember:
`evaluate_duplicates` affects `FidelityQuantumKernel`, not
`FidelityStatevectorKernel`; statevector evaluation skips equal statevectors
naturally, but does not offer the same named policy.

`enforce_psd` is applied only for symmetric `x_vec`/`y_vec` equality. If the
matrix has negative eigenvalues due to shots, enable it before fitting a method
that requires a valid Gram matrix. Preserve and inspect the raw matrix when
performing noise studies.

## 5. Define and bind a trainable kernel

Build the feature map with separate data and training `Parameter`s. The
training parameter sequence determines the order expected by a value sequence.

```python
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit_machine_learning.kernels import TrainableFidelityStatevectorKernel

D = 2
x = ParameterVector("x", D)
theta = ParameterVector("theta", 1)
feature_map = QuantumCircuit(D)
for q in range(D):
    feature_map.ry(theta[0], q)
    feature_map.rz(x[q], q)

kernel = TrainableFidelityStatevectorKernel(
    feature_map=feature_map,
    training_parameters=theta,
)
kernel.assign_training_parameters([0.25])
K = kernel.evaluate(X_train)
```

Use a mapping to bind named parameters or to update a subset after a complete
binding has already been made:

```python
kernel.assign_training_parameters({theta[0]: 0.5})
assert kernel.parameter_values.shape == (1,)
```

If any training value is still `None`, evaluation raises
`QiskitMachineLearningError`. The data width is `D`, not `D + len(theta)`.
The primitive-backed variant uses the same binding discipline:
`TrainableFidelityQuantumKernel(..., fidelity=fidelity, training_parameters=theta)`.

## 6. Train with QuantumKernelTrainer

Use the trainer only after a trainable kernel and labels are ready:

```python
from qiskit_machine_learning.kernels.algorithms import QuantumKernelTrainer
from qiskit_machine_learning.optimizers import SPSA
from qiskit_machine_learning.utils.loss_functions import SVCLoss

trainer = QuantumKernelTrainer(
    quantum_kernel=kernel,
    loss=SVCLoss(C=1.0),
    optimizer=SPSA(maxiter=20),
    initial_point=[0.25],
)
result = trainer.fit(X_train, y_train)
optimized_kernel = result.quantum_kernel
print(result.optimal_parameters, result.optimal_value)
```

A string such as `loss="svc_loss"` selects default loss settings. Use an
explicit loss object to pass `C`, `epsilon`, or other supported sklearn options.
`fit` raises `ValueError` if the kernel has no training parameters. The trainer
mutates the original kernel and also returns it in the result. Use the returned
`optimal_point`/`optimal_parameters` for reproducibility and report the
optimizer evaluation count.

Because these kernel losses repeatedly evaluate a matrix and fit an sklearn
precomputed model, the cost can grow rapidly with sample count, shots, and
circuit depth. Use a small smoke dataset and bounded optimizer iterations first,
then scale deliberately.
