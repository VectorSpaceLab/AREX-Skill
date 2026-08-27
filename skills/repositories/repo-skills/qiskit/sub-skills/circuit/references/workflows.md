# Circuit workflows

## 1. Build a minimal circuit

```python
from qiskit import QuantumCircuit

qc = QuantumCircuit(3)
qc.h(0)
qc.cx(0, 1)
qc.cx(0, 2)
```

Use this pattern when the task is simply to create an abstract circuit from scratch. Add classical bits only when the workflow needs measurement, conditionals, or data capture.

## 2. Work with parameters

```python
from qiskit.circuit import Parameter
from qiskit import QuantumCircuit

theta = Parameter("theta")
qc = QuantumCircuit(1)
qc.ry(theta, 0)
qc_bound = qc.assign_parameters({theta: 3.14159})
```

Use parameters for symbolic circuit families, sweeps, and variational workflows. Keep the bound and unbound circuit separate when you need both forms.

## 3. Compose and reuse circuit fragments

```python
from qiskit import QuantumCircuit

bell = QuantumCircuit(2, name="bell")
bell.h(0)
bell.cx(0, 1)

outer = QuantumCircuit(2)
outer.append(bell.to_gate(), [0, 1])
```

Prefer `to_gate()` or `compose()` when a subcircuit should be reused. Use explicit names when you want readable exports or drawings.

## 4. Add control flow

```python
from qiskit import QuantumCircuit

qc = QuantumCircuit(2, 2)
with qc.if_test((qc.clbits[0], 1)):
    qc.x(1)
```

Use the control-flow builders for dynamic circuits with runtime decisions. Make sure the classical condition is valid for the circuit's bits and registers.

## 5. Draw for review

For a quick textual check, `qc.draw(output="text")` is usually enough. Use the visualization sub-skill when the question is about image output, styles, or plotting dependencies.

## 6. Common circuit-library patterns

- Use `QuantumCircuit.measure_all()` for sampling-style workflows.
- Use `QuantumCircuit.measure()` when you need a specific classical layout.
- Use `QuantumCircuit.reset()` when modeling mid-circuit reinitialization or dynamic control.
- Use `circuit.library` gates and templates rather than hand-building standard structures every time.
