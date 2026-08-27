# Hamiltonian and chemistry data formats

Use these schemas when passing an object to another skill or serializing a
small construction record. They describe public package conventions, not a
requirement to write a file for every model.

## Model construction record

Keep a compact record alongside any generated operator:

```text
model_kind: hubbard | general_hubbard | jellium | plane_wave | molecular
operator_family: FermionOperator | BosonOperator | InteractionOperator | metadata
coefficient_units: caller-defined, explicit
coordinate_units: Angstrom | Bohr/atomic units | not applicable
basis_or_space: site | momentum | dual | molecular spin-orbital | not applicable
flags:
  periodic: bool or not applicable
  spinless: bool or not applicable
  particle_hole_symmetry: bool or not applicable
  plane_wave: bool or not applicable
  include_constant: bool
  e_cutoff: number or null
  non_periodic: bool or not applicable
  period_cutoff: number or null
mode_count: integer or null
tensor_shapes: list or null
constant_policy: included | omitted | separate | unknown
provenance: deterministic construction | loaded record | external backend result
optional_requirements: list
```

Do not use an unlabeled numeric coefficient or coordinate. The same tuple shape
can be physically meaningless if Angstrom and Bohr are mixed.

## Fermionic term representation

A `FermionOperator` has a mapping from terms to coefficients. A term is an
ordered tuple of `(mode, action)` pairs, where `action=1` is creation and
`action=0` is annihilation. The empty tuple is the identity. Number occupation
at mode `p` is `((p, 1), (p, 0))`; the term need not be manually expanded when
using the public operator API.

For standard `fermi_hubbard`:

```text
spinful site s: up = 2*s, down = 2*s + 1
spinless site s: mode = s
number of sites: x_dimension * y_dimension
number of modes: sites * (1 if spinless else 2)
```

A term count is not a mode count. Use `max(mode appearing in terms) + 1` only
when the operator is known to include all relevant modes; an all-zero or empty
operator needs an independently supplied count.

## General Hubbard parameter schema

`HubbardSquareLattice` contains:

```text
x_dimension: positive integer
y_dimension: positive integer
n_dofs: integer degrees of freedom per site
spinless: bool
periodic: bool
```

Its site index is `x + y * x_dimension`. A spinful model has two spin values
per DOF, with `Spin.UP == 0` and `Spin.DOWN == 1`. The public index conversion
is:

```text
spin_orbital = site * (n_dofs * n_spin_values) + dof * n_spin_values + spin
(site, dof, spin) = lattice.from_spin_orbital_index(spin_orbital)
```

General-Hubbard parameter tuples are:

```text
tunneling_parameters:   (edge_type, (dof_a, dof_b), coefficient)
interaction_parameters: (edge_type, (dof_a, dof_b), coefficient,
                         SpinPairs.ALL | SpinPairs.SAME | SpinPairs.DIFF)
potential_parameters:    (dof, coefficient)
```

The fourth interaction field is optional and defaults to `SpinPairs.ALL`; it is
ignored for a spinless lattice. Edge types are validated by the lattice. The
model's potential convention uses `-coefficient * number`; magnetic field is a
separate spinful field term.

## Grid schema

```text
Grid(
  dimensions: positive int,
  length: int or tuple/list[int] with one count per dimension,
  scale: positive float or ndarray with cell vectors as columns,
)
```

Derived values include:

```text
length: per-axis point counts
dimensions: number of spatial dimensions
num_points: product(length)
volume_scale(): absolute cell volume
```

`all_points_indices()` yields tuples in Cartesian-product order. Position
vectors are centered using per-axis integer shifts. Momentum vectors use the
reciprocal cell. `orbital_id(indices, spin=None)` is spinless; supplying spin
interleaves the spin value after the spatial index. Keep the tuple/list versus
scalar distinction and pass a float for a scalar scale.

## Jellium and plane-wave input schema

A plane-wave nuclear geometry is:

```python
[("H", (x, y, z)), ("He", (x2, y2, z2))]
```

The coordinate tuple length must equal `grid.dimensions`. Plane-wave
constructors interpret these coordinates as atomic units. Element symbols must
be in OpenFermion's periodic-element table. `jellium_model` without geometry
contains electron kinetic and electron-electron terms; `plane_wave_hamiltonian`
may add electron-nuclear terms. `include_constant` is an identity/Madelung
shift, not automatically the full nuclear repulsion.

## MolecularData metadata schema

Explicit construction requires:

```text
geometry: list[(element: str, (x: float, y: float, z: float))]
basis: str
multiplicity: positive integer-valued number
charge: integer (default 0)
description: str (default empty)
filename: optional base path/name; .hdf5 is normalized away
```

Geometry coordinates are in Angstroms. For an explicit geometry, the
constructor derives:

```text
name: element-counts + basis + multiplicity label + charge/description
n_atoms: len(geometry)
atoms: symbols sorted by atomic number
protons: atomic numbers in the same sorted order
n_electrons: sum(protons) - charge
```

A string `geometry` is a special file/identifier-compatible form with reduced
automatic atom metadata; prefer an explicit list for new constructions.
`multiplicity` is a spin multiplicity, not the number of unpaired electrons.

Calculation fields can be present or absent:

```text
n_orbitals, n_qubits, nuclear_repulsion
hf_energy, orbital_energies, canonical_orbitals, overlap_integrals
one_body_integrals, two_body_integrals
mp2_energy
cisd_energy, cisd_one_rdm, cisd_two_rdm
fci_energy, fci_one_rdm, fci_two_rdm
ccsd_energy, ccsd_single_amps, ccsd_double_amps
general_calculations: dict[str, value]
```

`None` means the object has no value in memory (and usually no saved result).
It does not mean zero. Large arrays are lazy properties when loaded from HDF5.
A filename points to a record; it is not itself evidence that a method ran.

## Integral tensor and operator shapes

For `n_orbitals` spatial orbitals:

```text
one_body_integrals.shape == (n_orbitals, n_orbitals)
two_body_integrals.shape ==
    (n_orbitals, n_orbitals, n_orbitals, n_orbitals)
```

`get_molecular_hamiltonian()` spin-doubles the one-body dimension and returns
an `InteractionOperator` whose one-body tensor is `(n_qubits, n_qubits)` and
two-body tensor is `(n_qubits, n_qubits, n_qubits, n_qubits)`, with
`n_qubits = 2 * n_orbitals` for the conventional spin-orbital expansion. Its
constant is the nuclear repulsion, plus an active-space core adjustment when
one is requested. The returned two-body tensor has already been multiplied by
the molecular Hamiltonian's one-half coefficient; do not add another factor
when handing it to a transform.

`make_reduced_hamiltonian` preserves the tensor dimension, returns a zero
one-body tensor, and modifies the two-body tensor using a supplied fixed
`n_electrons`. The constant is preserved. This is a representation change under
a number-sector assumption, not a generic tensor truncation.

## File and provenance rules

`MolecularData.save()` writes a record at `filename + ".hdf5"` containing
metadata and present calculation fields. `MolecularData(filename=...)` loads
metadata and initializes lazy properties; it accepts a filename with or without
the suffix. `get_from_file(property_name)` returns `None` when the field is not
available. Use a writable, caller-selected location for tests and cleanup
created records; do not assume the package's default data directory is writable.

Record whether a geometry came from a literal, a local geometry text file, or a
network lookup; whether tensors were supplied or computed; and which optional
backend produced them. This distinction prevents a metadata-only object from
being described as a solved molecule.
