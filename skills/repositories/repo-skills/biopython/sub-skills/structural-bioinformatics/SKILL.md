---
name: structural-bioinformatics
description: "Use Biopython Bio.PDB to parse, write, traverse, and analyze PDB,
  mmCIF, BinaryCIF, PQR, and PDBML structure data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Structural Bioinformatics

Use this sub-skill when the task involves macromolecular coordinate structures with Biopython's `Bio.PDB`: reading or writing structure files, navigating the SMCRA hierarchy, selecting atoms/residues/chains, handling alternate locations or point-mutant disorder, extracting polypeptides, computing contacts or geometry, or superimposing structures.

## Route here for

- Parsing PDB, PDBx/mmCIF, BinaryCIF, PQR, and PDBML/XML coordinate files into `Structure` objects.
- Choosing between `PDBParser`, `MMCIFParser`, `FastMMCIFParser`, `BinaryCIFParser`, `PDBMLParser`, `PDBIO`, and `MMCIFIO`.
- Traversing `Structure -> Model -> Chain -> Residue -> Atom` objects and using `Selection.unfold_entities`.
- Working with residue IDs, hetero residues, waters, insertion codes, atom IDs, altlocs, disordered atoms, and disordered residues.
- Extracting polypeptides and structure-derived sequences with `PPBuilder` or `CaPPBuilder`.
- Computing distances, angles, dihedrals, vectors, residue/atom neighborhoods, solvent-exposure-style quantities, or structure superpositions.
- Using `PDBList` only when an explicitly network-enabled task needs wwPDB downloads.
- Understanding optional structural tools such as DSSP/mkdssp, NACCESS, MSMS-backed residue depth, PSEA, and related executable-dependent workflows.

## Route elsewhere

- Sequence object construction, `SeqRecord` internals, annotations, feature locations, translation, and reverse-complement behavior: use `sequence-objects-and-features`.
- General sequence/alignment file I/O through `SeqIO`/`AlignIO`, including PDB-derived sequence formats such as `pdb-atom` or `pdb-seqres`: use `file-io-and-format-conversion` unless the task needs coordinate objects.
- BLAST/SearchIO semantics, pairwise sequence alignment, phylogenetic tree I/O, or external aligner orchestration: use `alignment-search-and-phylogeny`.
- Online biological database workflows, Entrez/KEGG/UniProt/ExPASy etiquette, and BioSQL databases: use `web-databases-and-biosql`.
- Protein structure prediction, docking, de novo design, force fields, or molecular dynamics setup: outside this Biopython repo skill except for simple coordinate parsing/selection utilities.

## Operating references

- Start with [`references/structure-workflows.md`](references/structure-workflows.md) for parser choice, SMCRA traversal, writing/selecting, polypeptides, contacts, geometry, superposition, downloads, and optional tools.
- Use [`references/structure-api-reference.md`](references/structure-api-reference.md) for verified signatures, object relationships, entity levels, residue/atom ID conventions, and format limits.
- Use [`references/troubleshooting.md`](references/troubleshooting.md) for parser warnings/errors, malformed coordinates, PQR charge/radius issues, mmCIF/PDB ID mismatches, BinaryCIF optional dependencies, writer limits, `NeighborSearch`, `Superimposer`, `PDBList`, and external-tool failures.
- Run [`scripts/pdb_structure_smoke.py`](scripts/pdb_structure_smoke.py) for a safe offline sanity check of `PDBParser`, SMCRA traversal, atom geometry, `NeighborSearch`, and `PDBIO` round-tripping on an embedded tiny PDB fixture.

## Guardrails

- Prefer mmCIF/PDBx or BinaryCIF for modern, large, or metadata-heavy structure work; legacy PDB has chain, atom-serial, residue-number, and header limitations.
- Treat `PERMISSIVE=True` as data-loss-tolerant parsing: warnings may mean atoms or residues were omitted. Use strict parsing when data integrity matters.
- Always decide how to handle disordered atoms/residues before measuring distances, contacts, or superpositions.
- Match superposition atom lists by biological identity and order; `Superimposer` minimizes RMSD for equal-length lists and mutates the moving atoms when `apply` is called.
- Do not require downloads, external executables, original repository examples, or repository test data for normal runtime recipes in this sub-skill.
