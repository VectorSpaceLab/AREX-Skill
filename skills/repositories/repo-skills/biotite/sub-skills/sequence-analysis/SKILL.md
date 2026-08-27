---
name: sequence-analysis
description: "Use Biotite for sequence construction, alphabets, annotations,
  translation, pairwise and multiple alignment, k-mer searches, profiles,
  phylogenetic trees, and sequence-centered graphics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Sequence Analysis

Use this sub-skill when a task is centered on `biotite.sequence`, `biotite.sequence.align`, `biotite.sequence.phylo`, or sequence-centered `biotite.sequence.graphics` workflows.

## Route Here For

- Constructing `NucleotideSequence`, `ProteinSequence`, `GeneralSequence`, custom `Alphabet`/`LetterAlphabet`, and `PositionalSequence` objects.
- Validating symbols, choosing ambiguous vs unambiguous nucleotide alphabets, slicing/editing sequences, concatenating sequences, and reading `.code`/`.symbols` safely.
- Translating nucleotide sequences, finding ORFs, using `CodonTable`, reverse complements, and protein letter conversions.
- Building `Feature`, `Location`, `Annotation`, and `AnnotatedSequence` objects and slicing annotations or extracting feature sequences.
- Pairwise alignment with `align.align_optimal()`, `align.align_ungapped()`, `align.align_banded()`, local/gapped/ungapped seed extension, and alignment scoring/identity.
- Multiple sequence alignment with `align.align_multiple()`, guide trees, k-mer based prefiltering, profiles, consensus sequences, and position-specific scoring matrices.
- Creating or parsing `phylo.Tree`/`TreeNode` objects, UPGMA/neighbor-joining trees, Newick strings, and sequence dendrogram plots.
- Deciding when sequence graphics such as alignment plots, sequence logos, feature maps, plasmid maps, and dendrograms need optional `matplotlib`.

## Use Another Biotite Sub-skill For

- FASTA, FASTQ, GenBank, GFF, Clustal, parser classes, and format round trips: `../file-io-formats/SKILL.md`.
- Entrez, UniProt, RCSB, PubChem, AlphaFold DB, BLAST, MSA application wrappers, and network/external binary planning: `../database-application/SKILL.md`.
- PyMOL, RDKit, OpenMM, display backends, and visualization/export tasks where sequence data is not the main object: `../interfaces-visualization/SKILL.md`.

## Start With

1. Choose the concrete sequence type and alphabet before building downstream objects.
2. For alignments, choose the substitution matrix, gap model, `local` vs global semantics, and whether `max_number` should cap equally optimal traces.
3. For annotations, keep track of 1-based biological feature positions vs Python sequence slicing positions.
4. For profiles/MSAs/trees, ensure every input sequence is already comparable and that alignment/profile shapes match.

## References

- API map: `references/api-reference.md`.
- Task recipes: `references/workflows.md`.
- Failure recovery: `references/troubleshooting.md`.
- Safe local check: `scripts/sequence_alignment_smoke.py`.

## Quick Smoke Check

Run this helper when you need to verify the local Biotite sequence surface without network or source checkout access:

```bash
python sub-skills/sequence-analysis/scripts/sequence_alignment_smoke.py --mode all
```

The helper uses tiny literal sequences, exits nonzero on failed assertions, and can run only selected checks with `--mode core`, `--mode alignment`, or `--mode profile`.
