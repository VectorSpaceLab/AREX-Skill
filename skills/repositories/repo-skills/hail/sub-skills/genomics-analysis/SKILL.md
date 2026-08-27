---
name: genomics-analysis
description: "Use dense Hail MatrixTable workflows for VCF, PLINK, BGEN,
  variant/sample QC, multiallelic splitting, PCA, LD pruning, association tests,
  VEP/Nirvana-style annotation, and reference genome or locus/call handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Hail Genomics Analysis

Use this sub-skill when the task is about dense genotype data represented as a Hail `MatrixTable`: importing VCF, PLINK, or BGEN; reasoning about row, column, entry, and global axes; annotating samples or variants; filtering calls; running QC; splitting multiallelics; running PCA, LD pruning, relatedness, or association tests; applying VEP/Nirvana-style annotation; or diagnosing reference genome and contig issues.

## Start Here

- Read `references/matrixtable-workflows.md` for import-to-native-cache, annotation, filtering, QC, split, PCA, association, VEP, and export recipes.
- Read `references/genomic-methods.md` for task-to-method selection across QC, PCA, association, relatedness, VEP/Nirvana boundaries, reference genomes, `Locus`, `Call`, and `Pedigree`.
- Read `references/data-formats.md` before choosing import/export options or interpreting `locus`, `alleles`, `s`, `GT`, `DP`, `GQ`, `PL`, `info`, dosage, and phenotype fields.
- Read `references/troubleshooting.md` when imports fail, references mismatch, `split_multi_hts` produces surprising INFO fields, VEP/Nirvana cannot run, association covariates fail, or `collect`/`entries` is too expensive.
- Use `scripts/matrixtable_recipe_template.py --print-template` to generate a safe, editable dense MatrixTable recipe skeleton.

## Route Elsewhere

- Use `../variant-datasets/SKILL.md` for sparse GVCF, VDS, combiner, `hl.vds`, local allele fields, or VDS-to-dense conversion work.
- Use `../tables-and-expressions/SKILL.md` for generic `Table` pipelines, one-dimensional annotations, joins, aggregations, or expression-index errors that do not depend on MatrixTable axes.
- Use `../setup-and-backends/SKILL.md` for `hl.init`, Spark/local/Batch backend choice, package installation, Java/JAR/runtime problems, cloud credentials, logs, and storage configuration.
- Use `../batch-and-cli/SKILL.md` for `hailctl`, `hailtop.batch`, job DAGs, cloud Batch execution, Dataproc/HDInsight command families, or CLI automation.

## Core Mental Model

A dense `MatrixTable` has four axes:

- `row`: variant/site fields, usually keyed by `locus` and `alleles`.
- `column`: sample fields, usually keyed by `s`.
- `entry`: per-row-by-column values such as `GT`, `DP`, `GQ`, `AD`, `PL`, `GP`, or `dosage`.
- `global`: metadata shared by the full dataset.

Choose axis-specific methods deliberately: `annotate_rows`, `annotate_cols`, `annotate_entries`, `annotate_globals`, `filter_rows`, `filter_cols`, `filter_entries`, `select_rows`, `select_cols`, `select_entries`, and `select_globals`. Avoid converting to `entries()` unless the task truly needs coordinate-form rows.

## Verified API Anchors

The inspected package exposes these dense-genomics entry points: `hl.import_vcf`, `hl.import_plink`, `hl.import_bgen`, `hl.export_vcf`, `hl.variant_qc`, `hl.sample_qc`, `hl.split_multi_hts`, `hl.linear_regression_rows`, `hl.logistic_regression_rows`, `hl.pca`, `hl.ld_prune`, and `hl.vep`. Treat `hl.vep` and `hl.nirvana` as external annotation boundaries: Hail joins annotations back to row variants, but executables, configs, caches, schemas, and assembly compatibility are environment responsibilities.

## Safe Defaults

- Import external genetics formats with an explicit `reference_genome`, inspect `mt.describe()`, then write or checkpoint native `.mt` before iterative analysis.
- Use `hl.variant_qc` and `hl.sample_qc` only when `GT` is a `call` entry field and row keys represent variant-like `locus`/`alleles`.
- Run `hl.split_multi_hts` before biallelic-only HWE-sensitive QC, LD pruning, many association workflows, and allele-specific annotations.
- Include an intercept explicitly in association covariates, usually `covariates=[1, ...]`.
- Keep dense workflows separate from VDS workflows; do not force sparse GVCF data into dense MatrixTables unless the task explicitly calls for densification.
