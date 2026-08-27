# Primitives and TorchConnector: operating guide

## Select exact or sampled reference behavior

The package provides V2-style wrappers intended for Qiskit Machine Learning
networks. Use exact mode while debugging shapes, circuit composition, and
reference values; use delegate mode when the task specifically needs sampling
noise or precision-aware behavior.

### Exact `QMLEstimator`

```python
from qiskit_machine_learning.primitives import QMLEstimator

estimator = QMLEstimator()  # default_precision=0.0: exact
```

An estimator PUB contains a circuit, observable(s), and optional parameter
values. A simple call is:

```python
job = estimator.run([(circuit, [observable], parameter_values)])
result = job.result()[0]
values = result.data.evs
stds = result.data.stds
```

In exact mode, the wrapper binds broadcast parameter values, constructs a
statevector for each bound circuit, and computes analytic expectation values.
`stds` are zero and the result metadata marks `exact=True`. A per-call
`precision` is accepted for API compatibility but ignored in exact mode.
Common observable forms accepted by this wrapper include `SparsePauliOp`, a
Pauli label string, a mapping such as `{"Z": 1.0}`, and a list of label/
coefficient pairs. Observable dimensions must still match the circuit.

Use a nonzero precision only when delegate/reference behavior is desired:

```python
estimator = QMLEstimator(default_precision=0.25, seed=123)
```

This mode delegates to Qiskit's `StatevectorEstimator`, including its
precision and random-seed semantics. It is not analytically noiseless.

### Exact `QMLSampler`

```python
from qiskit import QuantumCircuit
from qiskit_machine_learning.primitives import QMLSampler

circuit = QuantumCircuit(1, 1)
circuit.h(0)
circuit.measure(0, 0)
sampler = QMLSampler()  # shots=None: exact probability container
result = sampler.run([circuit]).result()[0]
probs = result.join_data().get_probabilities()
```

Exact result containers preserve sampler-style access. A dyadic distribution
such as `{ "0": 0.5, "1": 0.5 }` can produce deterministic compatible counts
through `get_counts()`. For a non-dyadic distribution, use
`get_probabilities()` rather than forcing counts. For multiple classical
registers, use `result.join_data(["register_a", "register_b"])` and respect
register/bit ordering.

Use finite shots only when sampled behavior is required:

```python
sampler = QMLSampler(shots=256, seed=123)
result = sampler.run([circuit]).result()[0]
counts = result.join_data().get_counts()
```

Finite-shot mode delegates to `StatevectorSampler`. A per-call `shots` can
override the constructor default in delegate mode; it does not change exact
probabilities when the sampler was constructed with `shots=None`.

## Build a QNN for a connector

The connector consumes a `NeuralNetwork`, not a raw circuit. A minimal
EstimatorQNN pattern is:

```python
from qiskit_machine_learning.circuit.library import qnn_circuit
from qiskit_machine_learning.neural_networks import EstimatorQNN
from qiskit_machine_learning.primitives import QMLEstimator

circuit, input_params, weight_params = qnn_circuit(1)
qnn = EstimatorQNN(
    circuit=circuit,
    estimator=QMLEstimator(),
    input_params=input_params,
    weight_params=weight_params,
    input_gradients=True,
)
```

`input_gradients=True` is essential when a Torch model has a classical layer
before the QNN and that layer must receive gradient signal. It is also a good
explicit setting for connector gradient smoke tests. If only the connector's
own weights are optimized, input gradients may be unnecessary, but changing
this assumption later requires rebuilding or updating the QNN deliberately.

The QNN's final input dimension is authoritative. Before wrapping it, inspect:

```python
print(qnn.num_inputs, qnn.num_weights, qnn.output_shape, qnn.sparse)
```

A dataset row must satisfy `row.shape[-1] == qnn.num_inputs`. A statevector
feature is not automatically converted into a valid QNN input; choose an
appropriate amplitude-loading/state-preparation design first.

## Forward and backward behavior

Install PyTorch through the public extra:

```bash
pip install 'qiskit-machine-learning[torch]'
```

Then create a module:

```python
import numpy as np
from qiskit_machine_learning.connectors import TorchConnector

connector = TorchConnector(
    qnn,
    initial_weights=np.zeros(qnn.num_weights),
    sparse=False,
)
output = connector(input_tensor)
loss = output.sum()
loss.backward()
```

`initial_weights=None` samples weights uniformly in `[-1, 1]`; use an explicit
array or tensor for a reproducible smoke. The connector registers `.weight` as
a Torch parameter and exposes `.neural_network` and `.sparse` properties.
Forward input may be a single observation or batch; the last dimension must
match `num_inputs`. Internally, the QNN executes on NumPy arrays and the
connector returns a Torch tensor on the input device. Backward calls the QNN's
`backward` method, contracts output gradients with input/weight Jacobians, and
returns gradients on the respective devices.

A standard hybrid model is:

```python
class Hybrid(torch.nn.Module):
    def __init__(self, qnn):
        super().__init__()
        self.classical = torch.nn.Linear(qnn.num_inputs, qnn.num_inputs)
        self.quantum = TorchConnector(qnn, sparse=False)

    def forward(self, x):
        return self.quantum(self.classical(x))
```

Use `model.state_dict()`/`load_state_dict()` for saving and loading a hybrid
Torch model. Recreate the same QNN architecture and connector shape before
loading weights. The serialized state does not replace the need for compatible
circuit/QNN construction.

## Sparse mode

Install both optional dependencies when sparse QNN output is required:

```bash
pip install 'qiskit-machine-learning[torch,sparse]'
```

The compatibility matrix is:

| QNN | connector | result |
|---|---|---|
| dense | omitted/`False` | dense Torch output |
| sparse | omitted/`None` | sparse connector output |
| sparse | `False` | sparse QNN materialized to dense Torch output |
| sparse | `True` | sparse Torch COO output and sparse gradients |
| dense | `True` | error: sparse connector requires sparse network |

Sparse output is only useful when the underlying QNN actually returns sparse
arrays. Setting the connector flag alone does not make a dense QNN sparse.
Sparse Torch operations have narrower operator support than dense operations;
convert intentionally with `.to_dense()` at a boundary that can afford the
memory when a downstream Torch layer cannot consume sparse tensors.

The connector uses an Einstein-summation contraction for Jacobians. Its helper
uses lower-case letters and cannot represent more than 25 dimensions. Very
high-rank batched tensors should be flattened or handled in smaller batches
before crossing the connector boundary.

## Device behavior

CPU is the portable default. For CUDA:

```python
if torch.cuda.is_available():
    device = torch.device("cuda")
    connector = connector.to(device)
    x = x.to(device)
else:
    # select CPU or skip the CUDA trial
    device = torch.device("cpu")
```

The QNN's quantum evaluation remains a NumPy/Qiskit operation; CUDA affects
Torch tensors and Torch-side layers. A CUDA-capable Torch install, compatible
Qiskit dependencies, and an available GPU are separate requirements. Do not
hard-code a CUDA device in a general-purpose workflow.

## Loss and utility handoff

Use Torch losses (`torch.nn.MSELoss`, `CrossEntropyLoss`, and so on) for a
Torch training loop. The package's NumPy losses are under
`qiskit_machine_learning.utils.loss_functions`; they require equal prediction
and target shapes. `CrossEntropyLoss` assumes probability-like predictions,
clips them before `log2`, and its gradient assumes a softmax-style output.
Route kernel loss classes to the kernel skill and optimizer selection to the
optimizer skill.
