---
name: variant-datasets
description: "Use Hail VariantDataset sparse sequencing workflows: read, filter,
  QC, combine GVCFs, convert VDS representations, and reason about local alleles
  and reference blocks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Hail Variant Datasets

Use this sub-skill when a task mentions `hail.vds`, `VariantDataset`, VDS, sparse sequencing data, GVCF combining, local allele fields (`LGT`, `LA`, `LAD`, `LPL`, `LPGT`), reference blocks (`END` or `LEN`), `to_dense_mt`, `to_merged_sparse_mt`, `interval_coverage`, or VDS-native `sample_qc`.

## Route First

- Use `references/vds-workflows.md` to choose between component matrices, dense conversion, merged sparse conversion, sample QC, interval coverage, filtering, split-multi, and GVCF combiner recipes.
- Use `references/api-reference.md` for concise `hail.vds` signatures, parameter notes, component field semantics, and combiner API details.
- Use `references/troubleshooting.md` for local allele mistakes, reference block `END`/`LEN` issues, component mismatch, combiner resume/save failures, interval/reference mismatch, and dense conversion surprises.
- Start new runnable examples from `scripts/vds_recipe_template.py`; it is a self-contained helper that defaults to dry-run/template output and does not depend on repository fixtures.

## Scope Boundaries

- Stay here for `hl.vds.VariantDataset`, `hl.vds.read_vds`, `hl.vds.filter_samples`, `hl.vds.filter_variants`, `hl.vds.filter_intervals`, `hl.vds.filter_chromosomes`, `hl.vds.sample_qc`, `hl.vds.split_multi`, `hl.vds.interval_coverage`, `hl.vds.to_dense_mt`, `hl.vds.to_merged_sparse_mt`, `hl.vds.new_combiner`, and `hl.vds.load_combiner`.
- Route ordinary dense `MatrixTable` GWAS, VCF/PLINK/BGEN analysis, row/column/entry transformations, and dense QC after VDS conversion to `../genomics-analysis/SKILL.md`.
- Route backend sizing, `hl.init`, Spark/local/Batch backend selection, cloud filesystem credentials, requester-pays, and cluster planning to `../setup-and-backends/SKILL.md`.
- Route `hailctl`, Hail Batch DAG orchestration, Batch Service jobs, and CLI monitoring to `../batch-and-cli/SKILL.md` unless the task is specifically about VDS API calls.

## Default Mental Model

A `hl.vds.VariantDataset` is a wrapper around two sparse component `MatrixTable`s, not a single `MatrixTable`:

- `vds.reference_data` is keyed by `locus`, has the sample column key, and stores reference blocks. Each entry covers `locus.position` through inclusive `END`, or equivalent `LEN`; calls are implicitly homozygous reference.
- `vds.variant_data` is keyed by `locus, alleles`, has the same sample columns, and stores sparse non-reference or variant rows. Entries commonly use local allele fields such as `LA`, `LGT`, `LAD`, `LPL`, and `LPGT`.

Choose representation deliberately: use components for sparse variant or coverage work, use `hl.vds.sample_qc` and `hl.vds.interval_coverage` before considering densification, use `hl.vds.to_dense_mt(vds)` only for downstream dense-only methods, and use `hl.vds.to_merged_sparse_mt(vds)` when a single sparse `MatrixTable` is needed.
