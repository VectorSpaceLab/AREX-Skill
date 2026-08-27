---
name: io-data-logging
description: "Use PennyLane circuit import/export, dataset loading, debugging
  snapshots, logging, pytrees, and concurrency support workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# I/O, data, debugging, and logging

Use this sub-skill when a task involves importing/exporting circuits, loading PennyLane datasets, debugging circuit execution, configuring logging, or using support utilities such as pytrees and concurrency.

## Read first

- [`references/api-reference.md`](references/api-reference.md): verified signatures and module responsibilities for I/O, data, debugging, and logging.
- [`references/workflows.md`](references/workflows.md): OpenQASM export, converter dependency checks, dataset loading, snapshots, and logging recipes.
- [`references/troubleshooting.md`](references/troubleshooting.md): optional converter imports, remote dataset/cache failures, debug measurement issues, and logging config mistakes.
- [`scripts/io_data_smoke.py`](scripts/io_data_smoke.py): safe CPU smoke for OpenQASM export and importable data/debugging/logging modules.

## Route within this sub-skill

- **Circuit export:** use `qp.to_openqasm(circuit, wires=None, rotations=True, measure_all=True, precision=None)` for OpenQASM 2 output where supported.
- **Circuit import/conversion:** use `qp.from_qasm`, `qp.from_qasm3`, `qp.from_qiskit`, `qp.from_qiskit_noise`, `qp.from_qiskit_op`, `qp.from_pyquil`, `qp.from_quil`, `qp.from_quil_file`, `qp.FromBloq`, and `qp.to_bloq` only after checking optional dependencies.
- **Datasets:** use `qp.data.load(...)` and dataset namespace utilities; treat remote downloads/cache mutation as opt-in behavior.
- **Debugging:** use `qp.snapshots`, `qp.breakpoint`, `qp.debug_expval`, `qp.debug_state`, `qp.debug_probs`, and `qp.debug_tape` for circuit introspection.
- **Logging:** use `pennylane.logging` and its TOML configuration surfaces when instrumenting PennyLane behavior.
- **Support utilities:** use `pennylane.pytrees` and `pennylane.concurrency` for advanced integration tasks after confirming exact APIs.

## Boundaries

- Circuit execution and measurements belong to [`../circuits-devices/SKILL.md`](../circuits-devices/SKILL.md).
- Operator transformations and decomposition belong to [`../operators-transforms/SKILL.md`](../operators-transforms/SKILL.md).
- Dataset-backed scientific qchem/application workflows belong to [`../applications-qchem-resource/SKILL.md`](../applications-qchem-resource/SKILL.md) when the domain module owns semantics.
- Source-checkout test/lint/development policy belongs to [`../repo-development/SKILL.md`](../repo-development/SKILL.md).

## Minimal OpenQASM export

```python
import pennylane as qp

dev = qp.device("default.qubit", wires=2)

@qp.qnode(dev)
def circuit(theta):
    qp.RX(theta, 0)
    qp.CNOT([0, 1])
    return qp.expval(qp.Z(1))

print(qp.to_openqasm(circuit)(0.2))
```

If a converter asks for Qiskit, PyQuil, OpenQASM3, or Qualtran, install and verify only that converter dependency.

## Verification cues

State whether the workflow is local-only or requires network/cache/external converter packages. For debug/logging answers, include a tiny QNode and expected printed/debug signal rather than only prose.
