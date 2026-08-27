# Serialization workflows

## 1. Choose the format

| Goal | Prefer |
| --- | --- |
| Human-readable OpenQASM 2 interchange with simple circuits | `qiskit.qasm2` |
| Modern OpenQASM 3 interchange and dynamic-circuit syntax | `qiskit.qasm3` |
| Full-fidelity Qiskit circuit persistence across systems and Python versions | `qiskit.qpy` |

## 2. OpenQASM 2 round-trip

```python
from qiskit import QuantumCircuit, qasm2

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

text = qasm2.dumps(qc)
round_tripped = qasm2.loads(text)
```

Use `strict=True` when you want closer conformance to the OpenQASM 2 specification. Use custom-instruction and custom-classical definitions when source programs use extensions.

## 3. OpenQASM 3 export and import

```python
from qiskit import qasm3

text = qasm3.dumps(qc)
parsed = qasm3.loads(text)
```

The compatibility import path needs `qiskit-qasm3-import` installed. If the task mentions the native parser, use `load_experimental()` or `loads_experimental()` and warn that the interface is experimental.

## 4. QPY binary persistence

```python
import io
from qiskit import qpy

buffer = io.BytesIO()
qpy.dump(qc, buffer)
buffer.seek(0)
loaded = qpy.load(buffer)[0]
```

Use QPY when losing Qiskit-specific structure would be a problem. Set a lower `version=` only when the target Qiskit release supports that version and the circuit contains no unsupported features.

## 5. File and stream rules

- QASM2 and QASM3 loaders accept filenames or strings through separate `load`/`loads` functions.
- QPY uses binary file objects; open files as `"wb"` for dumping and `"rb"` for loading.
- QASM text streams use text mode.
