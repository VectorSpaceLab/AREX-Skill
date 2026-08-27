# OpenFermion API index

Read this reference when a task needs a verified signature or a boundary between
operator, model, circuit, and analysis workflows. Signatures below were checked
against the inspected OpenFermion 1.8.2.dev0 package. They are a compact index;
load the owning sub-skill's API reference for tensor shapes and edge cases.

## Core representations

| API | Signature / contract | Use |
|---|---|---|
| `FermionOperator` | `FermionOperator(term=None, coefficient=1.0)` | Arbitrary fermionic ladder polynomials; `p^` creation and `p` annihilation |
| `QubitOperator` | `QubitOperator(term=None, coefficient=1.0)` | Sums of Pauli products such as `"X0 Y1"` |
| `BosonOperator` | `BosonOperator(term=None, coefficient=1.0)` | Bosonic ladder operators; finite truncation is needed for matrices |
| `MajoranaOperator` | `MajoranaOperator(term=None, coefficient=1.0)` | Majorana-generator products |
| `InteractionOperator` | `InteractionOperator(constant, one_body_tensor, two_body_tensor)` | Number-conserving one-/two-body interaction tensors |
| `PolynomialTensor` | `PolynomialTensor(n_body_tensors)` | General tensor-backed polynomial representation |

Operator `.terms` maps tuples to coefficients. Fermion/boson actions are integer
`1` (creation) and `0` (annihilation); Pauli actions are `"X"`, `"Y"`, and
`"Z"`. The empty term is identity. No-argument construction is the zero
operator. Use `compress()` and `isclose()` rather than comparing printed text.

## Normal ordering and mappings

| API | Signature | Important boundary |
|---|---|---|
| `normal_ordered` | `(operator, hbar=1.0)` | Canonical rewrite; may increase term count |
| `jordan_wigner` | `(operator)` | Direct canonical fermion-to-qubit mapping; no padding argument |
| `bravyi_kitaev` | `(operator, n_qubits=None)` | Fenwick-tree mapping; explicit padding must be >= required modes |
| `binary_code_transform` | `(operator, code)` | Requires a compatible `BinaryCode` mode/qubit contract |
| `reverse_jordan_wigner` | `(qubit_operator)` | JW inverse only; does not invert BK or arbitrary codes |
| `get_sparse_operator` | `(operator, n_qubits=None, trunc=None, hbar=1.0)` | Matrix conversion; qubit dimension is `2**n_qubits`; bosons need finite `trunc` |

## Model and chemistry constructors

| API | Signature | Important boundary |
|---|---|---|
| `fermi_hubbard` | `(x_dimension, y_dimension, tunneling, coulomb, chemical_potential=0.0, magnetic_field=0.0, periodic=True, spinless=False, particle_hole_symmetry=False)` | Returns a `FermionOperator`; default is periodic and spinful |
| `jellium_model` | `(grid, spinless=False, plane_wave=True, include_constant=False, e_cutoff=None, non_periodic=False, period_cutoff=None)` | Grid/cutoff/constant choices are part of the model contract |
| `MolecularData` | `(geometry=None, basis=None, multiplicity=None, charge=0, description='', filename='', data_directory=None)` | HDF5-backed metadata/results record; constructor does not run a chemistry solver |
| `MolecularData.get_molecular_hamiltonian` | inspect owning chemistry reference | Requires integral data; may accept active-space/core parameters |

## Circuit and analysis entry points

| API | Signature / contract | Use |
|---|---|---|
| `trotter_operator_grouping` | `(hamiltonian, trotter_number=1, trotter_order=1, term_ordering=None, k_exp=1.0)` | Ordered QubitOperator factors for product formulas |
| `uccsd_singlet_generator` | `(packed_amplitudes, n_qubits, n_electrons, anti_hermitian=True)` | Packed singlet UCCSD generator; amplitudes must match dimensions |
| `prepare_slater_determinant` | `(qubits, slater_determinant_matrix, initial_state=0)` | Cirq operation tree; matrix rows must be orthonormal |
| `get_ground_state` | `(sparse_operator, initial_guess=None)` | Lowest-state energy/vector from a sparse operator |
| `get_interaction_rdm` | `(qubit_operator, n_qubits=None)` | Reconstructs an `InteractionRDM` from measured qubit coefficients |

## Import and boundary notes

- Most APIs are re-exported from `openfermion`; deeper modules such as
  `openfermion.functionals.contextuality` and resource-estimation modules may
  be clearer and may have optional dependencies.
- Cirq-returning circuit APIs require Cirq core. QASM-like helpers return text,
  not necessarily a parser-compatible OpenQASM document.
- `get_sparse_operator` is conversion only. Choose an eigensolver or bounded
  diagonalization explicitly after checking shape and memory.
- `MolecularData` geometry is conventionally in Angstroms; plane-wave model
  constructors use their documented atomic-unit/grid conventions. Do not mix
  these without an explicit conversion.
