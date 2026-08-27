# Circuit and simulation API reference

The signatures below are the public OpenFermion interfaces used by this
sub-skill. Cirq objects are passed through or returned by operation-tree
iterators; materialize them with `cirq.Circuit(...)` when a circuit, depth, or
simulation is needed.

## Pauli products and QASM-like output

| API | Contract and important parameters |
|---|---|
| `trotter_operator_grouping(hamiltonian, trotter_number=1, trotter_order=1, term_ordering=None, k_exp=1.0)` | Accepts a non-empty `QubitOperator` and yields one-term `QubitOperator` factors. `trotter_order` is 1, 2, or 3. Default `term_ordering` is sorted `hamiltonian.terms` keys. Each factor is scaled by `k_exp / trotter_number` within a Trotter slice. Order 2 and 3 require at least two terms. |
| `pauli_exp_to_qasm(qubit_operator_list, evolution_time=1.0, qubit_list=None, ancilla=None)` | Yields textual basis changes, CNOTs, and `Rz` operations for `exp(-i * evolution_time * op)`. Use a list of single-term Hermitian `QubitOperator`s. `qubit_list` is a list/tuple with at least one label per indexed mode. `ancilla` changes the middle rotation to controlled-QPE-like text. Coefficients are cast to their real part. |
| `trotterize_exp_qubop_to_qasm(hamiltonian, evolution_time=1, trotter_number=1, trotter_order=1, term_ordering=None, k_exp=1.0, qubit_list=None, ancilla=None)` | Composes grouping and `pauli_exp_to_qasm`; returns a string generator, not a Cirq circuit. The textual dialect uses names such as `H`, `Rx`, `CNOT`, `Rz`, and `C-Phase`; treat it as an intermediate format and validate any downstream parser. |
| `qubit_operator_to_pauli_sum(operator, qubits=None)` | Public mapping from `QubitOperator` to Cirq `PauliSum`. If `qubits` is omitted, it creates `cirq.LineQubit.range(count_qubits(operator))`; supply an explicit sequence to preserve a non-default register. |

A tiny two-term Cirq product can be assembled as follows:

```python
import cirq
import openfermion as of

qubits = cirq.LineQubit.range(2)
h = of.QubitOperator('Z0', 0.5) + of.QubitOperator('X0 X1', 0.25)
circuit = cirq.Circuit()
for factor in of.trotter_operator_grouping(h, trotter_number=1, trotter_order=1):
    pauli_sum = of.qubit_operator_to_pauli_sum(factor, qubits)
    circuit.append(cirq.PauliSumExponential(pauli_sum, exponent=-0.2))
```

`PauliSumExponential` represents `exp(j * exponent * pauli_sum)` and supports
commuting Pauli terms. The example supplies one term per operation, so its
commutation precondition is unambiguous. A QubitOperator term is not
automatically a full Cirq circuit; choose a decomposition or a Cirq operation
explicitly.

## Cirq-native Trotter simulation

```text
simulate_trotter(
    qubits, hamiltonian, time, n_steps=1, order=0, algorithm=None,
    control_qubit=None, omit_final_swaps=False
)
```

- `qubits` is an ordered sequence: position `j` represents fermionic mode
  `j` at entry. The function yields operation trees.
- Supported Hamiltonian representations are `InteractionOperator` and
  `DiagonalCoulombHamiltonian`, depending on algorithm.
- With `algorithm=None`, a `DiagonalCoulombHamiltonian` selects
  `LINEAR_SWAP_NETWORK`, and an `InteractionOperator` selects `LOW_RANK`.
- `order=0` selects an asymmetric step. `order>=1` selects a symmetric step;
  higher values use recursive Suzuki splitting. Negative order is rejected.
- `control_qubit` requests a controlled step only when the selected algorithm
  implements that variant. `omit_final_swaps=True` may save operations but can
  leave mode/qubit order reversed.

The algorithm constants and scope are:

| Constant/class | Accepted Hamiltonian | Notes |
|---|---|---|
| `LINEAR_SWAP_NETWORK` / `LinearSwapNetworkTrotterAlgorithm` | `DiagonalCoulombHamiltonian` | Swap-network simulation; step permutations must be tracked. |
| `SPLIT_OPERATOR` / `SplitOperatorTrotterAlgorithm` | `DiagonalCoulombHamiltonian` | Basis changes plus diagonal two-body evolution. |
| `LOW_RANK` / `LowRankTrotterAlgorithm` | `InteractionOperator` | Low-rank two-body decomposition; real, spin-symmetric default tensor contract. |

For a custom low-rank rank budget, instantiate
`LowRankTrotterAlgorithm(truncation_threshold=1e-8, final_rank=None,
spin_basis=True)`. `final_rank` overrides the threshold; do not claim that a
truncated circuit is exact.

## Gaussian and Slater preparation

| API | Contract |
|---|---|
| `prepare_slater_determinant(qubits, slater_determinant_matrix, initial_state=0)` | Returns an operation-tree iterator for an `eta x N` matrix with orthonormal rows. `len(qubits)` must equal `N`. The target state has `eta` occupied modes. An integer `initial_state` uses Cirq/OpenFermion big-endian computational-basis convention; a sequence lists occupied qubit indices. |
| `slater_determinant_preparation_circuit(slater_determinant_matrix)` | Returns grouped raw Givens operations `(i, j, theta, phi)`, not Cirq operations. The starting computational-basis state has the first `eta` modes occupied. |
| `jw_slater_determinant(slater_determinant_matrix)` | Returns the prepared Jordan-Wigner state as a sparse vector. It is a state utility, not a Cirq circuit. |
| `prepare_gaussian_state(qubits, quadratic_hamiltonian, occupied_orbitals=None, initial_state=0)` | Returns operation trees for a `QuadraticHamiltonian` eigenstate. `occupied_orbitals` is a mode-index sequence, or a pair of spin-up/down sequences when separate noninteracting spin sectors are used. `None` selects negative-energy orbitals for the ground state. |
| `gaussian_state_preparation_circuit(quadratic_hamiltonian, occupied_orbitals=None, spin_sector=None)` | Returns `(circuit_description, start_orbitals)`. Descriptions contain parallel tuples of Givens rotations and may contain `'pht'` for particle-hole transformations in non-number-conserving cases. A non-number-conserving `spin_sector` is unsupported. |
| `bogoliubov_transform(qubits, transformation_matrix, initial_state=None)` | Returns operation trees for an `N x N` number-conserving or `N x 2N` general Gaussian transform. The matrix shape must agree with `len(qubits)`. `initial_state` may enable fewer operations. |

Use `cirq.Circuit(of.prepare_slater_determinant(...))` or
`cirq.Circuit(of.bogoliubov_transform(...))`. The iterators can contain
nested operation trees; do not call `list(...)` as a substitute for Cirq
flattening when an operation-tree consumer is available.

## UCC/UCCSD generators

| API | Contract |
|---|---|
| `uccsd_generator(single_amplitudes, double_amplitudes, anti_hermitian=True)` | Returns a `FermionOperator`. Dense inputs are an `N x N` and `N x N x N x N` array; sparse inputs are `[[[i,j], amplitude], ...]` and `[[[i,j,k,l], amplitude], ...]`. The default adds the negative Hermitian-conjugate excitation, yielding an anti-Hermitian generator. `anti_hermitian=False` produces the normal-CC-style forward terms only. |
| `uccsd_convert_amplitude_format(single_amplitudes, double_amplitudes)` | Converts dense arrays to sparse index/amplitude lists. It enumerates nonzero entries; zero amplitudes are omitted. |
| `uccsd_singlet_paramsize(n_qubits, n_electrons)` | Requires even `n_qubits`. Returns `m + m*(m+1)//2`, with `m=ceil(n_electrons/2)*(n_qubits//2-ceil(n_electrons/2))`. |
| `uccsd_singlet_get_packed_amplitudes(single_amplitudes, double_amplitudes, n_qubits, n_electrons)` | Extracts the unique singlet singles and doubles in the order consumed by `uccsd_singlet_generator`. Input arrays must be indexed over the same `n_qubits` spin orbitals. |
| `uccsd_singlet_generator(packed_amplitudes, n_qubits, n_electrons, anti_hermitian=True)` | Returns a spin-conserving `FermionOperator`. Supply exactly `uccsd_singlet_paramsize(...)` amplitudes and an even number of spin orbitals. |

These APIs generate operators; they do not perform a Jordan-Wigner mapping or
compile a UCC ansatz to native gates. Route mapping and operator algebra to the
sibling `operators-and-transforms` skill, then use the Pauli product workflow
or a deliberate circuit compiler.

## Low-rank factorization helpers

| API | Contract |
|---|---|
| `get_chemist_two_body_coefficients(two_body_coefficients, spin_basis=True)` | Reorders a four-index two-body tensor and returns `(one_body_correction, chemist_tensor)`. In the default spin-orbital mode, the tensor must encode a spin-symmetric interaction; a spin-asymmetric input raises `ValueError`. |
| `low_rank_two_body_decomposition(two_body_coefficients, truncation_threshold=1e-8, final_rank=None, spin_basis=True)` | Returns `(eigenvalues, one_body_squares, one_body_correction, truncation_value)`. The interaction matrix is diagonalized and rank-ordered by a weight estimate. `final_rank` takes precedence over the threshold. Required reality/symmetry checks are strict. |
| `prepare_one_body_squared_evolution(one_body_matrix, spin_basis=True)` | Returns `(density_density_matrix, basis_transformation_matrix)` for a squared Hermitian one-body operator. `spin_basis=True` extracts a same-spin block and expands it; a non-Hermitian input raises `ValueError`. |

The decomposition is an algebraic preparation for low-rank Trotter steps. It is
not a guarantee of low circuit depth: each retained rank can add basis changes
and a swap network. Record rank/threshold and `truncation_value` in any
handoff.

## VPE circuit and estimator support

| API | Contract |
|---|---|
| `vpe_single_circuit(qubits, prep, evolve, initial_rotation, final_rotation)` | Returns `initial_rotation`, `prep`, `evolve`, `cirq.inverse(prep)`, `final_rotation`, then `cirq.measure(*qubits, key='msmt')`. Rotations must already be operations targeted at the desired qubit. |
| `vpe_circuits_single_timestep(qubits, prep, evolve, target_qubit, rotation_set=None)` | Returns one circuit per rotation tuple. `None` uses `standard_vpe_rotation_set`, which currently contains eight `(complex_weight, initial_gate, final_gate)` tuples. |
| `standard_vpe_rotation_set` | Eight standard X/Y pre/post rotation combinations with complex phase-function weights. Preserve its order when pairing results. |
| `get_phase_function(results, qubits, target_qid, rotation_set=None)` | From `openfermion.measurements`, combines `msmt` result counts using the rotation weights. `target_qid` is the integer index in `qubits`, and the function handles its bit-order conversion. Result count length must match the rotation set. |
| `PhaseFitEstimator(evals, ref_eval=0)` | From `openfermion.measurements`, samples simulation times and fits known frequencies. `get_simulation_points(safe=True)` uses approximately twice as many points as eigenvalues; `get_expectation_value(phase_function)` returns the weighted spectral estimate. |

The VPE circuits only prepare and measure data. They do not run a simulator or
choose shots, alias-free time ranges, noise mitigation, or a hardware plugin.
