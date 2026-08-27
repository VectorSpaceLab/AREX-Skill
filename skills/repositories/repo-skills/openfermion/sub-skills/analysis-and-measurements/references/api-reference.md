# Analysis API reference

## When to read

Read this reference when a task depends on an exact signature, matrix shape,
index convention, return type, or public import path. Facts below were checked
against the OpenFermion source and live public imports for the inspected 1.8.x
development line. Keep the source package and runtime package on a compatible
version when reproducing a result.

## Sparse and dense representations

| API | Signature | Contract and shape facts |
|---|---|---|
| `get_sparse_operator` | `get_sparse_operator(operator, n_qubits=None, trunc=None, hbar=1.0)` | Returns a SciPy sparse matrix. `FermionOperator` terms use Jordan–Wigner; `QubitOperator` terms use the qubit basis; `DiagonalCoulombHamiltonian` and `PolynomialTensor` are converted to fermions first; bosonic or quadrature operators require positive integer `trunc`. Fermion/qubit matrices have shape `(2**n_qubits, 2**n_qubits)`. |
| `jordan_wigner_sparse` | `jordan_wigner_sparse(fermion_operator, n_qubits=None)` | Direct fermionic Jordan–Wigner sparse matrix, normally CSC after construction. If omitted, `n_qubits` is inferred from the highest referenced mode. |
| `qubit_operator_sparse` | `qubit_operator_sparse(qubit_operator, n_qubits=None)` | Sparse matrix for a `QubitOperator`; an explicit `n_qubits` smaller than the highest referenced qubit raises `ValueError`. Trailing identity qubits are retained when `n_qubits` is larger. |
| `get_number_preserving_sparse_operator` | `get_number_preserving_sparse_operator(fermion_op, num_qubits, num_electrons, spin_preserving=False, reference_determinant=None, excitation_level=None)` | Returns a CSC matrix in a number sector, optionally fixed-`Sz` and optionally truncated by excitation rank. The basis ordering depends on `reference_determinant`; with the default, the first `num_electrons` orbitals are occupied and the reference determinant is the first basis vector. |
| `sparse_eigenspectrum` | `sparse_eigenspectrum(sparse_operator)` | Densifies the complete matrix, uses `eigvalsh` for Hermitian matrices and `eigvals` otherwise, and returns sorted eigenvalues. Use only for small dimensions. |
| `eigenspectrum` | `eigenspectrum(operator, n_qubits=None)` | Converts through `get_sparse_operator` and then densifies. `BosonOperator` and `QuadOperator` are rejected by this API even though they can have sparse representations with a truncation. |
| `get_ground_state` | `get_ground_state(sparse_operator, initial_guess=None)` | Uses SciPy sparse `eigsh(k=1, which='SA')`; returns `(eigenvalue, eigenstate)` where the state is a one-dimensional NumPy array. The operator must be suitable for the Hermitian sparse eigensolver. |
| `get_gap` | `get_gap(sparse_operator, initial_guess=None)` | Requires `is_hermitian(sparse_operator)` and uses the two lowest algebraic eigenvalues; returns their absolute difference. Dimension must be large enough for `k=2`. |
| `expectation` | `expectation(operator, state)` | A 1-D or column-shaped NumPy pure state is accepted; a SciPy sparse density matrix is accepted for a sparse matrix operator. A `LinearOperator` cannot be paired with a sparse density matrix. No normalization or dimension repair is performed. |
| `variance` | `variance(operator, state)` | Computes `expectation(operator**2, state) - expectation(operator, state)**2`; use a sparse-compatible operator and a correctly shaped state. |

A qubit operator with `n_qubits=2` must produce shape `(4, 4)`; with
`n_qubits=0` an identity-only operator is a special case and should generally
be avoided in analysis code unless the intended scalar space is explicit. For
bosons, `n_modes` is inferred from referenced modes and the full dimension is
`trunc**n_modes`, so apply the same guard before materializing.

The sparse representation uses OpenFermion's Jordan–Wigner amplitude ordering:
qubit `q` corresponds to bit `n_qubits - 1 - q` in a computational-basis
index. `jw_configuration_state(occupied_orbitals, n_qubits)` and
`jw_hartree_fock_state(n_electrons, n_orbitals)` return dense one-hot vectors
of length `2**n_qubits`.

## Sector restriction and linear operators

| API | Purpose | Important checks |
|---|---|---|
| `jw_number_indices(n_electrons, n_qubits)` | Indices for all computational basis states with exactly `n_electrons` occupied modes. | Sector size is `binomial(n_qubits, n_electrons)`; invalid particle counts naturally yield an empty or invalid combination set, so validate `0 <= n_electrons <= n_qubits`. |
| `jw_sz_indices(sz_value, n_qubits, n_electrons=None, up_index=up_index, down_index=down_index)` | Indices with fixed spin projection; qubit count must be even and `2*sz_value` must be an integer. | If particle number is also supplied, parity and `n_electrons >= abs(2*sz_value)` must be compatible. |
| `jw_number_restrict_operator(operator, n_electrons, n_qubits=None)` | Selects both rows and columns for a number sector. | The input full matrix dimension must be a power of two; `n_qubits` defaults to `log2(shape[0])`. |
| `jw_sz_restrict_operator(operator, sz_value, n_electrons=None, n_qubits=None, ...)` | Selects both rows and columns for an `Sz` sector. | Use the same qubit ordering and spin-index callbacks as the operator's encoding. |
| `jw_number_restrict_state(state, n_electrons, n_qubits=None)` | Selects a sector from a full state vector. | The returned vector may not be normalized. |
| `jw_sz_restrict_state(state, sz_value, n_electrons=None, n_qubits=None, ...)` | Selects an `Sz` sector from a full state vector. | The returned vector may not be normalized. |
| `jw_get_ground_state_at_particle_number(sparse_operator, particle_number)` | Restricts a Jordan–Wigner sparse matrix, solves its lowest state in the sector, and expands the vector back to length `2**n_qubits`. | The input is assumed Hermitian and number-conserving. The returned expanded state has zero amplitude outside the sector. |
| `LinearQubitOperator` | SciPy `LinearOperator` applying a `QubitOperator` without assembling the matrix. | Shape is `(2**n_qubits, 2**n_qubits)`; provide `n_qubits` when trailing identity qubits matter. |
| `generate_linear_qubit_operator` | `generate_linear_qubit_operator(qubit_operator, n_qubits=None, options=None)` | Returns `LinearQubitOperator`; a `LinearQubitOperatorOptions` object selects the parallel implementation and should be reserved for a separately justified workload. |

A restriction changes the basis and matrix size; it does not attach metadata to
the matrix. Preserve the selected indices or the sector parameters alongside a
restricted result.

## Davidson eigensolvers

Public classes are available from `openfermion.linalg` and the root package:
`Davidson`, `QubitDavidson`, `SparseDavidson`, `DavidsonOptions`, and
`DavidsonError`.

```python
options = DavidsonOptions(
    max_subspace=12, max_iterations=80, eps=1e-8, real_only=False
)
solver = SparseDavidson(sparse_matrix, options=options)
success, values, vectors = solver.get_lowest_n(
    n_lowest=2, initial_guess=initial_guess, max_iterations=40
)
```

- `DavidsonOptions(max_subspace=100, max_iterations=300, eps=1e-6,
  real_only=False)` rejects `max_subspace <= 2`, non-positive iteration counts,
  and non-positive `eps`. The subspace is capped at `dimension + 1`.
- `SparseDavidson(sparse_matrix, options=None)` uses the sparse matrix diagonal
  as the preconditioner diagonal.
- `QubitDavidson(qubit_operator, n_qubits=None, options=None)` uses a
  `LinearQubitOperator` and a diagonal computed from only I/Z terms; X/Y terms
  contribute zero to that diagonal. In the inspected 1.8.x development line,
  use the safe `options=None` wrapper: a non-`None` `DavidsonOptions` is also
  forwarded to the linear-operator factory and can fail because that factory
  treats it as parallel linear-operator options. For custom Davidson settings,
  construct `Davidson(generate_linear_qubit_operator(...),
  get_linear_qubit_operator_diagonal(...), options=DavidsonOptions(...))` or
  use `SparseDavidson` on a materialized sparse matrix.
- `get_lowest_n` requires `1 <= n_lowest < options.max_subspace`, a nonzero
  dimension-compatible initial guess if supplied, and returns a boolean
  `success`, ascending approximate eigenvalues, and column eigenvectors.
- Always inspect `success` and compute a residual such as
  `max(abs(A @ v - v * values))`. A `False` result is a bounded non-convergence,
  not proof that the values are unusable.

## RDM conventions and mappings

OpenFermion's tensor convention is:

- `opdm[p, q] = <a_p^† a_q>` (shape `(n_orbitals, n_orbitals)`).
- `tpdm[p, q, r, s] = <a_p^† a_q^† a_r a_s>` (shape
  `(n_orbitals,)*4`).
- A one-hole RDM uses `<a_p a_q^†>`; a two-hole RDM uses the corresponding
  reversed creation/annihilation order; a particle-hole RDM is stored with
  `phdm[p, r, q, s]` corresponding to `<a_p^† a_r a_q^† a_s>`.

| API | Input/output | Boundary |
|---|---|---|
| `get_interaction_rdm(qubit_operator, n_qubits=None)` | Returns an `InteractionRDM` with one- and two-RDM tensors. | Reconstructs all one- and two-body terms by Jordan–Wigner matching; cost grows rapidly as `n_qubits**4`. Specify `n_qubits` for trailing or identity-only qubits. |
| `map_two_pdm_to_one_pdm(tpdm, particle_number)` | Contracts `tpdm` to an OPDM with `einsum('prrq', tpdm)/(particle_number-1)`. | Requires a four-tensor and `particle_number != 1`; the particle count must match the RDM normalization. |
| `map_one_pdm_to_one_hole_dm(opdm)` / inverse | Returns `I - opdm`; both directions use the same operation. | OPDM must be square. |
| `map_two_pdm_to_two_hole_dm(tpdm, opdm)` / `map_two_hole_dm_to_two_pdm(tqdm, opdm)` | Applies anticommutation delta terms and index reversals. | Both tensors must use the same orbital dimension; validate four ranks and shape equality first. |
| `map_two_hole_dm_to_one_hole_dm(tqdm, hole_number)` | Contracts with `einsum('prrq', tqdm)/(hole_number-1)`. | Requires `hole_number != 1` and consistent hole normalization. |
| `map_two_pdm_to_particle_hole_dm(tpdm, opdm)` / inverse | Maps using `phdm[p,r,q,s] = opdm[p,s] delta(q,r) - tpdm[p,q,r,s]`. | Both inputs must describe the same orbital space. |
| `map_particle_hole_dm_to_one_pdm(phdm, num_particles, num_basis_functions)` | Contracts with denominator `num_basis_functions - num_particles + 1`. | Raises `ValueError` if particles exceed basis functions. |
| `valdemoro_reconstruction(tpdm, n_electrons)` | Returns a six-index approximate 3-RDM by setting the third cumulant to zero. | Input is a four-tensor with the two-RDM normalization; output shape is `(m,)*6`. Avoid `n_electrons <= 1`. |

For an RDM workflow, check `shape == (m,)*rank`, Hermiticity/antisymmetry as
appropriate for the input convention, traces, and a round trip (for example
2-RDM -> 2-hole -> 2-RDM). These maps are algebraic transformations, not
representability or positivity projections.

## Equality-constrained measurement workflows

- `one_body_fermion_constraints(n_orbitals, n_fermions)` and
  `two_body_fermion_constraints(n_orbitals, n_fermions)` yield
  `FermionOperator`s whose expectations vanish for an N-representable state.
  They encode trace, Hermiticity, contraction, and two-body linear relations.
- `linearize_term(term, n_orbitals)` and `unlinearize_term(index, n_orbitals)`
  use a single vector layout: identity, `n_orbitals**2` one-body slots, then
  `n_orbitals**4` two-body slots. Input terms must be identity, normal-ordered
  one-body creation/annihilation, or normal-ordered two-body creation/annihilation.
- `operator_to_vector(operator)` infers `n_orbitals` with `count_qubits` and
  returns length `1 + n_orbitals**2 + n_orbitals**4`;
  `vector_to_operator(vector, n_orbitals)` reconstructs the operator. Validate
  the inferred count and vector length before the inverse. An identity-only
  operator or an operator with unreferenced trailing orbitals cannot communicate
  the intended larger orbital dimension through `operator_to_vector` alone.
- `constraint_matrix(n_orbitals, n_fermions)` returns a sparse matrix with
  `1 + n_orbitals**2 + n_orbitals**4` columns. Its row count is generated from
  the two-body constraint family and grows quickly.
- `apply_constraints(operator, n_fermions)` solves a SciPy linear program and
  symmetrizes the modified operator with its Hermitian conjugate. It prints
  progress, builds dense LP constraint arrays, and is not a bounded tiny
  helper for large orbital spaces. Compare spectra only in the intended
  particle-number sector.

## Measurement partitions and grouping

- `binary_partition_iterator(qubit_list, num_iterations=None)` yields two
  lists and defaults to `ceil(log2(len(qubit_list)))`; it needs at least two
  qubits. `partition_iterator(qubit_list, partition_size,
  num_iterations=None)` yields k-tuples of lists and rejects `k > len(list)`.
- `pauli_string_iterator(num_qubits, max_word_size=2)` yields tuples of X/Y/Z/I
  strings covering every word up to the requested word size. It rejects a
  non-positive word size or `max_word_size > num_qubits`.
- `group_into_tensor_product_basis_sets(operator, seed=None)` accepts only a
  `QubitOperator` and returns a dictionary `{basis_term: sub_operator}`. Each
  sub-operator is diagonal in the basis represented by its key; identity-only
  terms join the compatible group. The random seed controls grouping order,
  not the operator union.
- `pair_within(labels)` and `pair_between(frag1, frag2, start_offset=0)` yield
  tuples of disjoint pairs, with a bare leftover label possible for odd
  lengths. `pair_within_simultaneously` covers four-label combinations.
- `pair_within_simultaneously_binned(binned_majoranas)` and
  `pair_within_simultaneously_symmetric(num_fermions, num_symmetries)` produce
  symmetry-aware Majorana pairing schedules. They are generators whose output
  count is combinatorial; bound consumption with `itertools.islice` when
  exploring a schedule.

## VPE and resource functionals

```python
estimator = PhaseFitEstimator(evals, ref_eval=0)
times = estimator.get_simulation_points(safe=True)
energy = estimator.get_expectation_value(phase_function)
```

`PhaseFitEstimator` uses known eigenvalues and a least-squares fit. With
`safe=True`, it requests `2 * len(evals)` samples and chooses
`dt = pi / (max(evals)-min(evals))`; `safe=False` requests `len(evals)` samples.
The phase-function array must be aligned with the selected simulation points.
A zero eigenvalue span is not a useful fit interval.

`get_phase_function(results, qubits, target_qid, rotation_set=None)` expects one
Cirq result per rotation in the rotation set (the default is the standard VPE
set), a measurement key `msmt`, and counts for the target qubit's bit position.
The target position is interpreted in the supplied qubit order with the
small-endian-to-big-endian conversion handled internally.

`get_one_norm_int(constant, one_body_integrals, two_body_integrals)` expects a
2-D `(n_orb,n_orb)` one-body tensor and a 4-D `(n_orb,)*4` spatial-orbital
two-body tensor. It includes the constant contribution. The
`get_one_norm_int_woconst` variant omits it. The molecule variants accept a
`MolecularData` object. These are resource functionals for the stated integral
convention, not a general coefficient norm for an arbitrary `QubitOperator`.

`is_contextual(hamiltonian)` is available from
`openfermion.functionals.contextuality`; it accepts only `QubitOperator` and
returns a Boolean based on the implemented commuting/anticommuting triple
test.

## Grid and lattice helpers

`Grid(dimensions, length, scale)` accepts a positive integer `dimensions`, an
integer or per-axis tuple/list `length`, and a positive float or scale matrix.
For a scalar scale, the cell is cubic. Positions are centered using
`length[i]//2`; reciprocal vectors use `2*pi*inv(scale).T`. Useful methods are
`position_vector`, `momentum_vector`, `index_to_momentum_ints`,
`momentum_ints_to_index`, `momentum_ints_to_value`, `orbital_id`,
`grid_indices`, `all_points_indices`, and `volume_scale`.

`HubbardSquareLattice(x_dimension, y_dimension, n_dofs=1, spinless=False,
periodic=True)` exposes site/dof/spin counts, `to_site_index`,
`from_site_index`, `to_spin_orbital_index`, `from_spin_orbital_index`,
`site_pairs_iter`, neighbor iterators, `Spin`, and `SpinPairs`. Validate edge
types and dof ranges before iterating. Use these objects to define geometry or
indexing; do not mistake them for a Hamiltonian builder.
