# Quantum-info workflows

## 1. Build states and operators from circuits

```python
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)

state = Statevector.from_circuit(qc)
operator = Operator.from_circuit(qc)
```

Use `Statevector.from_circuit()` for state evolution and `Operator.from_circuit()` when the circuit is unitary and matrix-level comparison is needed.

## 2. Define observables for estimators

```python
from qiskit.quantum_info import SparsePauliOp

observable = SparsePauliOp.from_list([("ZZ", 1.0), ("XX", 0.5)])
```

Use `SparsePauliOp` for Hamiltonian-like sums and estimator inputs.

## 3. Generate reproducible random objects

```python
from qiskit.quantum_info import random_unitary, random_statevector

unitary = random_unitary(4, seed=123)
state = random_statevector(4, seed=123)
```

Use seeds when a test or example must be reproducible.

## 4. Compare matrices carefully

- Use `Operator(...).equiv(...)` or predicates that support tolerance and global-phase decisions.
- Ignore global phase only when the task's physics permits it.
- Keep tensor-product ordering explicit when comparing with NumPy arrays.

## 5. Compute measures

Use the public measure helpers such as `state_fidelity`, `average_gate_fidelity`, `process_fidelity`, `entropy`, `purity`, and `partial_trace` when a task is about mathematical analysis rather than execution.
