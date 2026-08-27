# Provider and backend workflows

## 1. Get the basic simulator

```python
from qiskit import QuantumCircuit
from qiskit.providers.basic_provider import BasicProvider

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

backend = BasicProvider().get_backend("basic_simulator")
result = backend.run(qc, shots=128).result()
counts = result.get_counts()
```

Use this for a lightweight local execution path that does not require an external service.

## 2. Build a generic fake backend

```python
from qiskit.providers.fake_provider import GenericBackendV2

backend = GenericBackendV2(num_qubits=5, seed=42)
```

Use `GenericBackendV2` when you need a backend-like object with a target, qubit properties, basis gates, and coupling behavior for tests, examples, or transpiler setup.

## 3. Control target features

- Pass `basis_gates` to constrain the standard library gates.
- Pass a `CouplingMap` or edge list to constrain two-qubit interactions.
- Set `control_flow=True` when the fake backend should expose control-flow operations.
- Set `noise_info=False` when you need deterministic target properties without sampled noise metadata.

## 4. Work with options

Use `Options` validators to document and enforce valid backend values such as shot ranges or allowed methods. Inspect available options before forwarding user-supplied kwargs into `run()`.

## 5. Cross-link to transpiler

If the backend is used only to compile a circuit, route to the transpiler sub-skill after constructing or selecting the backend.
