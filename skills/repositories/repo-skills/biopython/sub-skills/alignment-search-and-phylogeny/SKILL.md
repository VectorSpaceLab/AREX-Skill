---
name: alignment-search-and-phylogeny
description: "Operate Biopython alignment, search result, BLAST, and phylogeny
  workflows with offline-safe routing guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Alignment, search, BLAST, and phylogeny router

Use this sub-skill when the task is primarily about Biopython alignment/search/tree APIs:

- score or recover pairwise sequence alignments with `Bio.Align.PairwiseAligner`;
- load or apply substitution matrices such as `BLOSUM62`;
- inspect `Bio.Align.Alignment` objects or route multiple-alignment file handling through `Bio.AlignIO`;
- parse, index, filter, or write sequence-search output with `Bio.SearchIO`;
- parse or write BLAST XML with `Bio.Blast`, or plan a carefully approved `Bio.Blast.qblast` call;
- read, traverse, query, reroot, prune, ladderize, or write phylogenetic trees with `Bio.Phylo`.

Do not use this sub-skill for general sequence/FASTQ/GenBank conversion, Entrez or other database retrieval, or structural superposition. Route those tasks to the package skill areas for file I/O, web/database workflows, or structural bioinformatics.

## First-pass routing

1. **Pairwise alignment or substitution scoring**: load `references/alignment-search-workflows.md` and choose `PairwiseAligner`; use legacy `Bio.pairwise2` only for migrating old code.
2. **Multiple alignment file input/output**: use `Bio.AlignIO` guidance in `references/alignment-search-workflows.md`; route broad conversion/indexing questions to the file-I/O sub-skill.
3. **Search program results**: load `references/searchio-blast-reference.md`; prefer `SearchIO` for BLAST tabular/XML, BLAT PSL, HMMER, FASTA m10, Infernal, Exonerate, HH-suite, and InterProScan result models.
4. **BLAST XML records or qblast**: load `references/searchio-blast-reference.md`; keep parsing offline unless the user explicitly authorizes network use and supplies required service etiquette metadata.
5. **Trees and phylogenies**: load `references/phylo-reference.md`; copy trees before destructive modifications if the original topology must be preserved.
6. **Failures, unexpected scores, parser errors, or optional tools**: load `references/troubleshooting.md`.

## Offline check

Run `scripts/alignment_phylo_smoke.py` in an environment with Biopython installed to verify core offline coverage for `PairwiseAligner`, substitution matrices, `SearchIO` model availability, and `Phylo` Newick parsing/traversal/modification. The script does not require network access, external executables, databases, or original repository files.
