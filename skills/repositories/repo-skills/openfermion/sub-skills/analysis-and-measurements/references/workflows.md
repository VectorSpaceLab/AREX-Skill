# Bounded analysis workflows

These recipes use only public OpenFermion APIs and small deterministic inputs.
They are patterns to adapt after checking dimensions, normalization, and the
purpose of the result. They intentionally do not build molecular or Hubbard
models, synthesize circuits, download data, or claim benchmark performance.

## 1. Convert a tiny qubit operator and validate the spectrum

```python
import numpy as np
from openfermion import QubitOperator
from openfermion.linalg import (
    get_sparse_operator,
    get_ground_state,
    sparse_eigenspectrum,
    expectation,
)

n_qubits = 2
hamiltonian = (
    QubitOperator((), 0.1)
    + QubitOperator("Z0", -0.75)
    + QubitOperator("Z1", -0.50)
    + QubitOperator("X0 X1", -0.20)
)
A = get_sparse_operator(hamiltonian, n_qubits=n_qubits)
assert A.shape == (2**n_qubits, 2**n_qubits)
assert A.shape[0] <= 16  # explicit dense-analysis guard for this recipe
energy, state = get_ground_state(A)
assert state.shape == (2**n_qubits,)
assert np.isclose(np.linalg.norm(state), 1.0)
assert np.allclose(A @ state, energy * state, atol=1e-8)
print(A.shape, energy, sparse_eigenspectrum(A))
print("energy expectation", expectation(A, state))
```

`get_sparse_operator` returns a sparse matrix with dimension `2**n_qubits`.
The example's matrix is `4 x 4` with 8 stored entries. Its expected ground
energy is approximately `-1.165898890117` and its ascending spectrum is
`[-1.165898890117, -0.220156211872, 0.420156211872, 1.365898890117]`.
Use those values as a small regression expectation and still check the
residual with a tolerance. For an operator whose highest term references qubit
3, `n_qubits=2` must be rejected instead of silently dropping the term. If the
operator has trailing identity qubits, pass the intended larger count
explicitly.

Use `sparse_eigenspectrum` only after calculating the dense memory bound: its
implementation calls `.todense()`. For a larger sparse matrix use
`get_ground_state`, `get_gap`, or Davidson and report the iterative residual.

## 2. Restrict a Jordan–Wigner problem to a number or spin sector

```python
from openfermion import FermionOperator
from openfermion.linalg import (
    get_sparse_operator,
    jw_number_indices,
    jw_number_restrict_operator,
    jw_get_ground_state_at_particle_number,
)

n_qubits = 4
fermion_h = (
    FermionOperator("0^ 1") + FermionOperator("1^ 0")
    + FermionOperator("1^ 2") + FermionOperator("2^ 1")
)
full = get_sparse_operator(fermion_h, n_qubits=n_qubits)
sector = 2
indices = jw_number_indices(sector, n_qubits)
restricted = jw_number_restrict_operator(full, sector, n_qubits)
assert restricted.shape == (len(indices), len(indices))
energy, expanded_state = jw_get_ground_state_at_particle_number(full, sector)
assert expanded_state.shape == (2**n_qubits,)
```

The restricted matrix is ordered by the selected computational-basis indices,
not by the original full matrix dimension. The expanded state from
`jw_get_ground_state_at_particle_number` is zero outside that sector. For a
fixed `Sz` calculation, use an even qubit count and validate that
`2*sz_value` is an integer; when fixing particle number simultaneously, check
parity and `n_electrons >= abs(2*sz_value)` first.

For a direct number-preserving fermionic matrix, use
`get_number_preserving_sparse_operator`. Record `num_qubits`,
`num_electrons`, `spin_preserving`, `reference_determinant`, and
`excitation_level`, because those choices define both the dimension and basis
ordering. Do not compare vectors from two different reference determinants by
index alone.

## 3. Use Davidson with a bounded deterministic guess

```python
import numpy as np
from openfermion import QubitOperator
from openfermion.linalg import QubitDavidson

n_qubits = 2
operator = QubitOperator("Z0", -1.0) + QubitOperator("Z1", -0.4)
solver = QubitDavidson(operator, n_qubits=n_qubits)
initial_guess = np.eye(2**n_qubits, 2, dtype=complex)
success, values, vectors = solver.get_lowest_n(
    n_lowest=2, initial_guess=initial_guess, max_iterations=40
)
residual = np.max(np.abs(solver.linear_operator.dot(vectors) - vectors * values))
print(success, values, residual)
```

The initial guess must have `2**n_qubits` rows. `n_lowest` must be smaller
than the effective `max_subspace`; the default options reduce that subspace for
small matrices. Check `success` and the residual. If a two-state request does
not converge, preserve the returned values as approximate only, increase the
subspace or iteration budget cautiously, or use a sparse exact reference for a
small matrix. Do not hide a `False` success flag.

In the inspected 1.8.x development line, do **not** pass `DavidsonOptions` to
`QubitDavidson(..., options=...)`: that argument is also forwarded to the
linear-operator factory, which interprets a non-`None` value as parallel
linear-operator options and can fail on a missing `processes` attribute. For
custom iteration options, compose the serial linear operator explicitly:

```python
from openfermion.linalg import (
    Davidson,
    DavidsonOptions,
    generate_linear_qubit_operator,
    get_linear_qubit_operator_diagonal,
)

linear = generate_linear_qubit_operator(operator, n_qubits=n_qubits)
diagonal = get_linear_qubit_operator_diagonal(operator, n_qubits=n_qubits)
options = DavidsonOptions(max_subspace=6, max_iterations=40, eps=1e-9)
solver = Davidson(linear, diagonal, options=options)
```

Use `SparseDavidson` when the sparse matrix and its diagonal are available. Use
`Davidson` directly only when you can supply a SciPy sparse/linear operator and
its diagonal. `ParallelLinearQubitOperator` and multiprocessing are outside a
small verification workflow; use them only with an explicit workload and
resource budget.

## 4. Reconstruct and validate RDMs

Start with a shape preflight before any map:

```python
import numpy as np

m = opdm.shape[0]
if opdm.shape != (m, m):
    raise ValueError("OPDM must be square")
if tpdm.shape != (m, m, m, m):
    raise ValueError("TPDM must have four axes of the OPDM dimension")
```

The OpenFermion convention is `opdm[p,q] = <a_p^dagger a_q>` and
`tpdm[p,q,r,s] = <a_p^dagger a_q^dagger a_r a_s>`. A common bounded round trip
is:

```python
from openfermion.utils import (
    map_two_pdm_to_two_hole_dm,
    map_two_hole_dm_to_two_pdm,
)

hole_rdm = map_two_pdm_to_two_hole_dm(tpdm, opdm)
round_trip = map_two_hole_dm_to_two_pdm(hole_rdm, opdm)
assert np.allclose(round_trip, tpdm, atol=1e-10)
```

Also validate the one-body contraction against the known particle number:
`map_two_pdm_to_one_pdm(tpdm, particle_number)` divides by
`particle_number - 1`, so `particle_number=1` is undefined. The two-hole to
one-hole contraction similarly needs `hole_number != 1`. For a particle-hole
map, ensure `num_particles <= num_basis_functions` and use a consistent
`num_basis_functions` in the contraction.

`valdemoro_reconstruction(tpdm, n_electrons)` produces an approximate six-axis
3-RDM, not a measured exact 3-RDM. Verify output shape `(m,)*6` and an
appropriate trace for the chosen RDM normalization; do not use it as a
representability proof. It is undefined for a one-electron normalization.

`get_interaction_rdm(qubit_operator, n_qubits=...)` is useful for a bounded
measured `QubitOperator`, but loops over all one- and two-body index tuples.
Set `n_qubits` explicitly when the input has only an identity term or when
trailing zero-weight orbitals are meaningful. Keep the operator coefficients
and the target qubit count in the result metadata.

## 5. Apply equality constraints only as a resource-functional step

Use `one_body_fermion_constraints` or `two_body_fermion_constraints` when the
task is to express zero-expectation identities. For a small real one-/two-body
`FermionOperator`:

```python
from openfermion import count_qubits
from openfermion.measurements import (
    operator_to_vector,
    vector_to_operator,
    constraint_matrix,
)

n_orbitals = 4
n_fermions = 2
if count_qubits(operator) != n_orbitals:
    raise ValueError("operator terms do not establish the declared orbital dimension")
vector = operator_to_vector(operator)
expected_len = 1 + n_orbitals**2 + n_orbitals**4
assert vector.shape == (expected_len,)
restored = vector_to_operator(vector, n_orbitals)
assert restored == operator
C = constraint_matrix(n_orbitals, n_fermions)
assert C.shape[1] == expected_len
```

`operator_to_vector` infers the orbital count from referenced terms. An
identity-only operator or unreferenced trailing orbitals therefore needs a
separate dimension decision before vectorization; do not silently accept a
shorter vector. `apply_constraints` invokes a linear program and creates dense
LP arrays. Use it
only after bounding `n_orbitals`, and compare the original and modified
operators in the intended particle-number sector. It changes coefficient
representation while preserving the stated equality-constrained expectations;
it is not a general tensor-shape fixer or a positivity projection.

## 6. Group and partition measurements

For a `QubitOperator`, use:

```python
from openfermion.measurements import group_into_tensor_product_basis_sets

groups = group_into_tensor_product_basis_sets(operator, seed=0)
assert all(group.__class__.__name__ == "QubitOperator" for group in groups.values())
```

Each dictionary key is a tensor-product basis term and each value contains
terms diagonal in that basis. Reassemble by summing values and compare against
the input operator; grouping order can vary with `seed`. A non-qubit operator
must be diagnosed before the call.

Use `binary_partition_iterator` or `partition_iterator` when a coverage family
of qubit sets is needed, and `pauli_string_iterator` when every Pauli word up to
a bounded size must occur in at least one string. Use `itertools.islice` when
exploring generated schedules. For fermionic measurement schedules, the
`pair_within*` functions yield tuple pairings and may include unpaired labels
for odd list sizes; symmetry-aware variants expect Majorana labels or the
`num_fermions`/`num_symmetries` convention, not arbitrary qubit indices.

These utilities do not calculate shots, variances, post-rotations, or circuits.
Pass their bounded output to the circuit/simulation route when a runnable
experiment is required.

## 7. Process VPE samples and resource functionals

For known eigenvalues, generate the estimator's own points and produce the
phase function at exactly those points:

```python
import numpy as np
from openfermion.measurements import PhaseFitEstimator

evals = np.array([-1.0, 1.0])
estimator = PhaseFitEstimator(evals)
times = estimator.get_simulation_points(safe=True)
amplitudes = np.array([0.2, 0.8])
phase = np.array([
    np.sum(amplitudes * np.exp(1j * evals * time)) for time in times
])
energy = estimator.get_expectation_value(phase)
assert np.isclose(energy, 0.6)
```

The safe point count is twice the number of known eigenvalues and the step is
`pi/(max(evals)-min(evals))`. `get_phase_function` instead consumes one Cirq
result per rotation-set entry, each with a `msmt` measurement column; validate
that result count and key before fitting. VPE post-rotation and circuit creation
belong to the circuits route.

For spatial-orbital integrals, check `one_body.shape == (n,n)` and
`two_body.shape == (n,n,n,n)` before calling `get_one_norm_int`. Use
`get_one_norm_int` when the constant is included and
`get_one_norm_int_woconst` when it is intentionally omitted. These functions
are resource estimates tied to this integral convention, not a substitute for
`QubitOperator.induced_norm()` on an arbitrary operator. For contextuality,
call `is_contextual` from its public submodule and pass a `QubitOperator`.

## 8. Use grid and lattice helpers for numerical indexing

```python
import numpy as np
from openfermion.utils import Grid

grid = Grid(dimensions=1, length=4, scale=4.0)
positions = [grid.position_vector(i)[0] for i in range(4)]
assert np.allclose(positions, [-2.0, -1.0, 0.0, 1.0])
momentum = [grid.momentum_vector(i)[0] for i in range(4)]
assert grid.grid_indices(grid.orbital_id(2, spin=1), spinless=False) == [2]
```

`Grid` centers positions by `length//2`, while momentum indices use the same
shift and the reciprocal lattice. Check every coordinate with
`grid_indices`/`orbital_id`; `OrbitalSpecificationError` indicates an invalid
coordinate or qubit id. For an interaction geometry, use
`HubbardSquareLattice` to iterate sites, dofs, spins, or edge types and then
route the resulting model construction elsewhere.
