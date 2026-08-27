---
name: file-io-and-format-conversion
description: "Use Biopython SeqIO and AlignIO for offline sequence/alignment
  file parsing, writing, indexing, conversion, FASTA/FASTQ iterators, and
  compressed/BGZF tradeoffs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# File I/O and Format Conversion

Use this sub-skill when the task is to read, write, index, or convert biological sequence or multiple-alignment files with Biopython's `Bio.SeqIO`, `Bio.AlignIO`, low-level FASTA/FASTQ iterators, or BGZF-aware random access.

## Route here for

- Choosing `SeqIO.parse`, `SeqIO.read`, `SeqIO.write`, `SeqIO.convert`, `SeqIO.to_dict`, `SeqIO.index`, or `SeqIO.index_db`.
- Choosing `AlignIO.parse`, `AlignIO.read`, `AlignIO.write`, or `AlignIO.convert` for multiple sequence alignment files.
- FASTA, FASTQ, QUAL, GenBank/GB, EMBL, Swiss-Prot/UniProt XML, tabular sequence files, PHYLIP, Clustal, Stockholm, NEXUS, MAF, and related file formats.
- Memory tradeoffs for streaming, materializing records, in-memory dictionaries, on-disk indexes, and raw record extraction.
- Low-level FASTA/FASTQ iteration when `SeqRecord` construction is unnecessary.
- Compression decisions: plain text handles, standard gzip for streaming, and BGZF for indexed random access.

## Route elsewhere

- Sequence object semantics, annotations, features, coordinate behavior, translation, reverse complementing, and per-letter annotations: use `sequence-objects-and-features`.
- Search-result object models and BLAST/HMMER/PSL/SearchIO semantics: use `alignment-search-and-phylogeny`.
- Online downloads, Entrez/KEGG/ExPASy/UniProt service etiquette, and BioSQL databases: use `web-databases-and-biosql`.
- Structural file parsing for PDB/mmCIF objects: use `structural-bioinformatics` unless the task is only sequence extraction through a `SeqIO` format.

## Operating references

- Start with [`references/file-io-workflows.md`](references/file-io-workflows.md) for task patterns, memory choices, indexing, conversion, and compression.
- Use [`references/format-reference.md`](references/format-reference.md) for verified format names and read/write/index support.
- Use [`references/troubleshooting.md`](references/troubleshooting.md) for common parser/writer/index errors and recovery steps.
- Run [`scripts/seqio_alignio_smoke.py`](scripts/seqio_alignio_smoke.py) for a safe offline sanity check of SeqIO, AlignIO, indexing, BGZF, conversion, and low-level iterators.

## Guardrails

- Always pass explicit lowercase format names; Biopython does not infer the format from the filename extension.
- Prefer streaming (`parse`) for large files; only materialize into `list` or `to_dict` when the data size and memory budget are known to be small enough.
- Treat conversion as lossy unless the target format can store the same annotations, quality scores, alignments, and molecule type.
- Do not require network, external aligners, original examples, or repository test data for runtime recipes in this sub-skill.
