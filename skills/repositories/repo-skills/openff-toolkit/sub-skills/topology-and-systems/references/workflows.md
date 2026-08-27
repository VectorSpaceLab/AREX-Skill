# Topology Workflows

These recipes assume OpenFF Toolkit is importable and that molecule construction has already been handled. For molecule construction details, route to `../molecules-and-io/SKILL.md`.

## Build a Topology from Molecules

Use for small-molecule boxes, repeated ligands, and simple systems where molecules are already OpenFF `Molecule` objects.

```python
from openff.toolkit import Molecule, Topology

ethanol = Molecule.from_smiles("CCO")
benzene = Molecule.from_smiles("c1ccccc1")
topology = Topology.from_molecules([ethanol, benzene, benzene])

print(topology.n_molecules)
print(topology.n_unique_molecules)
print(topology.identical_molecule_groups)
```

Notes:

- Input order becomes topology molecule order.
- Repeated identical species are separate topology molecules but share an `identical_molecule_groups` representative.
- Use `add_molecules([...])` instead of repeated `add_molecule(...)` when adding many molecules.

## Load a PDB with HETATM Ligands

Use when the PDB contains protein/water/ions plus one or more nonstandard molecules.

```python
from openff.toolkit import Molecule, Topology

ligand = Molecule.from_smiles("CCO")
topology = Topology.from_pdb("complex.pdb", unique_molecules=[ligand])

residue_count = len(list(topology.hierarchy_iterator("residues")))
chain_count = len(list(topology.hierarchy_iterator("chains")))
```

Checklist before calling:

- The PDB has explicit hydrogens.
- HETATM ligand atoms have element information.
- HETATM ligand bonds are specified by `CONECT` records.
- The reference `Molecule` has the intended formal charges, bond orders, and stereochemistry.
- Every chemically distinct HETATM molecule appears once in `unique_molecules`.

If the loader raises an unassigned chemistry error, inspect whether a PDB component is a substructure/superstructure of the reference, lacks hydrogens, lacks `CONECT`, or has nonstandard atom/residue names.

## Convert OpenMM or MDTraj Topologies

Use when a system has already been loaded by OpenMM or MDTraj but needs OpenFF chemistry.

```python
from openff.toolkit import Molecule, Topology

ethanol = Molecule.from_smiles("CCO")
cyclohexane = Molecule.from_smiles("C1CCCCC1")

openff_topology = Topology.from_openmm(
    openmm_topology,
    unique_molecules=[ethanol, cyclohexane],
    positions=positions,
)
```

For MDTraj:

```python
openff_topology = Topology.from_mdtraj(
    mdtraj_topology,
    unique_molecules=[ethanol, cyclohexane],
    positions=positions,
)
```

Rules:

- Pass all unique chemical species exactly once.
- OpenMM/MDTraj hierarchy schemes are used; hierarchy metadata from `unique_molecules` is not the source of truth.
- Atom order from the input topology is preserved.
- Virtual sites cannot be represented by OpenFF `Topology` and must be handled elsewhere.

## Query Repeated Chemistry

Use `identical_molecule_groups` and `chemical_environment_matches` to reason about repeated copies.

```python
matches = topology.chemical_environment_matches("[#6:1]-[#8:2]")
for match in matches:
    print(match.topology_atom_indices, match.reference_atom_indices)
```

Use cases:

- Identify every occurrence of a SMARTS pattern across repeated molecules.
- Map reference-molecule atom indices to topology atom indices.
- Debug why parameter labeling or substructure matching sees multiple copies.

## Add Constraints

Use `add_constraint` for topology-level constraint annotations.

```python
from openff.units import unit

topology.add_constraint(0, 1, 1.01 * unit.angstrom)
topology.add_constraint(2, 3)          # unspecified distance
topology.add_constraint(2, 3, False)   # remove it
```

Notes:

- Atom indices are topology atom indices.
- Nonbonded atom pairs are allowed.
- Constraints are recorded symmetrically.
- Adding the same unspecified constraint twice raises an error.
- Force field creation is responsible for turning topology and force field data into engine-level constraints.

## Write a PDB

Use when a user needs a coordinate PDB from an OpenFF topology.

```python
from openff.units import unit
import numpy as np

positions = np.zeros((topology.n_atoms, 3)) * unit.angstrom
topology.to_file(
    "system.pdb",
    positions=positions,
    file_format="PDB",
    keep_ids=False,
    ensure_unique_atom_names="residues",
)
```

Guidance:

- Prefer explicit positions for reproducible scripts.
- If `positions=None`, every molecule must have a conformer.
- `file_format` currently supports only `"PDB"`.
- Use `ensure_unique_atom_names="residues"` for protein/PDB systems.
- Use `keep_ids=True` only if preserving chain/residue ids matters more than OpenMM-generated IDs.

## Convert to OpenMM Topology

Use for interoperability when a downstream library wants an `openmm.app.Topology`.

```python
openmm_topology = topology.to_openmm(ensure_unique_atom_names="residues")
```

Important:

- This is not an OpenMM `System` and contains no force field parameters.
- Missing residue/chain metadata is replaced with defaults (`UNK`, `0`, space insertion code, `X`).
- Bond orders are carried where available, but virtual sites are not produced.

## Create an OpenMM System

Use after a valid topology is ready and the task asks for OpenMM simulation objects.

```python
from openff.toolkit import ForceField

forcefield = ForceField("openff-2.2.0.offxml")
openmm_system = forcefield.create_openmm_system(topology)
```

Boundary notes:

- This sub-skill owns topology assembly and validation.
- Force field source choice, charge assignment, handler options, and parameter troubleshooting belong in `../smirnoff-force-fields/SKILL.md`.
- Toolkit backend availability for charges and file conversion belongs in `../toolkit-backends/SKILL.md`.

## Create Interchange for Engine Export

Use when the user wants Amber, GROMACS, LAMMPS, or other engine files through Interchange.

```python
from openff.toolkit import ForceField

forcefield = ForceField("openff-2.2.0.offxml")
interchange = forcefield.create_interchange(topology)

# Interchange-specific exporters live on the Interchange object and may require
# the openff-interchange package and engine-specific tools for validation.
```

Guidance:

- `ForceField.create_interchange(topology)` creates an in-memory Interchange object and does not create an OpenMM `System` under the hood.
- Engine export and validation can require optional packages or external executables.
- Keep topology/PDB fixes here; route exporter/API details to the Interchange or force-field-facing guidance available in the root skill.

## Visualize in a Notebook

Use for quick inspection in Jupyter when `nglview` is installed and positions exist.

```python
widget = topology.visualize()
```

Caveats:

- Requires every molecule to have positions.
- The default connectivity display can be inferred from positions and may not match topology connectivity exactly.
- `ensure_correct_connectivity=True` is not implemented.
