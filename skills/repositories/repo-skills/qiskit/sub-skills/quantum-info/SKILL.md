---
name: quantum-info
description: "Guides agents using Qiskit quantum-information states, operators,
  observables, channels, random generators, predicates, and measures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qiskit quantum-info workflows

Use this sub-skill when the task is about mathematical objects in `qiskit.quantum_info`: states, operators, observables, channels, random generators, matrix predicates, and fidelity or entropy measures.

## Read next

- `references/workflows.md` for common state, operator, Pauli, random-object, and measure recipes.
- `references/troubleshooting.md` for dimension, measurement, optional-dependency, and numerical-tolerance failures.
- `../../references/module-map.md` for route boundaries.
- `../../scripts/check_qiskit_environment.py --sections quantum-info` for a source-free quantum-info smoke check.

## Include here

- `Statevector`, `DensityMatrix`, `StabilizerState`, and state utilities.
- `Operator`, `ScalarOp`, `SparsePauliOp`, `Pauli`, `Clifford`, sparse Pauli types, and channel objects.
- Random generators such as `random_statevector`, `random_unitary`, `random_pauli`, and `random_quantum_channel`.
- Fidelity, entropy, purity, partial trace, commutator, and matrix-predicate workflows.

## Exclude or route elsewhere

- Constructing a circuit before analysis belongs in `../circuit/SKILL.md`.
- Compiling for a backend belongs in `../transpiler/SKILL.md`.
- Running samplers/estimators belongs in `../primitives/SKILL.md`.
- Saving objects as QASM/QPY belongs in `../serialization/SKILL.md`.
- Plotting states or histograms belongs in `../visualization/SKILL.md`.

## Default route

Start here when the user asks about amplitudes, matrices, state evolution, observables, Pauli operators, fidelity, or why two circuits are equivalent up to global phase.

## What to remember

- State and operator objects grow exponentially in qubit count; avoid full matrices for large circuits.
- `Operator.from_circuit()` expects a unitary-like circuit, while measured circuits are often not valid operator inputs.
- Use `SparsePauliOp` for estimator observables and Hamiltonian-like sums.
- Always state the tolerance and whether global phase should be ignored when comparing matrices.
