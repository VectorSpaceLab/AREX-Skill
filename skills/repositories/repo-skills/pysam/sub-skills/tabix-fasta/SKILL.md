---
name: tabix-fasta
description: "Guides agents using pysam for tabix compression, tabix indexing,
  indexed table fetches, BED/GTF/GFF/VCF row parser proxies, BGZF iteration,
  FASTA random access, FASTQ streaming, and parser or encoding data-format
  issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# tabix-fasta

Use this sub-skill when a task involves `pysam.TabixFile`, `tabix_compress`, `tabix_index`, `tabix_iterator`, `asTuple`, `asBed`, `asGTF`, `asGFF3`, `asVCF`, `FastaFile`, legacy `Fastafile`, `FastxFile`, `FastxRecord`, or FASTQ quality streaming.

## Read First

- `references/api-reference.md` for constructor signatures, fetch/index APIs, parser proxy contracts, and FASTA/FASTQ entry points.
- `references/data-formats.md` for tabix coordinate columns, BED/GTF/GFF/VCF parser fields, BGZF/index files, encodings, and FASTA/FASTQ assumptions.
- `references/workflows.md` for compression/index/fetch recipes, parser usage, BGZF iteration, FASTA random access, and FASTQ streaming patterns.
- `references/troubleshooting.md` for unsorted input, stale indexes, wrong presets or columns, coordinate confusion, plain gzip, parser/encoding failures, overwrite protection, and missing FASTA indexes.
- `scripts/tabix_fasta_smoke.py` for a source-free smoke helper that creates tiny BED, FASTA, and FASTQ fixtures and prints JSON assertions.

## Scope

This sub-skill owns tabix-indexed tabular files and sequence-file helpers: compressing and indexing tabular genomic rows, random-access `TabixFile.fetch()`, row parser proxies, sequential `tabix_iterator()`, `FastaFile.fetch()`, and `FastxFile` iteration.

Use sibling sub-skills instead for object-oriented `VariantFile` VCF/BCF workflows, SAM/BAM/CRAM alignment I/O, or invoking samtools/bcftools dispatcher commands.

## Defaults that prevent common mistakes

- Use BGZF output from `pysam.tabix_compress()` or `pysam.tabix_index()`; plain `gzip` files are not interchangeable with tabix-indexed BGZF files.
- Keep tabix input sorted by contig and start coordinate before indexing; pysam does not sort rows for you.
- Prefer `preset="bed"`, `"gff"`, `"sam"`, or `"vcf"` when the file matches a standard format; otherwise pass explicit 0-based column numbers.
- Treat integer `fetch(reference, start, end)` arguments as 0-based, half-open intervals; region strings such as `"chr1:101-200"` use samtools-style coordinates.
- For BED, pass `zerobased=True` when using explicit columns, or use `preset="bed"`; GFF/GTF/VCF/SAM presets handle their own conventional coordinates.
- Use `encoding="utf-8"` on `TabixFile` and parser objects when rows can contain non-ASCII text.
- Prefer `with pysam.TabixFile(...)`, `with pysam.FastaFile(...)`, and `with pysam.FastxFile(...)` so C-backed handles close promptly.
