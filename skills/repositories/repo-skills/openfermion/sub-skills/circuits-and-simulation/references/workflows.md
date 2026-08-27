# Circuit construction workflows

These workflows keep physical/operator choices separate from circuit assembly.
Start with the preflight record below and preserve it with the caller's result:

```text
operator_type, mapping/basis, ordered qubits, mode count, time,
n_steps, formula order, term order or algorithm, control qubit,
final swap policy, matrix/tensor shapes, optional dependencies,
qubits/operations/depth, and unresolved limits
```

## 1. Build a bounded QubitOperator product in Cirq

Use this when the input is already a `QubitOperator` and the caller wants a
Cirq circuit rather than textual QASM.

```python
import cirq
import openfermion as of

qubits = cirq.LineQubit.range(2)
hamiltonian = of.QubitOperator('Z0', 0.5) + of.QubitOperator('X0 X1', 0.25)
factors = list(of.trotter_operator_grouping(
    hamiltonian, trotter_number=2, trotter_order=2,
    term_ordering=[((0, 'Z'),), ((0, 'X'), (1, 'X'))],
))

circuit = cirq.Circuit()
for factor in factors:
    pauli_sum = of.qubit_operator_to_pauli_sum(factor, qubits)
    circuit.append(cirq.PauliSumExponential(pauli_sum, exponent=-0.1))
print(len(circuit.all_qubits()), len(circuit.all_operations()), len(circuit))
```

The `term_ordering` keys must exactly match the operator's term keys. With
second order, the last term is the central factor and the other terms appear
in forward/reverse order in every step. Use a fixed order whenever depth or
reproducibility is part of the request. The example uses one commuting term
per `PauliSumExponential`; a multi-term Cirq Pauli sum is valid there only when
all terms commute.

For a textual intermediate instead:

```python
qasm_lines = list(of.trotterize_exp_qubop_to_qasm(
    hamiltonian, evolution_time=0.2, trotter_number=2, trotter_order=2,
    term_ordering=[((0, 'Z'),), ((0, 'X'), (1, 'X'))],
))
```

This is not OpenQASM, and `pauli_exp_to_qasm` treats its coefficient as real.
Inspect lines before handing them to another parser.

## 2. Meet a depth or term-order constraint

1. Count the original non-identity terms and fix a complete `term_ordering`.
2. Generate `list(trotter_operator_grouping(...))` and record factor count.
3. For each factor, count its support and estimate basis-change/CNOT work. A
   Pauli string with `r` non-identity factors uses a CNOT chain in the QASM
   decomposition, with a reverse chain after the rotation.
4. Build the actual Cirq circuit and report `len(all_qubits())`,
   `len(all_operations())`, and `len(circuit)` rather than estimating depth
   from term count alone.
5. If the bound fails, change one declared control at a time: term ordering,
   `trotter_number`, formula order, commuting grouping, or a native algorithm.
   Do not silently change evolution time or drop swaps.

A requested “second-order” or “third-order” product is a formula choice, not a
claim of a particular hardware depth. Cirq moment packing depends on operation
supports and insertion strategy.

## 3. Use `simulate_trotter` with native fermionic Hamiltonians

For an `InteractionOperator`:

```python
import cirq
import openfermion as of
from openfermion.circuits import trotter

qubits = cirq.LineQubit.range(4)
# interaction_hamiltonian must be a caller-supplied InteractionOperator.
step_algorithm = trotter.LowRankTrotterAlgorithm(final_rank=2)
circuit = cirq.Circuit(
    of.simulate_trotter(
        qubits, interaction_hamiltonian, time=0.1, n_steps=2, order=0,
        algorithm=step_algorithm, omit_final_swaps=False,
    ),
    strategy=cirq.InsertStrategy.EARLIEST,
)
```

For a `DiagonalCoulombHamiltonian`, select `trotter.LINEAR_SWAP_NETWORK` or
`trotter.SPLIT_OPERATOR`. `order=0` and `order=1` choose asymmetric and
symmetric implementations respectively. Controlled simulation needs a control
qubit and an algorithm implementation that supports the requested formula.

Before measuring or appending another circuit, inspect whether the selected
step reversed the qubit sequence. `omit_final_swaps=True` is a deliberate
interface change: retain a record of the new mode order and only use it when
the next stage understands that permutation.

## 4. Prepare a Slater determinant with a dimension gate

For an `eta x N` matrix `Q`:

```python
import numpy as np
import cirq
import openfermion as of

q = np.array([[1.0, 1.0]]) / np.sqrt(2.0)  # eta=1, N=2; rows are orthonormal
qubits = cirq.LineQubit.range(q.shape[1])
slater_circuit = cirq.Circuit(
    of.prepare_slater_determinant(qubits, q, initial_state=0)
)
```

Preflight:

- `Q.ndim == 2`, `Q.shape[1] == len(qubits)`;
- `Q.shape[0] <= Q.shape[1]` and `Q @ Q.conj().T` is identity within the
  caller's tolerance;
- the intended initial state has exactly `eta` occupied modes if it is meant
  to be a number-conserving starting determinant;
- an integer uses big-endian bit positions, while a sequence lists qubit
  indices directly.

The returned preparation is correct up to a global phase. Use
`slater_determinant_preparation_circuit` when a raw parallel Givens description
is wanted, and `jw_slater_determinant` when a sparse Jordan-Wigner state—not a
Cirq circuit—is wanted.

## 5. Prepare a Gaussian state or basis rotation

For a `QuadraticHamiltonian`, use
`prepare_gaussian_state(qubits, hamiltonian, occupied_orbitals, initial_state)`.
Leave `occupied_orbitals=None` for the negative-energy ground-state choice, or
pass mode indices for a selected eigenstate. Two spin-sector lists are valid
only when the Hamiltonian has the required separated spin structure.

For a known transformation matrix `W`, use
`bogoliubov_transform` and validate:

```text
W.shape in {(N, N), (N, 2*N)} and len(qubits) == N
```

The `(N, N)` case is number conserving. The `(N, 2N)` case can include
particle-hole mixing; it may emit `X` operations for particle-hole changes.
When modes are arranged as all spin-up followed by all spin-down, a block
structured transformation can be decomposed sector by sector. Record the mode
ordering; an interleaved register is not the same convention.

## 6. Create a UCCSD generator safely

The UCC APIs return `FermionOperator`s, not circuits. For dense amplitudes,
check shapes before construction:

```python
n = 4
single = np.zeros((n, n))
double = np.zeros((n, n, n, n))
generator = of.uccsd_generator(single, double)
```

The default is anti-Hermitian and therefore suitable as a formal unitary
cluster generator. `anti_hermitian=False` is a different CC-style operator,
not a cheaper way to request UCC.

For singlet packing:

1. Require even `n_qubits` and `0 <= n_electrons <= n_qubits`.
2. Compute `n_params = of.uccsd_singlet_paramsize(n_qubits, n_electrons)`.
3. Ensure the packed amplitude sequence has exactly `n_params` entries.
4. Call `uccsd_singlet_generator`.

To pack dense arrays, pass arrays indexed over the same spin-orbital dimension
to `uccsd_singlet_get_packed_amplitudes`. Then route the returned operator to
the mapping/compiler workflow; do not imply that a generator is already a
Cirq ansatz.

## 7. Prepare low-rank evolution data

For a real, spin-symmetric interaction tensor, call:

```python
evals, squares, correction, truncation = of.low_rank_two_body_decomposition(
    tensor, truncation_threshold=1e-8, final_rank=None, spin_basis=True
)
```

Record `len(evals)`, `squares.shape`, and `truncation`. `final_rank` overrides
the threshold; a nonzero truncation is an approximation bound from the
decomposition, not a circuit error measured by Cirq.

For one retained square, call
`prepare_one_body_squared_evolution(squares[j])`. The matrix must be
Hermitian. The returned density-density coefficients and basis transformation
are consumed by the low-rank Trotter implementation; they are not themselves
a complete circuit. Use `LowRankTrotterAlgorithm` when the caller wants the
full Cirq operation tree.

## 8. Build and consume VPE data

Construct one circuit per rotation tuple:

```python
import cirq
import openfermion as of

system = cirq.LineQubit.range(2)
prep = cirq.Circuit(cirq.X(system[1]))
evolve = cirq.Circuit(cirq.rz(0.2).on_each(*system))
circuits = of.vpe_circuits_single_timestep(
    system, prep, evolve, target_qubit=system[0]
)
```

The default produces eight circuits. Each measures all `system` qubits under
`msmt`; run them in the exact returned order. Pass the resulting Cirq results
to `of.get_phase_function(results, system, target_qid=0)`. For known spectral
values, `of.PhaseFitEstimator(evals).get_simulation_points()` provides time
points, and `get_expectation_value` fits the phase-function samples.

Keep three contracts separate: circuit generation, shot execution, and
frequency fitting. A VPE circuit does not determine a shot count or a noise
model, and `PhaseFitEstimator` assumes its supplied frequencies are known.
