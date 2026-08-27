# Hamiltonian and chemistry workflows

These recipes are intentionally small and source-independent. They construct
symbolic objects or metadata only. Before a real run, replace the tiny values,
write down units and flags, and apply a workload budget.

## 1. Make a 2x2 Hubbard operator with deliberate flags

A reproducible 2x2 request must answer four questions before construction:

- **Periodic?** `True` wraps the square cell. `False` leaves an open boundary.
- **Spinless?** `False` (the default) gives up/down modes per site; `True`
  gives one mode per site and ignores magnetic field.
- **Particle-hole symmetric?** `True` replaces occupation factors with
  `n - 1/2` and can introduce constants; `False` uses ordinary occupations.
- **Parameter convention?** In this API `tunneling=t`, `coulomb=U`,
  `chemical_potential=mu`, and hopping is `-t`.

```python
from openfermion.hamiltonians import fermi_hubbard

h = fermi_hubbard(
    2, 2,
    tunneling=0.5,
    coulomb=2.0,
    chemical_potential=0.0,
    magnetic_field=0.0,
    periodic=False,                 # choose, do not inherit the default
    spinless=False,                 # 8 spin orbitals for this case
    particle_hole_symmetry=False,
)
print(len(h.terms))
```

Validate `max(mode) + 1` against 8 for this spinful case (or 4 for spinless)
and inspect the identity coefficient separately. Do not use the number of terms
as the mode count. For periodic 2x2, the implementation avoids duplicate
wraparound edges in the two-site dimensions; edge counts therefore need to be
read from the actual operator or `HubbardSquareLattice`, not guessed.

### General/multiband variant

Use `HubbardSquareLattice(2, 2, n_dofs=2, periodic=False, spinless=False)`
when each site has two spatial degrees of freedom. Construct typed parameter
records and call `model.hamiltonian()`:

```python
from openfermion.hamiltonians import FermiHubbardModel
from openfermion.utils import HubbardSquareLattice, SpinPairs

lattice = HubbardSquareLattice(2, 2, n_dofs=2, periodic=False)
model = FermiHubbardModel(
    lattice,
    tunneling_parameters=[
        ("neighbor", (0, 0), 0.5),
        ("onsite", (0, 1), 0.2),
    ],
    interaction_parameters=[
        ("onsite", (0, 1), 1.5, SpinPairs.ALL),
    ],
    potential_parameters=[(0, 0.1), (1, -0.1)],
    magnetic_field=0.0,
)
h = model.hamiltonian()
```

Onsite tunneling between the same DOF is invalid. An onsite `SAME`
interaction for the same DOF is invalid because it would interact a spin
orbital with itself. Use `lattice.site_pairs_iter(edge_type, ordered=False)`
to make edge accounting explicit.

## 2. Build a bounded jellium or plane-wave model

Choose the real-space cell and mode budget first. `Grid(1, 4, 2.0)` means a
one-dimensional cell with four points and total length 2.0; use a float for a
scalar scale. A two-dimensional example is `Grid(2, (2, 2), 3.0)`. The
operator has `grid.num_points` spinless modes or twice that many spinful modes.

```python
from openfermion.hamiltonians import jellium_model
from openfermion.utils import Grid

grid = Grid(dimensions=1, length=4, scale=2.0)
h_pw = jellium_model(grid, spinless=True, plane_wave=True, e_cutoff=10.0)
h_dual = jellium_model(grid, spinless=True, plane_wave=False)
```

`plane_wave=True` uses reciprocal/momentum modes. `False` uses the dual basis
and can include a Madelung identity constant. A cutoff filters plane-wave
kinetic and potential modes, so record it with the Hamiltonian. Jellium
potential formulas support physical dimensions 1, 2, and 3; the zero momentum
transfer is skipped. Do not equate a dual-basis constant with a measured total
energy. In this package version, the `jellium_model` wrapper adds the constant
twice when both `plane_wave=False` and `include_constant=True`; the direct
`dual_basis_jellium_model` constructor adds it once. Verify and record the
identity coefficient for that combination.

For nuclei, use a dimension-matched geometry and keep units distinct from
`MolecularData`:

```python
from openfermion.hamiltonians import plane_wave_hamiltonian

h = plane_wave_hamiltonian(
    grid,
    geometry=[("H", (0.0, 0.0, 0.0))],  # coordinate length must match grid
    spinless=True,
    plane_wave=True,
    e_cutoff=10.0,
)
```

The geometry tuple must have one coordinate in 1-D, two in 2-D, or three in
3-D, and the element symbol must be in the package's periodic table. With
`geometry` present, do not request `include_constant=True`; the constructor
rejects that combination. For non-periodic corrections, select and record a
`period_cutoff` rather than relying on an undocumented physical assumption.

The external-potential helpers are useful when composing pieces, but they are
still finite-grid approximations. They do not replace a converged chemistry
calculation or automatically include nuclear-nuclear energy.

## 3. Create molecular metadata without pretending to run chemistry

This is a safe setup stage:

```python
from openfermion.chem import MolecularData

molecule = MolecularData(
    geometry=[("H", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, 0.7414))],
    basis="sto-3g",
    multiplicity=1,
    charge=0,
    description="tiny",
    filename="h2-tiny",
)
assert molecule.n_atoms == 2
assert molecule.n_electrons == 2
assert molecule.n_orbitals is None
assert molecule.one_body_integrals is None
```

The coordinates above are Angstroms. The constructor derives the name
`H2_sto-3g_singlet_tiny`, the sorted atom/proton vectors, and the electron
count. It does not know orbital counts, nuclear repulsion, integrals, HF/MP2/
CI/CC energies, or RDMs. Those fields remain unset until a supported backend
or a previously saved record supplies them.

Calling `molecule.save()` is an explicit file write and creates an HDF5 record
at the base `filename` with an `.hdf5` suffix. For a metadata-only dry run,
do not call it. To load an existing record, use `MolecularData(filename=...)`;
when a required constructor field is missing, the filename is a load request,
not a request to infer chemistry. Lazy large properties are fetched from the
record only when accessed.

## 4. Require integral evidence before making an electronic Hamiltonian

After a backend has populated and saved both integral tensors, load the record
and use:

```python
molecule = MolecularData(filename="existing-record")
one_body, two_body = molecule.get_integrals()
h = molecule.get_molecular_hamiltonian()
```

`get_integrals()` raises `MissingCalculationError` when either tensor is absent.
`get_molecular_hamiltonian()` returns an `InteractionOperator`; its constant is
nuclear repulsion, and its one-/two-body tensors are in spin-orbital form. Even
indices are alpha/up and odd indices beta/down. If an active space is desired,
pass spatial-orbital `occupied_indices` and `active_indices`; the returned core
adjustment is added to the constant.

Do not call `load_molecular_hamiltonian` as though it runs PySCF: it loads a
record by its systematic metadata identity and extracts an existing
Hamiltonian. If a plugin's result is not present, stop at the missing-data
error and report the backend requirement.

## 5. Fold one-body terms into a reduced Hamiltonian

Use this only when a downstream algorithm explicitly requires a two-body-only
`InteractionOperator` and the fixed electron number is known:

```python
from openfermion.chem import make_reduced_hamiltonian

reduced = make_reduced_hamiltonian(h, n_electrons=molecule.n_electrons)
assert reduced.one_body_tensor.shape == h.one_body_tensor.shape
assert not reduced.one_body_tensor.any()
```

The returned operator keeps the constant and sets the one-body tensor to zero;
the two-body tensor receives a wedge-like correction scaled by
`1 / (4 * (n_electrons - 1))`. This is not an equivalent operator over all
particle-number sectors. It is equivalent only under the fixed-number premise.
Reject or clarify an electron count of one before calling it.

## 6. Handoff to transforms or resource estimation

Provide the next stage with:

```text
operator family: FermionOperator or InteractionOperator
mode count / tensor shapes: explicit
constant: included, omitted, or separate
basis: site, momentum, dual, or molecular spin-orbital
index convention: explicit
flags: periodic, spinless, particle-hole, cutoff, non-periodic correction
units: coefficient and coordinate units
provenance: metadata only, loaded integrals, or backend result
```

Then route mapping and normal-ordering questions to
[operators-and-transforms](../../operators-and-transforms/SKILL.md), circuit
questions to the circuits sibling, and sparse/eigensolver/RDM questions to the
analysis sibling. Resource-estimation helpers can consume the resulting
operator or tensors, but their optional package and backend requirements must
be checked independently.

## 7. Optional integrations and safe boundaries

- **PubChem:** `geometry_from_pubchem` imports the core-declared `pubchempy`
  dependency lazily and performs an online request. The lookup itself is an
  optional workflow. Keep it out of deterministic tests; validate returned
  coordinates and units before creating `MolecularData`.
- **PySCF/electronic-structure plugins:** install and invoke outside this
  sub-skill. They may be platform/backend constrained and may populate HDF5
  calculation fields, but OpenFermion core does not infer those results.
- **ASE/JAX/resource estimation:** optional integrations. Treat absent imports,
  unsupported accelerators, and version mismatches as capability boundaries,
  not as reasons to alter the model silently.
- **Cloud/precomputed molecular files:** acquiring a record is outside a
  bounded construction smoke test. If used, state the record version and
  fields actually present.
