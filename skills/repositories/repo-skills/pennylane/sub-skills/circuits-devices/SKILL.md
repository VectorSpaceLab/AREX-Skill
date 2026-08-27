---
name: circuits-devices
description: "Build and debug PennyLane QNodes, devices, measurements, shots,
  drawing, and device-test CLI workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Circuits, QNodes, devices, and measurements

Use this sub-skill when the task asks how to create, execute, inspect, or debug PennyLane circuits. It owns QNodes, device selection, measurements, shots, drawing, mid-circuit measurement routing, and the device-test CLI.

## Read first

- [`references/api-reference.md`](references/api-reference.md): signatures and core objects for `QNode`, `qnode`, `device`, measurements, drawing, and `execute`.
- [`references/workflows.md`](references/workflows.md): recipes for QNode creation, finite shots, drawing, and device-test checks.
- [`references/troubleshooting.md`](references/troubleshooting.md): device, wire, shot, measurement-shape, and mid-circuit failure modes.
- [`scripts/qnode_smoke.py`](scripts/qnode_smoke.py): safe CPU QNode smoke script.
- [`scripts/device_help.sh`](scripts/device_help.sh): helper to display `pl-device-test --help` when the console script is installed.

## Route within this sub-skill

- **Basic circuit creation:** use `qp.device(...)`, define a quantum function with operations, return measurement processes, and wrap it with `@qp.qnode(dev)` or `qp.QNode(func, dev)`.
- **Device choice:** start with `default.qubit` for ordinary pure-state CPU simulation; use `default.mixed` for noisy/mixed-state workflows, `default.clifford` for Clifford circuits, `default.tensor` for tensor-network style simulation, `reference.qubit` for reference checks, and `null.qubit` for dry/resource-like runs.
- **Measurements:** use `qp.expval`, `qp.var`, `qp.probs`, `qp.sample`, `qp.counts`, `qp.state`, `qp.density_matrix`, entropy/purity/mutual-info functions, and shadows according to the requested return type.
- **Shots:** analytic workflows use exact-style returns; sampling/counts require finite shots. Use `qp.set_shots` or QNode/device update methods when changing shot behavior.
- **Drawing/inspection:** use `qp.draw(qnode)(*args)` for text diagrams and `qp.draw_mpl(qnode)(*args)` for Matplotlib figures.
- **Plugin/device validation:** use `pl-device-test --help` first, then choose explicit `--device`, `--shots`, `--analytic`, and `--device-kwargs` values.

## Boundaries

- Operations/templates and circuit transforms are owned by [`../operators-transforms/SKILL.md`](../operators-transforms/SKILL.md).
- Gradients/interfaces/training are owned by [`../gradients-interfaces/SKILL.md`](../gradients-interfaces/SKILL.md).
- Domain modules such as qchem/qcut/resource are owned by [`../applications-qchem-resource/SKILL.md`](../applications-qchem-resource/SKILL.md).
- Import/export, datasets, logging, and debugging snapshots are owned by [`../io-data-logging/SKILL.md`](../io-data-logging/SKILL.md), although snapshot measurements can be used inside circuits.
- Source-checkout test/lint policy is owned by [`../repo-development/SKILL.md`](../repo-development/SKILL.md).

## Minimal pattern

```python
import pennylane as qp

angles = qp.numpy.array([0.1, 0.2], requires_grad=True)
dev = qp.device("default.qubit", wires=2)

@qp.qnode(dev)
def circuit(params):
    qp.RX(params[0], wires=0)
    qp.CNOT(wires=[0, 1])
    qp.RY(params[1], wires=1)
    return qp.expval(qp.Z(1))

value = circuit(angles)
print(value)
print(qp.draw(circuit)(angles))
```

## Verification cues

A good answer or code change in this area should state the chosen device, wires, shot setting, measurement return shape, interface/diff assumptions if gradients are involved, and a tiny QNode smoke check. For source-checkout changes, native candidates include QNode, device, and measurement tests mirrored under `tests/workflow/`, `tests/devices/`, and `tests/measurements/`.
