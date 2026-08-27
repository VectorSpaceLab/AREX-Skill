# Structure and coordinate contracts

## PDB

A PDB contains records that OpenMM parses into a `Topology` and positions. The topology includes chains, residues, atoms, bonds when inferable, and periodic-box metadata when supplied; positions must have exactly one coordinate for each atom. Chain IDs and residue IDs are identifiers, not proof of biological identity. Preserve insertion codes and alternate-location decisions in provenance.

Before simulation, check:

- intended chain IDs and whether each chain is complete;
- residue name, numeric residue ID, insertion code, and atom count;
- duplicate atom names within a residue;
- missing heavy atoms, hydrogens, termini, caps, waters, ions, and alternate locations;
- whether ligand bonds and formal chemistry are actually represented.

PDB residue IDs may be non-contiguous and may include insertion codes. The bundled range helper accepts ordinary numeric inclusive ranges and fails conservatively on non-numeric IDs instead of silently reinterpreting them.

## FASTA and SDF

FASTA records sequence and headers; it cannot supply 3-D coordinates, protonation, bond geometry, or a simulation topology. Use it to cross-check chain identity or missing sequence, not as a replacement for a PDB.

SDF carries small-molecule coordinates and chemistry such as bonds and formal charges. Conversion to a PDB can discard bond orders, charges, stereochemistry, or atom naming. Preserve the SDF and conversion settings; after conversion, compare atom count, residue mapping, and chemistry with a toolkit that understands the molecule.

## Topology-preserving edits

A chain/residue selection is complete only when every retained atom retains its coordinate and every retained bond joins retained atoms. A naming normalization must not be described as parameterization. External protonation, capping, and ligand-parameterization tools may add atoms or alter bonds; always revalidate after those steps.
