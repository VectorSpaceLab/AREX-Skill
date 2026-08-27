---
name: file-io-formats
description: "Use Biotite to read, write, validate, and convert local sequence,
  structure, molecule, and trajectory file formats into Sequence, Annotation,
  AtomArray, and AtomArrayStack objects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# File IO Formats

Use this sub-skill when a task is centered on `biotite.sequence.io`, `biotite.structure.io`, local parser classes, file round trips, or converting stored data into Biotite sequence, annotation, structure, molecule, or trajectory objects.

## Route Here For

- FASTA, FASTQ, GenBank/GenPept, GFF3, Clustal, A3M, and generic sequence file loading/saving.
- PDB, PDBx/mmCIF, BinaryCIF, GRO, PDBQT, MOL, SDF, and generic structure file loading/saving.
- Choosing between `PDBFile`, `CIFFile`, `BinaryCIFFile`, `MOLFile`, `SDFile`, `GROFile`, and trajectory file classes.
- Using PDBx hierarchy objects: file, block, category, column, data, masks, BinaryCIF encodings, and `compress()`.
- Converting files into `Sequence`, `Annotation`, `Alignment`, `AtomArray`, `AtomArrayStack`, `BondList`, and trajectory coordinate arrays.
- Debugging IO-specific failures such as text/binary handles, malformed records, missing trajectory templates, model/altloc choices, and unsupported fields.

## Use Another Biotite Sub-skill For

- Sequence construction, alphabets, annotation analysis, alignments, profiles, and phylogeny after parsing: [../sequence-analysis/SKILL.md](../sequence-analysis/SKILL.md).
- AtomArray filtering, geometry, bonds, superposition, secondary structure, contacts, and trajectory analysis after loading: [../structure-analysis/SKILL.md](../structure-analysis/SKILL.md).
- RCSB, Entrez, UniProt, PubChem, AlphaFold DB, BLAST, MSA wrappers, DSSP, SRA, Vina, and other network/external application planning: [../database-application/SKILL.md](../database-application/SKILL.md).
- PyMOL, RDKit, OpenMM, plotting, display, and visualization-oriented conversion: [../interfaces-visualization/SKILL.md](../interfaces-visualization/SKILL.md).

## Start With

1. Identify whether the input is sequence text, sequence annotations, an alignment, a coordinate structure, a small molecule, or a coordinate-only trajectory.
2. Prefer generic helpers (`load_sequence()`, `load_sequences()`, `load_structure()`) for simple extension-driven tasks; use format-specific file classes when options, metadata, annotations, bonds, models, or round-trip fidelity matter.
3. Choose text vs binary handles correctly: FASTA/FASTQ/GenBank/GFF/Clustal/PDB/CIF/MOL/SDF/GRO/PDBQT are text, BinaryCIF is binary, and trajectories usually require filesystem paths.
4. For structures, decide `model`, `altloc`, `extra_fields`, `include_bonds`, and author-vs-label fields before downstream analysis.
5. For trajectories, load a topology/template `AtomArray` or `AtomArrayStack` first; trajectory files normally store coordinates, boxes, and times, not atom annotations.

## References

- API map and class chooser: [references/api-reference.md](references/api-reference.md).
- Format behavior and caveats: [references/data-formats.md](references/data-formats.md).
- Common local workflows: [references/workflows.md](references/workflows.md).
- Failure recovery: [references/troubleshooting.md](references/troubleshooting.md).
- FASTA helper: [scripts/roundtrip_sequence_io.py](scripts/roundtrip_sequence_io.py).
- PDB/PDBx helper: [scripts/tiny_structure_io_smoke.py](scripts/tiny_structure_io_smoke.py).

## Quick Checks

From the Biotite skill root, run the no-network helpers when you need a local sanity check:

```bash
python sub-skills/file-io-formats/scripts/roundtrip_sequence_io.py
python sub-skills/file-io-formats/scripts/tiny_structure_io_smoke.py --mode pdb
```

Use `--help` on either helper for options. The structure helper intentionally focuses on tiny PDB/PDBx round trips; trajectory guidance is covered in the references because trajectory files are coordinate-only and require an external topology/template contract.
