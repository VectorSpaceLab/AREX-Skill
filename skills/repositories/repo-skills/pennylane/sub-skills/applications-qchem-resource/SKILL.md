---
name: applications-qchem-resource
description: "Use PennyLane application modules for qchem, mappings, QAOA,
  kernels, qcut, shadows, pulse, resources, and estimator workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Application modules, qchem, and resources

Use this sub-skill when a task moves beyond a basic circuit into PennyLane application modules: quantum chemistry, fermionic/bosonic/spin mappings, QAOA, kernels, circuit cutting, shadows, pulse/FTQC notes, resource specs, or the estimator.

## Read first

- [`references/api-reference.md`](references/api-reference.md): module map and verified signatures for qchem/resource/estimator examples.
- [`references/workflows.md`](references/workflows.md): tiny qchem, resource, qcut/kernel, and mapping workflows.
- [`references/troubleshooting.md`](references/troubleshooting.md): optional dependency, dataset, backend, and scale pitfalls for application modules.
- [`scripts/resource_and_qchem_smoke.py`](scripts/resource_and_qchem_smoke.py): safe CPU smoke for resource specs and a minimal qchem object.

## Route within this sub-skill

- **Quantum chemistry:** `qp.qchem.Molecule`, `qp.qchem.molecular_hamiltonian`, tapering, symmetry generators, OpenFermion conversions, basis/structure utilities.
- **Operator mappings:** `qp.FermiWord`, `qp.FermiSentence`, `qp.jordan_wigner`, `qp.parity_transform`, `qp.bravyi_kitaev`, `qp.BoseWord`, `qp.BoseSentence`, `qp.binary_mapping`, `qp.unary_mapping`, `qp.christiansen_mapping`, and spin utilities.
- **Algorithms:** `qp.qaoa`, `qp.kernels`, `qp.qcut`, `qp.shadows`, `qp.pulse`, `qp.ftqc`, and `qp.liealg` where evidence and optional dependencies support the request.
- **Resource estimation:** `qp.specs(qnode)` for circuit specs, `qp.resource` for resource-level objects, and `qp.estimator.estimate` for estimator workflows.

## Boundaries

- Use [`../operators-transforms/SKILL.md`](../operators-transforms/SKILL.md) for low-level operator arithmetic, matrices, transforms, and custom operators.
- Use [`../circuits-devices/SKILL.md`](../circuits-devices/SKILL.md) for QNode/device/measurement execution details.
- Use [`../gradients-interfaces/SKILL.md`](../gradients-interfaces/SKILL.md) for differentiating variational algorithms.
- Use [`../io-data-logging/SKILL.md`](../io-data-logging/SKILL.md) for importing/exporting circuits or remote datasets.

## Minimal patterns

Resource specs:

```python
import pennylane as qp

dev = qp.device("default.qubit", wires=2)

@qp.qnode(dev)
def circuit(theta):
    qp.RX(theta, 0)
    qp.CNOT([0, 1])
    return qp.expval(qp.Z(1))

print(qp.specs(circuit)(0.2))
```

Tiny qchem object without external solver work:

```python
symbols = ["H", "H"]
coordinates = qp.numpy.array([[0.0, 0.0, -0.35], [0.0, 0.0, 0.35]])
mol = qp.qchem.Molecule(symbols, coordinates, unit="angstrom")
print(mol.n_electrons)
```

## Verification cues

State optional dependency requirements up front. Many application workflows are CPU-capable in small cases but may need external chemistry solvers, CVX/KAHYPAR/opt_einsum, OpenQASM/Qualtran/Qiskit integrations, or accelerator plugins for scale. Use tiny local examples before promising a full scientific workflow.
