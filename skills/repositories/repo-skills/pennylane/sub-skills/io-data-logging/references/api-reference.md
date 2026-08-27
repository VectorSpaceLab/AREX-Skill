# I/O, data, debugging, and logging API reference

## Circuit conversion

Verified signatures/examples:

```python
qp.to_openqasm(circuit, wires=None, rotations=True, measure_all=True, precision=None)
qp.from_qasm(quantum_circuit: str, measurements=None)
```

Top-level converter exports include:

- `from_pyquil`
- `from_qasm`
- `to_openqasm`
- `from_qiskit`
- `from_qiskit_noise`
- `from_qiskit_op`
- `from_quil`
- `from_quil_file`
- `FromBloq`
- `bloq_registers`
- `from_qasm3`
- `to_bloq`

Many converters require optional external packages. `from_qasm` may use converter functionality from the PennyLane-Qiskit ecosystem; check imports before using it.

## Data manager

Verified signature:

```python
qp.data.load(data_name, attributes=None, folder_path=Path("datasets"),
             force=False, num_threads=50, block_size=8388608,
             progress_bar=None, **params)
```

`qp.data.load` downloads missing data and returns a list of `pennylane.data.Dataset` objects. Dataset names, attributes, and filter parameters are dataset-specific.

## Debugging

Top-level debugging exports include:

- `qp.snapshots`
- `qp.breakpoint`
- `qp.debug_expval`
- `qp.debug_state`
- `qp.debug_probs`
- `qp.debug_tape`

Snapshots/debug measurements are useful inside QNodes when inspecting intermediate states. They may interact with device and shot settings.

## Logging

`pennylane.logging` includes configuration helpers, decorators, filters, and a TOML config packaged with the repo. Use logging when diagnosing PennyLane internals or source-checkout behavior rather than adding ad-hoc prints to library code.

## Pytrees and concurrency

`pennylane.pytrees` and `pennylane.concurrency` provide support utilities for advanced execution/runtime integration. Inspect live signatures before using them in user code because they are less common than QNode/operator APIs.

## Optional dependency policy

Do not install broad `external-libraries` or docs groups just to make one converter work. Identify the exact import/converter path, install the minimum dependency, and run a tiny converter smoke.
