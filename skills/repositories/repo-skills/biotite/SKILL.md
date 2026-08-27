---
name: biotite
description: "Use Biotite for computational molecular biology workflows:
  sequence analysis, structure analysis, biological database access, file-format
  conversion, application wrappers, and optional molecular interfaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Biotite

Use this repo skill when a task involves Biotite, `biotite.sequence`, `biotite.structure`, biological sequence/structure files, RCSB/Entrez/UniProt/PubChem/AlphaFold DB access, external bioinformatics application wrappers, or optional PyMOL/RDKit/OpenMM/Matplotlib integration.

Biotite is a Python package for computational molecular biology. It represents sequences and molecular structures with NumPy-backed objects and exposes APIs for file parsing, local analysis, database queries, visualization, and external tool orchestration.

## Start Here

1. Confirm Biotite is installed in the active Python environment with the safe root check below.
2. Route to the focused sub-skill that owns the task; avoid using source-repo examples, tests, or docs at runtime.
3. Use sibling cross-links when a workflow spans fetch → parse → analyze → visualize.
4. Treat database calls, external executables, GUI rendering, and optional interfaces as opt-in side effects.
5. Read [references/troubleshooting.md](references/troubleshooting.md) for install/import, build, optional dependency, and routing failures.

## Install And Import Check

For normal package use, prefer wheel installs:

```bash
python -m pip install biotite
python - <<'PY'
import biotite
import biotite.sequence as seq
import biotite.structure as struc
print(biotite.__version__)
print(seq.ProteinSequence("ACDE"))
print(struc.AtomArray(1).array_length())
PY
```

For source checkouts, Biotite may need Python 3.12+, NumPy, Cython/build tooling, Rust build support, and compiled extension wheels. Prefer wheel installs for use-only tasks and source installs only for development or unreleased APIs.

Run the bundled diagnostic when routing a user problem:

```bash
python scripts/check_biotite_environment.py
```

It performs import/version checks and can also call the sub-skill optional diagnostics without contacting networks or running analyses.

## Sub-skill Routes

- [sequence-analysis](sub-skills/sequence-analysis/SKILL.md): sequence objects, alphabets, annotations, translation/codons, pairwise and multiple alignment, substitution matrices, k-mer searches, profiles, phylogenetic trees, and sequence graphics decisions.
- [structure-analysis](sub-skills/structure-analysis/SKILL.md): `Atom`, `AtomArray`, `AtomArrayStack`, filters, bonds, geometry, superposition, RMSD/RMSF, SASA, hydrogen bonds, base pairs, pseudoknots, periodic boxes, secondary structure, and trajectory analysis.
- [file-io-formats](sub-skills/file-io-formats/SKILL.md): FASTA, FASTQ, GenBank, GFF, Clustal, PDB, PDBx/mmCIF, BinaryCIF, GRO, PDBQT, MOL/SDF, trajectory IO, and conversions into Biotite objects.
- [database-application](sub-skills/database-application/SKILL.md): RCSB, AlphaFold DB, Entrez, UniProt, PubChem, BLAST, Clustal Omega, MAFFT, MUSCLE, DSSP, AutoDock Vina, SRA, Tantan, and ViennaRNA wrappers.
- [interfaces-visualization](sub-skills/interfaces-visualization/SKILL.md): PyMOL, RDKit, OpenMM, Matplotlib-backed graphics, sequence/structure visualization, and optional dependency diagnostics.

## Common Workflow Routing

- Remote sequence alignment: use `database-application` for Entrez/UniProt/RCSB retrieval, `file-io-formats` for FASTA/GenBank parsing, then `sequence-analysis` for alignment/profile/phylogeny.
- Protein structure measurement: use `database-application` for RCSB/AFDB fetch if needed, `file-io-formats` for PDBx/BinaryCIF parsing, then `structure-analysis` for filtering, bonds, geometry, SASA, contacts, or superposition.
- Molecular interoperability: use `file-io-formats` for MOL/SDF/PDBx loading, `structure-analysis` to prepare coordinates/bonds, then `interfaces-visualization` for RDKit/OpenMM/PyMOL/plotting.
- External bioinformatics tools: use `database-application` first to check binaries and wrapper lifecycle; route outputs to `file-io-formats`, `sequence-analysis`, or `structure-analysis`.

## Shared References And Scripts

- Repository snapshot and refresh baseline: [references/repo-provenance.md](references/repo-provenance.md).
- Router import metadata: [references/repo-routing-metadata.json](references/repo-routing-metadata.json).
- Cross-cutting failure recovery: [references/troubleshooting.md](references/troubleshooting.md).
- Root environment diagnostic: [scripts/check_biotite_environment.py](scripts/check_biotite_environment.py).
