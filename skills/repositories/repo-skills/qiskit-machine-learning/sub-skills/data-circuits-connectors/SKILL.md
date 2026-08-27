---
name: data-circuits-connectors
description: "Operate Qiskit Machine Learning's built-in datasets, circuit
  helpers, reference primitives, TorchConnector integration, and shared
  validation utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data, circuits, primitives, and connectors

Use this sub-skill when the task is about generating a built-in Qiskit Machine
Learning dataset, composing an ML circuit, evaluating a circuit with the
package's exact/reference primitives, or exposing a QNN through PyTorch. It
also covers reproducibility and small validation/loss helpers.

This sub-skill does **not** own model fitting or optimizer strategy. Route
algorithm/model-selection questions to `algorithms`, QNN gradient design to
`qnn-gradients`, fidelity-kernel behavior to `kernels-fidelity`, and optimizer
internals to `optimizers` in the surrounding graph.

## Fast routing

1. **Need data?** Read [datasets-and-circuits.md](references/datasets-and-circuits.md)
   and choose the dataset whose feature representation matches the QNN input.
2. **Need a circuit?** Check qubit count and parameter partition before building
   the QNN. Use `qnn_circuit` for a feature-map/ansatz pair or
   `raw_feature_vector` only for power-of-two amplitude dimensions.
3. **Need deterministic reference evaluation?** Read
   [primitives-and-connectors.md](references/primitives-and-connectors.md).
   `QMLEstimator()` and `QMLSampler()` are exact by default; nonzero estimator
   precision or finite sampler shots delegates to the corresponding Qiskit
   reference primitive behavior.
4. **Need PyTorch?** Install the `torch` extra, set `input_gradients=True` on
   the QNN when upstream input gradients are needed, then use
   `TorchConnector`. Keep sparse settings consistent between the QNN and
   connector.
5. **An import or shape/device error?** Start with
   [troubleshooting.md](references/troubleshooting.md), then run the linked
   scripts from any working directory:
   `python /path/to/this/skill/scripts/check_install.py --help`,
   `dataset_smoke.py --help`, and `torch_connector_smoke.py --help`.

## Operating rules

- Treat dataset feature dimension as a contract, not a hint. `ad_hoc_data`
  returns rows of length `n`; phase-of-matter and entanglement datasets return
  state vectors of dimension `2**n` (entanglement ndarray formatting adds a
  final singleton axis). A statevector feature of dimension `2**n` needs an
  `n`-qubit circuit.
- Check the return arity. The four standard values are
  `(x_train, y_train, x_test, y_test)`; `include_sample_total=True` appends a
  fifth array.
- Seed the correct generator. `ad_hoc_data` and entanglement concentration
  use `qiskit_machine_learning.utils.algorithm_globals.random_seed`; phase of
  matter has its own `seed` argument. For a PyTorch workflow also call
  `torch.manual_seed` if randomized PyTorch parameters or data ordering must
  be repeatable.
- Do not silently normalize or reshape labels. One-hot labels and scalar/string
  labels are different downstream contracts; preserve the requested
  `one_hot` mode.
- `raw_feature_vector(feature_dimension)` requires a positive power of two and
  creates `log2(feature_dimension)` qubits. Its parameterized initialize
  instruction is only defined after all amplitudes are bound and is unsuitable
  for gradient-based circuit optimization.
- `qnn_circuit` returns `(circuit, feature_map.parameters, ansatz.parameters)`.
  Explicit feature map and ansatz circuits should have matching qubit counts.
  The legacy `num_qubits`-based padding/alignment path is deprecated; construct
  matching circuits explicitly for forward compatibility.
- `TorchConnector(sparse=True)` is valid only when `neural_network.sparse` is
  also true and requires the `sparse` extra. A dense connector can materialize
  a sparse QNN result, but a sparse connector cannot wrap a dense QNN.
- A CUDA request is conditional: check `torch.cuda.is_available()` before
  selecting `cuda`. CPU is the portable default. Do not infer CUDA support from
  the package being importable.

## Canonical API index

- Dataset and circuit contracts: [datasets-and-circuits.md](references/datasets-and-circuits.md)
- Primitive and connector contracts: [primitives-and-connectors.md](references/primitives-and-connectors.md)
- Signatures, outputs, and utility index: [api-reference.md](references/api-reference.md)
- Failure diagnosis: [troubleshooting.md](references/troubleshooting.md)
- Install probe: `scripts/check_install.py`
- Deterministic dataset probe: `scripts/dataset_smoke.py`
- CPU/CUDA TorchConnector probe: `scripts/torch_connector_smoke.py`

## Minimal patterns

```python
from qiskit_machine_learning.datasets import ad_hoc_data
from qiskit_machine_learning.utils import algorithm_globals

algorithm_globals.random_seed = 1376
x_train, y_train, x_test, y_test = ad_hoc_data(
    training_size=20, test_size=10, n=2, gap=0.3
)
```

```python
from qiskit_machine_learning.circuit.library import qnn_circuit
from qiskit_machine_learning.neural_networks import EstimatorQNN
from qiskit_machine_learning.primitives import QMLEstimator

circuit, input_params, weight_params = qnn_circuit(2)
qnn = EstimatorQNN(
    circuit=circuit,
    input_params=input_params,
    weight_params=weight_params,
    estimator=QMLEstimator(),
    input_gradients=True,  # required for gradients into an upstream torch layer
)
```

```python
# Optional dependency: pip install 'qiskit-machine-learning[torch]'
from qiskit_machine_learning.connectors import TorchConnector

model = TorchConnector(qnn, initial_weights=[0.0] * qnn.num_weights)
```

Use the references for parameter validation, output shapes, exact-vs-sampled
semantics, and recovery steps; keep this file as the routing surface.
