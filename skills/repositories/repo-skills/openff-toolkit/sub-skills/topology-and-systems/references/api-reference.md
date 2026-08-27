# Topology API Reference

Verified against OpenFF Toolkit `0.0.1.dev1+g120f71473` with RDKit and the built-in toolkit wrappers available. OpenEye, AmberTools, and NAGL were unavailable in the inspected environment.

## Imports

```python
from openff.toolkit import Molecule, Topology, ForceField
from openff.units import unit
```

Use `Molecule` construction guidance from `../molecules-and-io/SKILL.md`; this reference assumes molecules are already chemically valid OpenFF molecules.

## Constructors and Mutators

### `Topology.from_molecules`

Signature:

```python
Topology.from_molecules(molecules)
```

Behavior:

- Accepts one OpenFF `Molecule`-like object or an iterable of them.
- Creates a new topology containing one copy of each input molecule in input order.
- Stores deep copies, so later edits to the original `Molecule` do not update the topology copy.
- Use this for SMILES/SDF-derived small-molecule systems, solvent boxes assembled elsewhere, or repeated copies created in Python.

Pattern:

```python
ethanol = Molecule.from_smiles("CCO")
benzene = Molecule.from_smiles("c1ccccc1")
topology = Topology.from_molecules([ethanol, benzene, benzene])
```

### `add_molecule` and `add_molecules`

Signatures:

```python
topology.add_molecule(molecule) -> int
topology.add_molecules(molecules: list) -> list[int]
```

Behavior:

- `add_molecule` adds one molecule and returns its topology molecule index.
- `add_molecules` requires a Python `list`; it is preferred when adding many molecules because cached properties are invalidated once.
- Both add deep copies.
- Passing invalid object types raises `ValueError`.

## PDB, OpenMM, and MDTraj Imports

### `Topology.from_pdb`

Signature:

```python
Topology.from_pdb(
    file_path,
    unique_molecules=None,
    toolkit_registry=GLOBAL_TOOLKIT_REGISTRY,
    _custom_substructures=None,
    _additional_substructures=None,
)
```

Behavior summary:

- Requires `openmm` because it reads through `openmm.app.PDBFile`.
- Accepts a path, `pathlib.Path`, or text file-like object containing PDB content.
- Supports canonical proteins, waters, and common monoatomic ions without user `unique_molecules` when residue and atom names match the supported templates.
- Supports arbitrary HETATM/nonstandard molecules when exact reference `Molecule` objects are passed through `unique_molecules` and the PDB supplies explicit elements and bond connectivity.
- Records atom metadata keys `residue_name`, `residue_number`, `insertion_code`, and `chain_id`, and initializes default hierarchy schemes when possible.
- Reads a PDB `CRYST` record as periodic box vectors in Angstroms.
- For molecules matched through `unique_molecules`, bond orders and formal charges come from the reference molecule; stereochemistry is inferred from PDB geometry and may differ from the reference molecule.

`_custom_substructures` and `_additional_substructures` are experimental. Use them only when the task explicitly needs custom polymer/substructure perception and the future agent can explain their instability.

### `Topology.from_openmm`

Signature:

```python
Topology.from_openmm(openmm_topology, unique_molecules=None, positions=None) -> Topology
```

Behavior:

- Requires every unique chemical species in `openmm_topology` to appear exactly once in `unique_molecules`.
- Preserves atom order from the OpenMM topology; bond ordering is not guaranteed.
- Uses OpenMM elements, connectivity, and any bond orders to match connected components to the reference molecules.
- Raises `MissingUniqueMoleculesError` if `unique_molecules` is `None`.
- Raises `DuplicateUniqueMoleculeError` if two references are graph-indistinguishable under the matching criteria.
- Raises `ValueError` when a component cannot be matched; if the unmatched component looks like isolated atoms from a PDB, suspect missing `CONECT` records.
- Transfers OpenMM atom name, residue name, residue id, insertion code, and chain id into OpenFF atom metadata.
- Transfers periodic box vectors when present and stores `positions` when supplied.
- Raises a virtual-site unsupported error if virtual sites are present; the `Topology` object model does not store virtual sites.

### `Topology.from_mdtraj`

Signature:

```python
Topology.from_mdtraj(mdtraj_topology, unique_molecules=None, positions=None) -> Topology
```

Behavior:

- Requires `mdtraj` and converts via `mdtraj_topology.to_openmm()`.
- Has the same `unique_molecules`, position, matching, and hierarchy behavior as `from_openmm`.
- Use it for topology conversion only; do not assume MDTraj round-trips preserve all OpenFF chemistry.

## Exports and Interoperability

### `Topology.to_openmm`

Signature:

```python
topology.to_openmm(ensure_unique_atom_names="residues") -> openmm.app.Topology
```

Behavior:

- Creates an OpenMM `Topology`; does not create an OpenMM `System`.
- Preserves OpenFF atom order in OpenMM atom ids.
- Adds bonds with OpenMM bond type/order when available; aromatic bonds are marked as aromatic.
- Transfers box vectors if stored on the OpenFF topology.
- Does not populate OpenMM virtual sites.
- Groups atoms into OpenMM chains/residues from atom metadata: `chain_id`, `residue_name`, `residue_number`, and `insertion_code`.
- Defaults missing metadata to residue name `UNK`, residue number `0`, insertion code space, and chain id `X`.
- Never lets an OpenMM residue or chain span more than one OpenFF molecule.

`ensure_unique_atom_names`:

- `"residues"` (default): generate names unique within each residue/hierarchy element when that scheme exists; otherwise within each molecule.
- `True`: generate names unique within each molecule.
- `False`: preserve existing names, including duplicates or empty names.
- Other hierarchy scheme names can be used if the molecules define that scheme.

### `Topology.to_file`

Signature:

```python
topology.to_file(file, positions=None, file_format="PDB", keep_ids=False, ensure_unique_atom_names="residues")
```

Behavior:

- Requires `openmm` and currently supports only PDB output.
- Accepts a path or writable text file-like object.
- Accepts positions as OpenMM quantities, OpenFF unit-wrapped quantities, unitless NumPy arrays interpreted as Angstroms, or `None`.
- When `positions=None`, uses the first conformer of each molecule; if any molecule lacks conformers, gather or provide positions before writing.
- Calls `to_openmm` internally, so the same metadata and atom-name rules apply.
- `keep_ids=True` asks OpenMM PDB writing to preserve residue and chain ids; default `False` lets OpenMM generate ids.
- PDB atom numbering and residue/chain ids may be rewritten by the writer and should not be used as persistent topology identifiers.

## Topology Queries and Properties

### `unique_molecules` and `n_unique_molecules`

`topology.unique_molecules` yields the first instance of each chemically identical molecule group. `topology.n_unique_molecules` counts those groups. This is derived from graph isomorphism over topology molecules, not from object identity.

### `identical_molecule_groups`

Property shape:

```python
{unique_mol_idx: [(topology_mol_idx, atom_map), ...]}
```

Where each key is the first topology molecule index for a unique chemical species. Each `atom_map` maps atom indices of the key molecule to atom indices in the matching topology molecule instance. The representative molecule is included in its own group.

Use this for:

- Mapping SMARTS matches from unique species to repeated copies.
- Detecting repeated solvent/ligand molecules.
- Understanding why `chemical_environment_matches` returns topology atom indices across multiple copies.

### `chemical_environment_matches`

Signature:

```python
topology.chemical_environment_matches(query, aromaticity_model="MDL", unique=False, toolkit_registry=GLOBAL_TOOLKIT_REGISTRY)
```

Behavior:

- `query` must be a SMARTS string with tagged atoms for useful match ordering.
- Runs matching once per chemically unique molecule, then expands matches to all identical copies.
- Returns match objects with `reference_atom_indices`, `reference_molecule`, and `topology_atom_indices`.
- `unique=True` is forwarded to molecule-level SMARTS matching.
- Raises `ValueError` for simple topology molecules that do not support chemical environment matching.

### `nth_degree_neighbors`

Signature:

```python
topology.nth_degree_neighbors(n_degrees)
```

Behavior:

- Yields canonical atom pairs separated by exactly `n_degrees` bonds within each molecule.
- Uses shortest graph distance. In rings, the shortest path controls membership; a pair with paths of length 2 and 4 is considered 2 bonds apart, not 4.

### `add_constraint`, `is_constrained`, and `constrained_atom_pairs`

Signatures:

```python
topology.add_constraint(iatom, jatom, distance=True)
topology.is_constrained(iatom, jatom)
topology.constrained_atom_pairs
```

Behavior:

- Marks atom-index pairs as constrained even if the atoms are not bonded.
- `distance=True` records an unspecified distance to be resolved later.
- A unit-wrapped distance records an explicit constraint distance.
- `distance=False` removes an existing constraint in both directions.
- Constraints are stored symmetrically under `(iatom, jatom)` and `(jatom, iatom)`.
- Re-adding an already unspecified constraint, or replacing an explicit distance with `True`, raises a constraint-exists error.
- Force field parameterization may apply or interpret constraints later; this API only marks them on the topology.

### `hierarchy_iterator` and dynamic hierarchy attributes

Signature:

```python
topology.hierarchy_iterator(iter_name)
```

Behavior:

- Iterates hierarchy elements from molecules that define the named hierarchy scheme, commonly `"residues"` or `"chains"`.
- Yields elements sorted first by topology molecule order and then by each molecule's hierarchy order.
- Molecules without the named iterator are skipped by `hierarchy_iterator`.
- Dynamic attributes such as `topology.residues` are available only when all necessary hierarchy schemes exist; otherwise expect an `AttributeError` and use `hierarchy_iterator` defensively.

### `visualize`

Signature:

```python
topology.visualize(ensure_correct_connectivity=False)
```

Behavior:

- Requires `nglview` and is intended for Jupyter widgets.
- Requires all molecules to have positions.
- `ensure_correct_connectivity=True` is not implemented and raises `ValueError`.
- The default visualization infers connectivity from positions for performance and may not exactly reflect topology connectivity.

## System and Export Handoff

A `Topology` is a chemical graph plus optional hierarchy metadata, positions, box vectors, and constraints. It is not a parameterized molecular mechanics system.

After the topology is correct:

```python
forcefield = ForceField("openff-2.2.0.offxml")
interchange = forcefield.create_interchange(topology)
openmm_system = forcefield.create_openmm_system(topology)
```

Use the SMIRNOFF force-field sub-skill for force field selection and parameter assignment details. Use Interchange guidance when exporting Amber, GROMACS, or other engine input files.
