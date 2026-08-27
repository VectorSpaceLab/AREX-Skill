---
name: pysam
description: "Routes agents using pysam for SAM/BAM/CRAM, VCF/BCF, tabix-indexed
  tables, FASTA/FASTQ, bundled samtools/bcftools wrappers, and installation or
  build troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# pysam

Use this repo skill when a task involves the Python package `pysam`: reading or writing high-throughput sequencing files, manipulating alignments or variants, indexing genomic interval files, fetching FASTA/FASTQ records, calling bundled samtools/bcftools commands from Python, or diagnosing install/build/import failures.

## Start Here

- Read `references/package-overview.md` for the package scope, install options, verified version facts, and route summary.
- Read `references/troubleshooting.md` for cross-cutting setup, coordinate, index, and routing failures.
- Read `references/repo-provenance.md` before deciding whether this skill is current for a specific checkout.
- Run `scripts/check_pysam_environment.py` when you need a source-free import and smoke diagnostic for the active Python environment.

## Install and Minimal Check

Prefer Bioconda when users want the most reliable install path:

```bash
conda config --add channels bioconda
conda config --add channels conda-forge
conda config --set channel_priority strict
conda install pysam
```

PyPI wheels are usually enough for ordinary Python use:

```bash
python -m pip install pysam
python -c 'import pysam; print(pysam.__version__)'
```

For a deeper package check, run:

```bash
python scripts/check_pysam_environment.py
```

## Route by Task

| User task | Read |
| --- | --- |
| Open, read, write, index, fetch, count, or pile up SAM/BAM/CRAM data; edit `AlignedSegment` flags, CIGAR, tags, sequence, or qualities | `sub-skills/alignment-io/SKILL.md` |
| Read, write, filter, subset, or construct VCF/BCF files with `VariantFile`, `VariantHeader`, `VariantRecord`, INFO/FORMAT/sample fields, or indexed fetches | `sub-skills/variant-io/SKILL.md` |
| Compress/index/fetch tabix tables; parse BED/GTF/GFF/VCF rows; use `FastaFile`, `FastxFile`, or FASTQ quality arrays | `sub-skills/tabix-fasta/SKILL.md` |
| Translate shell `samtools`/`bcftools` commands into Python calls; handle `catch_stdout`, `save_stdout`, `usage()`, `get_messages()`, or `SamtoolsError` | `sub-skills/command-wrappers/SKILL.md` |
| Install pysam, build from source, link external `htslib`, compile Cython extensions, migrate legacy `csamtools` names, or inspect build helpers | `sub-skills/troubleshooting-build/SKILL.md` |

## Common Routing Decisions

- If a user asks about BAM rows, reads, CIGAR strings, pileup columns, or unmapped reads, start with `alignment-io` even when the final solution also calls `samtools`.
- If a user asks about VCF header metadata, sample genotypes, INFO/FORMAT types, or record writing, start with `variant-io` even when the file is tabix-indexed.
- If a user asks about generic compressed BED/GTF/GFF tables or FASTA/FASTQ sequence access, start with `tabix-fasta`.
- If a user gives a shell command such as `samtools sort`, `samtools faidx`, `bcftools view`, or `bcftools query` and wants Python code, start with `command-wrappers`.
- If `import pysam` or installation fails before any data workflow can run, start with `troubleshooting-build`.

## Coordinate and Index Defaults

- pysam Python integer intervals are usually 0-based and half-open.
- Region strings such as `chr1:101-200` follow samtools-style 1-based inclusive conventions.
- `AlignmentFile.fetch()` and `VariantFile.fetch()` require an appropriate index for random access; use sequential modes only when the workflow supports them.
- Tabix random access requires BGZF compression and a `.tbi` or `.csi` index.
- FASTA random access uses `.fai` indexes; FASTQ streaming uses `FastxFile` and does not require random-access indexing.

## Bundled Helpers

- `scripts/check_pysam_environment.py` verifies imports, versions, command wrapper presence, and tiny source-free operations across the major routes.
- `sub-skills/alignment-io/scripts/alignment_smoke.py` creates a tiny BAM and exercises alignment reads, indexing, coverage, pileup, and quality helpers.
- `sub-skills/variant-io/scripts/variant_smoke.py` writes and reads a tiny VCF with INFO/FORMAT/sample fields.
- `sub-skills/tabix-fasta/scripts/tabix_fasta_smoke.py` creates tiny tabix, FASTA, and FASTQ fixtures.
- `sub-skills/command-wrappers/scripts/command_wrapper_smoke.py` checks dispatcher usage, stdout handling, and safe samtools command behavior.
- `sub-skills/troubleshooting-build/scripts/inspect_build_config.py` prints redacted build/import diagnostics.

## What This Skill Does Not Cover

- It does not teach general genomics biology or variant interpretation beyond file/API mechanics.
- It does not require the original pysam source checkout for runtime use.
- It does not cover maintainer release engineering beyond install/build and extension-development troubleshooting.
