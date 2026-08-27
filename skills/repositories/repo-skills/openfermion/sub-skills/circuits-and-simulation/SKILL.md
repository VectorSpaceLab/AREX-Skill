---
name: circuits-and-simulation
description: "Turn OpenFermion operators and fermionic state data into bounded
  Cirq circuits, Trotter products, preparation circuits, and VPE measurement
  circuits while preserving dimension, ordering, and backend boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent: openfermion
license: Apache 2.0
---

# Circuits and simulation

Load this skill when the request is about a Trotter circuit, exponentiating a
Pauli Hamiltonian, Cirq interoperability, Slater or Gaussian-state
preparation, UCC/UCCSD generator construction, low-rank factorization helpers,
basis rotations, circuit depth, term ordering, or variational phase estimation
(VPE). This skill constructs circuit descriptions and bounded Cirq circuits; it
does not choose a physical Hamiltonian, perform operator mapping/algebra, run
external hardware, or make benchmark claims.

Use [api-reference.md](references/api-reference.md) for verified signatures and
shape contracts, [workflows.md](references/workflows.md) for recipes and
preflight checks, and [troubleshooting.md](references/troubleshooting.md) for
failure diagnosis. The bounded helper is
[scripts/circuit_smoke.py](scripts/circuit_smoke.py).

## Route before constructing

1. If the input is a model, geometry, basis, or chemistry data choice, route to
   [hamiltonians-and-chemistry](../hamiltonians-and-chemistry/SKILL.md).
2. If the work is fermion/qubit algebra, a mapping, normal ordering, or term
   simplification, route to the sibling `operators-and-transforms` skill.
3. Otherwise record the operator family, qubit/mode order, evolution time,
   Trotter order and step count, control qubit (if any), desired final qubit
   ordering, and the exact matrix/amplitude dimensions before calling an API.

## Choose the circuit boundary

- **Cirq-native fermionic simulation:** use `simulate_trotter` for an
  `InteractionOperator` or `DiagonalCoulombHamiltonian`. Choose an exposed
  algorithm explicitly when reproducibility matters: `LOW_RANK`,
  `LINEAR_SWAP_NETWORK`, or `SPLIT_OPERATOR`.
- **Qubit-Pauli product formula:** use `trotter_operator_grouping` to inspect
  ordered single-term factors, then `pauli_exp_to_qasm` or
  `trotterize_exp_qubop_to_qasm` for the package's QASM-like text output. These
  functions do not return Cirq circuits.
- **Cirq interop:** map a `QubitOperator` to a Cirq `PauliSum` with
  `qubit_operator_to_pauli_sum`, then exponentiate one commuting group at a
  time with the Cirq operation appropriate to the installed Cirq version. The
  helper uses `cirq.PauliSumExponential` for one-term groups; do not pass a
  noncommuting sum to that operation.
- **State preparation:** use `prepare_slater_determinant` for an orthonormal
  row matrix, `prepare_gaussian_state` for a `QuadraticHamiltonian`, and
  `bogoliubov_transform` for an explicit basis transformation. All emit Cirq
  operation trees consumed by `cirq.Circuit`.

## Product formulas and ordering

`simulate_trotter(..., order=0)` selects an asymmetric step; `order=1` selects
the first symmetric step, and larger positive orders recursively split that
step. `n_steps` divides the requested `time`. Swap-network algorithms can
reverse the mode-to-qubit ordering after a step. Preserve the returned
permutation or set `omit_final_swaps=True` only when the caller accepts the
reversed final ordering.

For `trotter_operator_grouping`, default term order is the sorted keys of the
`QubitOperator.terms` dictionary. A supplied `term_ordering` is an explicit
sequence of existing term keys and is part of the numerical approximation, not
just display order. Second- and third-order grouping require at least two
terms. Count factors before choosing a depth budget: first order has one pass
per step, second order has a forward/backward palindrome, and the third-order
helper expands recursively with signed coefficients.

## Dimension and convention gates

- A Slater matrix is `eta x N` with orthonormal rows; pass exactly `N` qubits.
  The initial computational-basis state has `eta` occupied modes, either the
  first `eta` modes (default integer `0` is the vacuum) or a caller-specified
  big-endian integer/index sequence.
- A Bogoliubov matrix is `(N, N)` for number-conserving transformations or
  `(N, 2*N)` for general Gaussian transformations; pass `N` qubits. A
  spin-block optimization assumes all spin-up modes precede all spin-down
  modes.
- Singlet UCCSD requires an even `n_qubits` value (spin orbitals). For
  `n_electrons`, use `n_spatial = n_qubits // 2`,
  `n_occupied = ceil(n_electrons / 2)`, and
  `n_virtual = n_spatial - n_occupied`. The exact packed length is
  `n_occupied*n_virtual + m*(m+1)//2`, where `m=n_occupied*n_virtual`.
- Low-rank decomposition expects the documented real/symmetric tensor
  contract. With `spin_basis=True`, the spin-orbital tensor must be
  spin-symmetric; spin-dependent interactions are rejected rather than
  silently downfolded.
- VPE's `qubits` sequence defines measurement bit order. Each generated circuit
  measures every supplied qubit under key `msmt`; the estimator must receive
  results in the same rotation-set order.

## Minimal bounded check

From any working directory, run:

```text
python scripts/circuit_smoke.py --help
python scripts/circuit_smoke.py --tiny
python scripts/circuit_smoke.py --tiny --with-slater
```

The helper uses a two-qubit, two-term `QubitOperator`, reports qubits,
operation count, and depth, and optionally reports a two-mode Slater
preparation. It performs no network access, file writes, plugin discovery, or
large simulation. It is a structural smoke check, not a physics benchmark.

## Boundaries and handoff

OpenFermion's circuit layer depends on Cirq for Cirq-returning primitives and
VPE circuits. Cirq itself supplies simulators, device targets, and gatesets;
OpenFermion does not install, select, or verify external hardware plugins in
this skill. QASM-like output from `pauli_exp_to_qasm` uses textual gate names
and is not a promise of OpenQASM compatibility. For actual hardware routing,
noise models, plugin simulators, or large-depth resource claims, preserve the
operator/circuit contract and route to the approved backend workflow.

A useful handoff includes: operator class and basis, qubit order, matrix/tensor
shapes, `time`, `n_steps`, formula order, explicit term ordering or algorithm,
whether swaps are retained, circuit qubits/operations/depth, and any
unresolved optional dependency or backend requirement.
