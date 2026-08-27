# Application workflows

## Resource specs for a QNode

```python
import pennylane as qp

dev = qp.device("default.qubit", wires=2)

@qp.qnode(dev)
def circuit(theta):
    qp.RX(theta, 0)
    qp.CNOT([0, 1])
    return qp.expval(qp.Z(1))

spec_fn = qp.specs(circuit)
print(spec_fn(0.2))
```

Use this for quick circuit depth, gate counts, wires, and related specs. If the user needs target hardware/gate-set estimates, consider `qp.estimator.estimate` and state the gate set.

## Estimate resources

```python
resources = qp.estimator.estimate(circuit)(0.2)
print(resources)
```

Set `gate_set`, `zeroed_wires`, `any_state_wires`, and `tight_wires_budget` only when the target compilation/resource model requires them.

## Tiny qchem setup

```python
import pennylane as qp

symbols = ["H", "H"]
coordinates = qp.numpy.array([[0.0, 0.0, -0.35], [0.0, 0.0, 0.35]])
mol = qp.qchem.Molecule(symbols, coordinates, unit="angstrom")
print(mol.n_electrons)
```

To produce a molecular Hamiltonian, confirm optional chemistry dependencies and choose `method`, `basis_name`, `mapping`, active electrons/orbitals, and units deliberately. Keep tiny molecules for smoke tests.

## Map fermionic operators

```python
fw = qp.FermiWord({(0, 0): "+", (1, 1): "-"})
qubit_op = qp.jordan_wigner(fw)
print(qubit_op)
```

After mapping, use operator tools such as `qp.simplify`, `qp.matrix`, or `qp.pauli_decompose` as needed.

## QAOA sketch

Use `qp.qaoa` when the problem is naturally expressed as cost/mixer Hamiltonians and alternating layers. Validate the Hamiltonian/operator shape first, then build a QNode with trainable layer parameters. Route gradient/training-loop details to the gradients sub-skill.

## Kernels and qcut

- Kernels: start from a feature-map QNode and a small Gram-matrix or kernel-value check. Optional CVX dependencies may be needed for postprocessing/cost functions.
- Qcut: start by drawing the circuit and identifying cut points. For Monte Carlo cutting, document shots and randomness. KAHYPAR/partitioner-dependent workflows need optional dependencies.

## Shadows and pulse

- Classical shadows require finite-shot thinking and postprocessing; define what observable or expectation will be recovered.
- Pulse workflows use parametrized Hamiltonians and may be device/backend-specific. Keep examples small and state time/parameter conventions.
