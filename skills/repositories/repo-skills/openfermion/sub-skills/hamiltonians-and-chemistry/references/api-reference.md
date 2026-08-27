# Hamiltonian and chemistry API reference

These are the public entry points confirmed from the package exports and live
call signatures for this repository version. Return types below are symbolic
OpenFermion objects unless stated otherwise. Coefficients can be real or
complex; preserve that fact when serializing.

## Standard and general Hubbard models

| API | Important signature/contract | Result and cautions |
| --- | --- | --- |
| `fermi_hubbard` | `fermi_hubbard(x_dimension, y_dimension, tunneling, coulomb, chemical_potential=0.0, magnetic_field=0.0, periodic=True, spinless=False, particle_hole_symmetry=False)` | Returns a `FermionOperator`. Standard square grid; spinful has two modes per site, spinless one. `periodic` and the two particle/spin flags materially change terms. |
| `bose_hubbard` | `bose_hubbard(x_dimension, y_dimension, tunneling, interaction, chemical_potential=0.0, dipole=0.0, periodic=True)` | Returns a `BosonOperator`; it is not a fermionic qubit Hamiltonian. Route bosonic transforms separately. |
| `HubbardSquareLattice` | `HubbardSquareLattice(x_dimension, y_dimension, n_dofs=1, spinless=False, periodic=True)` | Lattice descriptor. Valid edge types are `onsite`, `neighbor`, `horizontal_neighbor`, `vertical_neighbor`, and `diagonal_neighbor`. Use `site_pairs_iter(edge_type, ordered=...)` to inspect edges. |
| `FermiHubbardModel` | `FermiHubbardModel(lattice, tunneling_parameters=None, interaction_parameters=None, potential_parameters=None, magnetic_field=0.0, particle_hole_symmetry=False)` | Parameterized multiband model. Call `.hamiltonian()` after construction. Its lattice determines mode indexing, spin availability, and legal edge types. |

For `fermi_hubbard`, site `s` has spin-up mode `2*s` and spin-down mode
`2*s+1`; a spinless site uses mode `s`. Hopping terms are Hermitian pairs. A
spinful on-site Coulomb term couples up and down at one site. A spinless
Coulomb term is between neighboring occupations. The standard function uses
right and bottom neighbors and avoids duplicate wraparound edges for dimensions
of size two.

`FermiHubbardModel` parameter records are:

```text
Tunneling:   (edge_type, (dof_a, dof_b), coefficient)
Interaction: (edge_type, (dof_a, dof_b), coefficient[, SpinPairs.ALL|SAME|DIFF])
Potential:   (dof, coefficient)
```

`SpinPairs.ALL` is all spin pairs, `SAME` is up/up and down/down, and `DIFF`
is the two opposite-spin ordered pairs. The model validates edge types and DOF
indices. Same-DOF onsite tunneling is rejected, as is an onsite same-spin
self-interaction. `.tunneling_terms()`, `.interaction_terms()`,
`.potential_terms()`, and `.field_terms()` are inspectable components before
`.hamiltonian()` combines them.

## Grid, jellium, and plane waves

| API | Important signature/contract | Result and cautions |
| --- | --- | --- |
| `Grid` | `Grid(dimensions, length, scale)` | `length` is an integer (replicated per dimension) or a tuple/list of per-axis counts. `scale` is a positive float for a cubic cell or an ndarray whose columns are cell vectors. Exposes `num_points`, `volume_scale()`, `all_points_indices()`, position/momentum conversion, and orbital indexing. |
| `wigner_seitz_length_scale` | `wigner_seitz_length_scale(wigner_seitz_radius, n_particles, dimension)` | Returns the cell length scale for a hypercube. `dimension` must be a positive integer. |
| `hypercube_grid_with_given_wigner_seitz_radius_and_filling` | `(dimension, grid_length, wigner_seitz_radius, filling_fraction=0.5, spinless=True)` | Returns a cubic `Grid`; floors the particle count and rejects a zero-particle choice or filling above one. |
| `jellium_model` | `jellium_model(grid, spinless=False, plane_wave=True, include_constant=False, e_cutoff=None, non_periodic=False, period_cutoff=None)` | Returns a `FermionOperator` containing kinetic and electron-electron terms. `plane_wave=True` is momentum space; `False` is the dual/position basis. `include_constant` adds the Madelung identity shift and is not a geometry-independent energy calculation. |
| `plane_wave_kinetic` | `(grid, spinless=False, e_cutoff=None)` | Kinetic-only plane-wave operator. Modes above the kinetic energy cutoff are skipped. |
| `plane_wave_potential` | `(grid, spinless=False, e_cutoff=None, non_periodic=False, period_cutoff=None)` | Electron-electron potential in plane-wave basis. Coulomb momentum coefficient is dimension-specific; the zero-momentum term is skipped. |
| `dual_basis_jellium_model` | `(grid, spinless=False, kinetic=True, potential=True, include_constant=False, non_periodic=False, period_cutoff=None)` | Dual-basis kinetic/potential combination. Use `dual_basis_kinetic` or `dual_basis_potential` for one component. |
| `plane_wave_hamiltonian` | `(grid, geometry=None, spinless=False, plane_wave=True, include_constant=False, e_cutoff=None, non_periodic=False, period_cutoff=None)` | Adds nuclear external potential to jellium. Geometry coordinates must have exactly `grid.dimensions` entries and recognized element symbols. `include_constant=True` is rejected with non-`None` geometry. |
| `plane_wave_external_potential` | `(grid, geometry, spinless, e_cutoff=None, non_periodic=False, period_cutoff=None)` | External nuclear potential in plane-wave basis; applies an optional mode cutoff. |
| `dual_basis_external_potential` | `(grid, geometry, spinless, non_periodic=False, period_cutoff=None)` | External nuclear potential in the dual basis. |

`Grid.orbital_id(indices, spin=None)` returns the spinless orbital index when
`spin=None`, and interleaves spin by returning `2 * spatial_index + spin`
otherwise. `grid_indices(qubit_id, spinless)` is the inverse. Grid position
indices are shifted around the cell center; momentum indices use reciprocal
cell vectors. A scalar `scale` must be a float, not an integer, in this API.

Coulomb helpers support dimensions 1, 2, and 3. One-dimensional Coulomb uses a
softening parameter in the lower-level `coulomb_potential_momentum` helper;
the public jellium constructors use their documented defaults. Non-periodic
corrections require a meaningful period cutoff; `None` derives one from the
cell volume.

**Version-specific constant check:** source and live inspection confirm that
`jellium_model(..., plane_wave=False, include_constant=True)` currently adds
the Madelung identity shift both inside `dual_basis_jellium_model` and again in
the wrapper. For a unit-scale cell, the observed difference from
`include_constant=False` is `2 * 2.8372`; direct
`dual_basis_jellium_model(..., include_constant=True)` adds it once. Inspect
the identity coefficient and use the direct dual constructor when exactly one
shift is intended. Do not silently compensate without recording the choice.

## MolecularData and tensor operations

| API | Important signature/contract | Result and cautions |
| --- | --- | --- |
| `MolecularData` | `MolecularData(geometry=None, basis=None, multiplicity=None, charge=0, description="", filename="", data_directory=None)` | Metadata container with lazy HDF5-backed calculation fields. If geometry, basis, or multiplicity is missing, `filename` must identify a loadable record. |
| `name_molecule` | `(geometry, basis, multiplicity, charge, description)` | Deterministic name from sorted element counts, basis, multiplicity, charge, and optional description. Multiplicity must be a positive integer-valued number. |
| `geometry_from_file` | `(file_name)` | Reads only lines with four whitespace-separated fields: element and three Angstrom coordinates. It performs no chemistry validation. |
| `angstroms_to_bohr` / `bohr_to_angstroms` | `(distance)` | Scalar conversion helpers. `MolecularData` geometry is documented in Angstroms; plane-wave geometry is in atomic units. |
| `MolecularData.get_integrals()` | `()` | Returns `(one_body_integrals, two_body_integrals)` or raises `MissingCalculationError` when either is absent. The exception is defined in the public `openfermion.chem.molecular_data` module. |
| `MolecularData.get_active_space_integrals` | `(occupied_indices=None, active_indices=None)` | Returns `(core_constant, one_body, two_body)`. Indices refer to spatial orbitals; at least one active index is required. Integral data must already exist. |
| `MolecularData.get_molecular_hamiltonian` | `(occupied_indices=None, active_indices=None)` | Returns an `InteractionOperator` with nuclear/core constant and spin-orbital tensors. Even spin-orbital indices are alpha/up and odd indices beta/down. Requires integral data. |
| `MolecularData.get_molecular_rdm` | `(use_fci=False)` | Returns an `InteractionRDM` from stored CISD or FCI RDMs; raises `MissingCalculationError` when the selected calculation has not been performed. |
| `load_molecular_hamiltonian` | `(geometry, basis, multiplicity, description, n_active_electrons=None, n_active_orbitals=None)` | Loads a previously saved record and returns its molecular `InteractionOperator`, optionally selecting a leading active space. It does not run a backend. |
| `make_reduced_hamiltonian` | `(molecular_hamiltonian, n_electrons)` | Returns an `InteractionOperator` with a zero one-body tensor and one-body information folded into the two-body tensor using the electron count. Do not use `n_electrons=1`; the formula divides by `n_electrons - 1`. |
| `antisymtei`, `j_mat`, `k_mat` | `(two_body_integrals)` | Return antisymmetrized, Coulomb, or exchange views of OpenFermion-ordered two-electron tensors. Check ordering before comparing with another chemistry package. |

The `MolecularData` constructor immediately derives `n_atoms`, sorted `atoms`,
`protons`, and `n_electrons` for an explicit geometry. It initializes
`n_orbitals`, `n_qubits`, nuclear repulsion, integral arrays, RDMs, and method
energies as unset (`None`). Large arrays are lazily loaded from the HDF5 record.
`save()` writes metadata and present calculation fields; a missing field is
stored as an empty placeholder. Loading by filename accepts either the base
name or a name ending in `.hdf5`.

The OpenFermion two-electron convention is represented as
`h[p,q,r,s] a†_p a†_q a_r a_s` with a one-half factor applied when the
spin-orbital `InteractionOperator` is formed. Do not transpose tensors merely
to match a chemist/physicist convention without checking the consuming API.

## Optional and special constructors

The chemistry package also exports `make_atom`, `make_atomic_ring`, and
`make_atomic_lattice`; they produce `MolecularData` geometry/metadata objects
and do not perform integrals. The Hamiltonian package exports other specialized
models such as Richardson–Gaudin and d-wave mean-field constructors. Treat
those as model-specific APIs: inspect their signatures and tests before using
them, and do not infer molecular-electronic-structure semantics from their
names.

`geometry_from_pubchem(name, structure=None)` imports `pubchempy` only when
called, requests 3-D then 2-D data when `structure=None`, and returns the first
matching geometry or `None`. The core package declares `pubchempy`, but this
lookup remains an optional online workflow with external service failure modes,
not a deterministic or offline constructor. PySCF, JAX, and ASE belong to the
optional resource/plugin boundary rather than the core model constructors.
