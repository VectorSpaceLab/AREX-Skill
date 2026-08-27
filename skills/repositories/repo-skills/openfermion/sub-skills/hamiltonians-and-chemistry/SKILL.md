---
name: hamiltonians-and-chemistry
description: "Build deterministic lattice, jellium, plane-wave, and molecular
  Hamiltonian inputs; preserve chemistry data contracts; and route mapping or
  external chemistry work safely."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent: openfermion
license: Apache 2.0
---

# Hamiltonians and chemistry

Load this skill when the task is about choosing or constructing a model
Hamiltonian, a discretization, or chemistry metadata. It covers the symbolic
input side of OpenFermion. It does **not** run a quantum-chemistry package,
query PubChem, download a dataset, or choose a qubit mapping for the caller.

## Decide the model before calling an API

1. **Hubbard/lattice model:** choose the site shape, boundary condition,
   spinless versus spinful convention, particle-hole shift, and units of the
   coefficients. Use `fermi_hubbard` for the standard 2-D square model, or
   `FermiHubbardModel` plus `HubbardSquareLattice` for multiple degrees of
   freedom and typed edges.
2. **Uniform electron gas:** choose a `Grid` (dimension, point counts, and
   real-space cell), spin convention, plane-wave versus dual basis, cutoff,
   and whether a Madelung constant is actually wanted. Use `jellium_model`.
3. **Nuclei in a periodic cell:** validate a geometry list of
   `(element, coordinates)` tuples against the grid dimension, then use
   `plane_wave_hamiltonian`. Coordinates are in atomic units for plane-wave
   constructors; do not silently pass `MolecularData`'s Angstrom geometry.
4. **Molecular electronic structure:** construct or load `MolecularData` with
   geometry, basis, multiplicity, and charge. Metadata alone is not an
   integral or energy calculation. Call `get_molecular_hamiltonian()` only
   after the required integral data exists.
5. **Reduced electronic Hamiltonian:** start from an
   `InteractionOperator`, pass a positive electron count to
   `make_reduced_hamiltonian`, and record that the resulting two-body tensor
   is particle-number dependent.

The full signatures, index conventions, tensor shapes, and output contracts
are in [api-reference.md](references/api-reference.md). Reusable recipes and
decision gates are in [workflows.md](references/workflows.md).

## Minimal deterministic entry points

For a bounded smoke check, run the bundled
[build_tiny_hamiltonian.py](scripts/build_tiny_hamiltonian.py) helper by its
resolved skill path from any working directory:

```text
python <skill-directory>/scripts/build_tiny_hamiltonian.py --model hubbard --periodic
python <skill-directory>/scripts/build_tiny_hamiltonian.py --model molecular
```

The helper constructs a 2x2 spinful Hubbard operator (no file or network
access) or an H2 `MolecularData` metadata object. Its JSON output reports
choices and small structural facts, not an energy or a chemistry result.

## Hubbard construction contract

`fermi_hubbard(x_dimension, y_dimension, tunneling, coulomb, ...)` returns a
`FermionOperator`. A spinful `x * y` grid has `2*x*y` modes; a spinless grid
has `x*y`. Even modes are spin-up and odd modes are spin-down for the standard
constructor. Hopping is `-t`; chemical potential contributes `-mu*n`; in the
spinful case the magnetic field shifts up/down occupations with opposite
signs. The default is periodic and spinful, so state those flags explicitly
in reproducible work.

`particle_hole_symmetry=True` replaces each number factor by `n - 1/2`. This
changes both constants and interaction terms; it is not a cosmetic label.
For spinless models `magnetic_field` is ignored. Small dimensions and periodic
boundaries have deduplication behavior, so do not infer edge counts by
multiplying a generic degree by the number of sites; inspect the operator or
lattice iterator.

For a general model, `HubbardSquareLattice` exposes `onsite`, `neighbor`,
`horizontal_neighbor`, `vertical_neighbor`, and `diagonal_neighbor` edge types.
`FermiHubbardModel` parameter tuples are `(edge_type, (dof_a, dof_b),
coefficient[, spin_pairs])` for tunneling/interactions and `(dof, coefficient)`
for potentials. Validate same-dof onsite tunneling and same-spin self
interactions before constructing a large model.

## Chemistry data lifecycle

`MolecularData` stores a molecule definition and calculation results in an
HDF5-backed record. Geometry is a list of `(symbol, (x, y, z))` tuples in
Angstroms; `basis` is a basis-set label; `multiplicity` is a positive integer;
and `charge` is the total charge. The constructor derives a name, atom/proton
metadata, and electron count, but leaves orbitals, integrals, nuclear
repulsion, and method energies unset until supplied or loaded. `save()` writes
the record to `filename + ".hdf5"`; it is not needed for metadata-only use.

Use `get_integrals()` to require both one- and two-electron tensors. Use
`get_molecular_hamiltonian()` to obtain an `InteractionOperator` with the
nuclear-repulsion constant and spin-orbital tensors; optional active-space
indices are spatial-orbital indices and core adjustment changes the constant.
`MissingCalculationError` is the expected signal for absent computed data.
See [data-formats.md](references/data-formats.md) before handing tensors to a
transform or resource-estimation workflow.

PubChem (`geometry_from_pubchem`) is an optional, network-dependent workflow;
the core distribution declares `pubchempy`, but the function imports it only
when called. `structure` is `None`, `"2d"`, or `"3d"`. PySCF and other chemistry
backends are separate plugins, not core constructors. ASE/JAX and the
`resources` extra are optional boundaries: detect and document their
installation and backend requirements, and do not claim that metadata
construction executed them.

## Handoff and routing

After building a `FermionOperator` or `InteractionOperator`, route qubit
mapping, normal ordering, transforms, and operator-family conversion to
[operators-and-transforms](../operators-and-transforms/SKILL.md). Route circuit
synthesis or time evolution to the circuits sibling. Route sparse matrices,
eigensolvers, RDM reconstruction, or measurements to the analysis sibling.
This skill may provide the source operator and its mode/tensor contract, but it
does not silently map, simulate, diagonalize, or run an external plugin.

Before handoff, record:

- model, basis, units, geometry/grid, and all non-default flags;
- mode count or tensor shape and index convention;
- whether constants are included and whether a cutoff was applied;
- whether data is metadata, loaded integrals, or a computed method result;
- optional dependency, network, plugin, and workload boundaries; and
- the intended next sibling and requested acceptance check.

Use [troubleshooting.md](references/troubleshooting.md) for actionable
recovery of import, geometry, shape, file, plugin, and model-flag failures.
