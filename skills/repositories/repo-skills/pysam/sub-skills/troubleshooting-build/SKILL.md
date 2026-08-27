---
name: troubleshooting-build
description: "Guides agents troubleshooting pysam installation, source builds,
  imports, Cython extension linking, htslib selection, typing stubs, deprecated
  names, and platform build failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# troubleshooting-build

Use this sub-skill when a task involves installing or importing `pysam`, diagnosing wheel/source build failures, choosing builtin versus external `htslib`, compiling Cython code against pysam, resolving runtime linker errors, migrating old extension-module names, or understanding typing/deprecation caveats.

## Read first

- `references/install-build-reference.md` for Bioconda, PyPI wheels, source builds, builtin/external `htslib`, environment variables, profiling, and platform caveats.
- `references/extension-development.md` for `get_include()`, `get_libraries()`, `get_defines()`, Cython `cimport` patterns, `lib*` extension module names, and type stub expectations.
- `references/troubleshooting.md` for common failure signatures and targeted fixes.
- `scripts/inspect_build_config.py` for a safe JSON probe of a local `pysam` install. It redacts local paths by default; use `--show-paths` only when the user explicitly wants machine-specific diagnostics.

## Scope

This sub-skill owns installation, import, build, link, and extension-development issues for `pysam` 0.24.x and its wrapped `htslib`, `samtools`, and `bcftools` versions.

Use sibling sub-skills instead for data workflows after `pysam` imports successfully:

- `../alignment-io/SKILL.md` for `AlignmentFile`, `AlignedSegment`, SAM/BAM/CRAM, pileup, indexes, and coordinate behavior.
- `../variant-io/SKILL.md` for `VariantFile`, headers, VCF/BCF records, sample subsetting, and record translation.
- `../tabix-fasta/SKILL.md` for tabix-indexed tables, `TabixFile`, `FastaFile`, BGZF/index helpers, and FASTA access.
- `../command-wrappers/SKILL.md` for `pysam.samtools`, `pysam.bcftools`, top-level command aliases, and `SamtoolsError` handling.

## Defaults that prevent common mistakes

- Prefer Bioconda when the user needs the least fragile install path or wants non-Python dependencies resolved automatically.
- Prefer normal `pip install pysam` only when a compatible wheel exists or the environment has a working compiler toolchain and htslib build dependencies.
- For repository installs, ensure Cython is installed first; PyPI source distributions can include generated C files, but repository checkouts require Cython.
- Treat `HTSLIB_LIBRARY_DIR` and `HTSLIB_INCLUDE_DIR` as a matched pair for external `htslib`, and verify runtime linking with the dynamic loader path if `libhts` cannot be found.
- Use `pysam.get_include()`, `pysam.get_libraries()`, and `pysam.get_defines()` when compiling Cython extensions that link against pysam internals.
- Migrate old direct extension imports such as `pysam.csamtools` to `pysam.libcsamtools`; direct extension modules use the `lib` prefix in modern pysam.
