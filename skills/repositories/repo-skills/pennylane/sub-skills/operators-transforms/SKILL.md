---
name: operators-transforms
description: "Use PennyLane operations, templates, observables, op math,
  decompositions, compile pipelines, transforms, and custom-operator
  validation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Operators, templates, and transforms

Use this sub-skill when a task asks which operation/template to use, how to compose observables, how to inspect operator matrices/eigenvalues, how to decompose or compile a circuit, or how to add/validate custom operators.

## Read first

- [`references/api-reference.md`](references/api-reference.md): verified signatures and API groups for operations, templates, op math, and transforms.
- [`references/workflows.md`](references/workflows.md): recipes for operator composition, template shape checks, decomposition/compile, and custom operators.
- [`references/troubleshooting.md`](references/troubleshooting.md): shape, wire, differentiability, decomposition, and custom-operator failures.
- [`scripts/operator_validation.py`](scripts/operator_validation.py): tiny custom operator plus `assert_valid` check.
- [`scripts/decompose_smoke.py`](scripts/decompose_smoke.py): safe decomposition/compile smoke.

## Route within this sub-skill

- **Basic gates and observables:** use top-level gates like `qp.RX`, `qp.RY`, `qp.RZ`, `qp.CNOT`, `qp.Hadamard`, `qp.PauliX/Y/Z`, and measurement observables through circuits/devices.
- **Templates:** use `qp.AngleEmbedding`, `qp.AmplitudeEmbedding`, `qp.StronglyEntanglingLayers`, state-preparation templates, subroutines, and tensor-network templates when a workflow needs reusable ansatz structure.
- **Operator arithmetic:** use `qp.sum`, `qp.prod`, `qp.s_prod`, `qp.pow`, `qp.adjoint`, `qp.ctrl`, `qp.cond`, `qp.exp`, `qp.dot`, `qp.commutator`, and `qp.pauli_decompose` to compose or analyze operators.
- **Inspection:** use `qp.matrix`, `qp.eigvals`, `qp.generator`, `qp.is_unitary`, `qp.is_hermitian`, `qp.is_commuting`, `qp.equal`, `qp.assert_equal`, `qp.simplify`, and `qp.map_wires`.
- **Transforms:** use `qp.transform` for custom tape transforms; use packaged transforms such as `qp.compile`, `qp.decompose`, batching transforms, `qp.defer_measurements`, dynamic-one-shot, Clifford+T decomposition, and pattern matching.
- **Custom operators:** route to the custom-operator workflow and validate with `pennylane.ops.functions.assert_valid(op)`.

## Boundaries

- Device, measurement execution, shots, and drawing are owned by [`../circuits-devices/SKILL.md`](../circuits-devices/SKILL.md).
- Gradient transforms and differentiability choices are owned by [`../gradients-interfaces/SKILL.md`](../gradients-interfaces/SKILL.md).
- Qchem/fermionic/bosonic/spin operator mappings are owned by [`../applications-qchem-resource/SKILL.md`](../applications-qchem-resource/SKILL.md), but the resulting qubit operators can be inspected here.
- Source-code lint/test/contribution policy is owned by [`../repo-development/SKILL.md`](../repo-development/SKILL.md).

## Minimal pattern

```python
import pennylane as qp

op = 0.5 * qp.PauliZ(0) + qp.PauliX(1) @ qp.PauliZ(2)
print(qp.simplify(op))
print(qp.matrix(qp.RX(0.2, wires=0)))

@qp.qnode(qp.device("default.qubit", wires=3))
def circuit(x):
    qp.AngleEmbedding(x, wires=range(3), rotation="Y")
    qp.StronglyEntanglingLayers(qp.numpy.zeros((1, 3, 3)), wires=range(3))
    return qp.expval(op)

print(qp.draw(qp.compile(circuit))(qp.numpy.array([0.1, 0.2, 0.3])))
```

## Verification cues

For a useful answer, include expected parameter shapes, wire conventions, transform level (`user`, `device`, or `gradient`) when drawing/compiling, and a validation step such as `assert_valid`, `qp.matrix`, `qp.draw`, or focused tests for source changes.
