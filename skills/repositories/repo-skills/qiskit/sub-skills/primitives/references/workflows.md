# Primitive workflows

## 1. Sample a measured circuit

```python
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

sampler = StatevectorSampler(seed=123)
result = sampler.run([qc], shots=128).result()[0]
counts = result.data[next(iter(result.data.keys()))].get_counts()
```

Use this for Bell states, GHZ states, or any other sampling-style circuit.

## 2. Estimate an observable

```python
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp

qc = QuantumCircuit(1)
qc.h(0)

estimator = StatevectorEstimator()
ev = estimator.run([(qc, SparsePauliOp("Z"))]).result()[0].data.evs
```

Use this when the user cares about expectation values instead of bitstring counts.

## 3. Sweep parameters

- Pass parameter values together with the circuit in the convenience tuple form.
- Use `SamplerPub` and `EstimatorPub` when you want to make the PUB structure explicit.
- Keep the circuit and the sweep binding shape aligned so the result container shape is predictable.

## 4. Read results safely

- For sampler outputs, inspect the `DataBin` key names before assuming a field name.
- For estimator outputs, read `result[0].data.evs` and metadata such as target precision.
- Use the primitive job's `result()` method rather than peeking into internals.

## 5. Common primitive choices

- Use `StatevectorSampler` for quick deterministic reference sampling.
- Use `StatevectorEstimator` for reference expectation values without involving an external backend.
- Use a backend-specific primitive implementation only when the workflow explicitly needs hardware or simulator behavior beyond the reference statevector path.
