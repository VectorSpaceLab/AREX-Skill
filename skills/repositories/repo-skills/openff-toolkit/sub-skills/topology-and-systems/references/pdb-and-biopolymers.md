# PDB and Biopolymer Guidance

This reference distills OpenFF Toolkit topology/PDB behavior into operational rules for future agents. It is self-contained and does not require reopening the source repository docs or tests.

## PDB Loader Mental Model

`Topology.from_pdb(...)` reads a PDB through OpenMM, then assigns chemistry into OpenFF molecules.

It succeeds when each atom and bond in the PDB can be assigned to one of these sources:

- Supported protein residue templates for the 20 canonical amino acids using standard PDB residue and atom names.
- Supported water recognition, especially residue `HOH` with atom names `H1`, `O`, and `H2`, or ATOM records with elements plus `CONECT` records.
- Supported Sage-compatible monoatomic ions: `Li+`, `Na+`, `K+`, `Rb+`, `Cs+`, `F-`, `Cl-`, `Br-`, and `I-`.
- Exact user-provided OpenFF `Molecule` objects passed as `unique_molecules` for arbitrary HETATM or nonstandard molecules.
- Experimental custom substructure inputs when the task explicitly needs unsupported polymer-like chemistry.

The output is a `Topology` containing full OpenFF molecule objects, not just a coordinate topology.

## Required PDB Conditions

For robust `Topology.from_pdb` loading:

- All hydrogens must be explicit; missing hydrogens usually prevent chemistry assignment.
- Every particle must correspond to an atomic nucleus; virtual sites or extra points are not allowed in the `Topology` model.
- Protein/polymer atom and residue names must follow PDB Chemical Component Dictionary conventions for supported residues.
- Bond connectivity must come from either residue templates or valid `CONECT` records.
- `CONECT` records must represent chemical bonds, not angle constraints or nonbonded relationships.
- Redundant `CONECT` records are allowed when they repeat connectivity already implied by residue templates.
- A `CRYST` record, if present, is interpreted as periodic box vectors in Angstroms.

## `unique_molecules` for HETATM and Small Molecules

Use `unique_molecules` when a PDB contains arbitrary small molecules, ligands, unusual ions, cofactors, or HETATM records that are not covered by standard residue templates.

Rules:

- Pass each chemically distinct species exactly once.
- The species does not need to appear in the PDB; zero-copy reference molecules are allowed.
- The PDB must contain explicit element information and `CONECT` records for these molecules, because PDB does not encode bond orders or formal charges.
- The PDB molecule must exactly match the reference molecule's element/connectivity graph. Substructures and superstructures are not accepted.
- Bond orders and formal charges are taken from the OpenFF reference molecule.
- Stereochemistry is assigned from 3D PDB geometry, even if it conflicts with the reference molecule.
- Overlapping possible references can still work when each final PDB component exactly matches one reference.

Example pattern:

```python
ethanol = Molecule.from_smiles("CCO")
cyclohexane = Molecule.from_smiles("C1CCCCC1")
topology = Topology.from_pdb("system.pdb", unique_molecules=[ethanol, cyclohexane])
```

If a future task starts from a PDB plus ligand SDF/SMILES, construct the ligand `Molecule` first using molecule I/O guidance, then pass it here through `unique_molecules`.

## Proteins, Waters, and Ions

Protein loading currently targets canonical amino acid residues and their supported caps/states in the bundled residue substructure library. The loader can assemble complete protein molecules and expose residue/chain hierarchy iterators when metadata is present.

Operational guidance:

- Prefer PDBs that already include hydrogens and correct protonation states.
- Keep standard atom names; misnamed atoms can prevent residue template assignment.
- Treat noncanonical amino acids, covalent ligands, post-translational modifications, polymers beyond the supported templates, and unusual terminal states as custom chemistry requiring explicit checks.
- For waters, prefer standard `HOH` residue naming and `H1`, `O`, `H2` atom names, or include elements and `CONECT` records.
- Common monatomic ions listed above are recognized; pass unsupported ions through `unique_molecules`.

## Custom Substructures

`Topology.from_pdb` exposes two experimental inputs:

- `_custom_substructures`: a dictionary adding residue-like substructure SMARTS for polymer perception.
- `_additional_substructures`: molecule-based additional substructure definitions, most stable for standalone molecules not bonded into a larger protein/polymer.

Use them cautiously:

- They are private/experimental parameters and may change.
- The SMARTS format must match the residue substructure library style, including explicit atomic number, degree, formal charge, tagged atoms, and neighboring wildcard atoms.
- Do not recommend them as a default ligand-loading path; use `unique_molecules` first for exact HETATM molecules with `CONECT` records.
- When used, document why ordinary `unique_molecules` or standard residue templates are insufficient.

## Hierarchy Metadata

OpenFF stores hierarchy information on atoms as metadata:

- `atom.metadata["residue_name"]`
- `atom.metadata["residue_number"]`
- `atom.metadata["insertion_code"]`
- `atom.metadata["chain_id"]`

After PDB/OpenMM/MDTraj loading, these fields can be used through hierarchy schemes:

```python
residues = list(topology.hierarchy_iterator("residues"))
chains = list(topology.hierarchy_iterator("chains"))
```

Important assumptions:

- Hierarchy metadata is for interoperability and user convenience.
- OpenFF parameter assignment does not use residue or chain metadata.
- Editing hierarchy metadata after loading can make conversion to other packages surprising because other packages impose stricter hierarchy rules.
- `hierarchy_iterator("residues")` skips molecules that do not define residue schemes; dynamic `topology.residues` is stricter and may raise if schemes are absent.
- OpenFF does not globally sort residues by residue number across molecules; topology molecule order wins.

## OpenFF vs OpenMM/RDKit/OpenEye Hierarchy Differences

Different toolkits require different hierarchy completeness.

OpenFF:

- Metadata fields may be absent on some or all atoms.
- Residues/chains are not required for parameterization.
- Residues need not be globally sorted by residue number.

OpenMM:

- Every atom must belong to a residue and chain.
- Residues must be contiguous within a chain.
- `Topology.to_openmm()` creates default metadata when OpenFF atoms lack it: residue name `UNK`, residue number `0`, insertion code space, chain id `X`.
- A residue or chain will never span multiple OpenFF molecules.

RDKit:

- Some atoms may have no PDB residue information.
- When any common residue metadata is set during conversion, missing fields can be filled by RDKit defaults.

OpenEye:

- Residue fields are expected to be populated; OpenFF conversion fills defaults when needed.
- In the inspected environment OpenEye was unavailable, so prefer RDKit/BuiltIn-backed workflows unless the user provides an OpenEye-capable environment.

## Atom Names and PDB Output

PDB consumers often require atom names to be unique within a residue or molecule. OpenFF conversion defaults reflect this:

```python
openmm_topology = topology.to_openmm(ensure_unique_atom_names="residues")
topology.to_file("out.pdb", positions=positions, ensure_unique_atom_names="residues")
```

Guidance:

- Use `"residues"` by default for PDB/protein-style systems.
- Use `True` when molecule-wide uniqueness is more important than residue-local preservation.
- Use `False` only when preserving original names is required and duplicates/empty names are acceptable.
- PDB truncates atom names, so uniqueness cannot be guaranteed for names that exceed PDB field limits.
- If writing a PDB with no positions supplied, make sure every molecule has at least one conformer or pass explicit positions.

## PDB-to-ForceField Handoff

A successfully loaded `Topology` still lacks applied force field parameters.

Typical handoff:

```python
forcefield = ForceField("openff-2.2.0.offxml")
interchange = forcefield.create_interchange(topology)
openmm_system = forcefield.create_openmm_system(topology)
```

For mixed protein/small-molecule workflows, expect a boundary with protein force fields, Interchange, or OpenMM/Amber machinery. This sub-skill should ensure the OpenFF topology and ligand chemistry are correct, then route detailed parameter assignment/export decisions to force-field or backend-specific guidance.
