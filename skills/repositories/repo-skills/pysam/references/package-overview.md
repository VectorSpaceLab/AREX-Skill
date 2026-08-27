# pysam Package Overview

## Purpose

`pysam` is a Python/Cython interface for high-throughput sequencing file formats and command-line functionality from htslib, samtools, bcftools, and tabix. Use this skill for practical agent workflows around file I/O, indexing, interval fetches, command wrappers, and build/import troubleshooting.

## Verified Public Facts

- Distribution/import name: `pysam`.
- Verified package version in the source snapshot: `0.24.0`.
- Python requirement from package metadata: `>=3.8`.
- Source release notes report bundled htslib, samtools, and bcftools version family `1.23.1`.
- Installed-package inspection confirmed imports for `pysam`, key compiled extension modules, `pysam.samtools`, and `pysam.bcftools`.
- Many C-extension classes do not expose reliable `inspect.signature()` values; use docstrings, type stubs, and smoke scripts for signature and behavior checks.

## Main API Families

| API family | Primary objects | Owning sub-skill |
| --- | --- | --- |
| SAM/BAM/CRAM | `AlignmentFile`, `AlignmentHeader`, `AlignedSegment`, `PileupColumn`, `PileupRead`, `IndexedReads` | `sub-skills/alignment-io/SKILL.md` |
| VCF/BCF | `VariantFile`, `VariantHeader`, `VariantRecord`, header/record mapping views | `sub-skills/variant-io/SKILL.md` |
| Tabix tables | `TabixFile`, `tabix_compress`, `tabix_index`, `asTuple`, `asBed`, `asGTF`, `asGFF3`, `asVCF` | `sub-skills/tabix-fasta/SKILL.md` |
| FASTA/FASTQ | `FastaFile`, `FastxFile`, `FastxRecord`, `FastqProxy` | `sub-skills/tabix-fasta/SKILL.md` |
| Command wrappers | `pysam.samtools`, `pysam.bcftools`, top-level samtools aliases, `SamtoolsError` | `sub-skills/command-wrappers/SKILL.md` |
| Build/extension support | `get_include()`, `get_libraries()`, `get_defines()`, `pysam.lib*` Cython modules | `sub-skills/troubleshooting-build/SKILL.md` |

## Installation Guidance

Use Bioconda when users want the lowest-friction install path, especially on platforms where compiler settings and non-Python libraries are difficult:

```bash
conda config --add channels bioconda
conda config --add channels conda-forge
conda config --set channel_priority strict
conda install pysam
```

Use PyPI for ordinary wheel installs:

```bash
python -m pip install pysam
python -c 'import pysam; print(pysam.__version__)'
```

For source builds, repository checkouts require Cython and a working C build toolchain. See `sub-skills/troubleshooting-build/references/install-build-reference.md` before suggesting source builds, external `htslib`, or profiling builds.

## Agent Workflow Pattern

1. Classify the user's task by file type or API surface.
2. Route to the nearest sub-skill rather than searching all references.
3. Use the sub-skill `SKILL.md` as the router and its references for details.
4. Run a bundled smoke helper when the user needs environment confirmation.
5. Keep generated commands and examples independent of the original source checkout.

## Common Cross-Skill Concepts

- Integer coordinates in pysam APIs are generally 0-based, half-open.
- Region strings follow samtools-style syntax and are often 1-based inclusive.
- Random access requires an index: BAM/CRAM/VCF/BCF/tabix/FASTA each has different index files and creation paths.
- File handles, iterators, and proxy objects are C-backed; convert data to plain Python values before storing it beyond iterator lifetimes when needed.
- Command wrappers behave like Python functions but still follow samtools/bcftools command semantics and failure modes.
