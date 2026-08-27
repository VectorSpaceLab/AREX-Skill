---
name: variant-io
description: "Guides agents using pysam VariantFile, VariantHeader, and
  VariantRecord for VCF/BCF reading, writing, sample subsetting, metadata edits,
  and coordinate/header troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# variant-io

Use this sub-skill when a task involves VCF/BCF variant data through `pysam.VariantFile`, `VariantHeader`, `VariantRecord`, INFO/FORMAT/sample fields, record creation, record translation, or random access with `fetch`.

## Read First

- `references/api-reference.md` for the object model, signatures, modes, and mapping-like containers.
- `references/workflows.md` for common read/filter/write, header-building, record-editing, sample-subsetting, and translation patterns.
- `references/troubleshooting.md` for header declarations, INFO/FORMAT mismatches, genotype/allele errors, indexes, coordinates, and VCF/BCF mode choices.
- `scripts/variant_smoke.py` for a source-free VCF round-trip smoke helper that prints JSON assertions.

## Scope

This sub-skill owns VCF/BCF I/O and variant object manipulation: `VariantFile`, `VariantHeader`, `VariantHeaderRecord`, `VariantRecord`, `VariantRecordSample`, header metadata mappings, `fetch`, `write`, `subset_samples`, `new_record`, and `translate`.

Use sibling sub-skills instead for tabix row parsers and BED/GTF/GFF parsing, bcftools command wrappers, or SAM/BAM/CRAM alignment and pileup workflows.
