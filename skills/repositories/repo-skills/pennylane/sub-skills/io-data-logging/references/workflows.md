# I/O, data, debugging, and logging workflows

## Export a QNode to OpenQASM

```python
import pennylane as qp

dev = qp.device("default.qubit", wires=2)

@qp.qnode(dev)
def circuit(theta):
    qp.RX(theta, 0)
    qp.CNOT([0, 1])
    return qp.expval(qp.Z(1))

qasm = qp.to_openqasm(circuit, precision=6)(0.2)
print(qasm)
```

Use `wires`, `rotations`, `measure_all`, and `precision` when the target consumer has strict wire or measurement expectations.

## Import from external circuit formats

Before using a converter, run a minimal import check for the dependency it needs. Example pattern:

```python
try:
    import qiskit  # or pyquil, openqasm3, qualtran, etc.
except ModuleNotFoundError as exc:
    raise RuntimeError("Install the converter dependency for this workflow") from exc
```

Then convert a tiny circuit before converting production circuits. Validate the resulting PennyLane function/QNode by drawing or executing it on `default.qubit`.

## Load a dataset

```python
import pennylane as qp

datasets = qp.data.load(
    data_name="qchem",
    attributes=["molecule", "hamiltonian"],
    folder_path="datasets",
    progress_bar=True,
    molname="H2",
)
```

Dataset filters are dataset-specific. For offline or reproducible workflows, require a local `folder_path` with pre-downloaded data and avoid `force=True` unless the user wants to refresh cache contents.

## Use snapshots/debugging

```python
import pennylane as qp

dev = qp.device("default.qubit", wires=1)

@qp.qnode(dev)
def circuit(theta):
    qp.RX(theta, 0)
    qp.Snapshot("after_rx")
    return qp.expval(qp.Z(0))

print(qp.snapshots(circuit)(0.2))
```

Use snapshots to inspect intermediate values without permanently changing the circuit's final measurement contract.

## Configure logging

Use PennyLane logging when investigating internals or source-checkout changes. Keep logging changes local to the debugging session unless the user asks for production logging configuration. Prefer configured loggers/decorators over print statements inside library code.

## Concurrency/pytrees

For advanced runtime or integration tasks, inspect the exact live API before writing code. These utilities support PennyLane internals and advanced execution; they are not first-choice APIs for ordinary circuit examples.
