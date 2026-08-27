---
name: specialist-domains
description: "Use OmicVerse specialist domains for genetics/post-GWAS, AIRR
  immune repertoire, molecular structure/drug binding, raw sequencing alignment,
  amplicon pipelines, and external binary wrappers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# OmicVerse Specialist Domains

Use this sub-skill when the task involves `omicverse.genetics`, `omicverse.airr`, `omicverse.mol`, or `omicverse.alignment`, especially when the workflow may require optional scientific backends, downloads, or external command-line tools.

For root routing and adjacent domains, return to [the OmicVerse root skill](../../SKILL.md). Route core AnnData reading/QC/plotting to [core-analysis](../core-analysis/SKILL.md), table statistics and enrichment to [multiomics-statistics](../multiomics-statistics/SKILL.md), and single-cell biological annotation/trajectory workflows to [single-cell-workflows](../single-cell-workflows/SKILL.md).

## Safe Workflow

1. Classify the domain before coding: genetics summary statistics/genotypes, AIRR immune-repertoire AnnData/tables, molecular target/structure/drug binding, or raw sequencing/alignment.
2. Validate inputs before invoking heavy functions. Use `scripts/check_specialist_inputs.py` for column/schema checks, FASTQ pairing, and target-id sanity checks.
3. Gate side effects. Do not allow downloads, external binary execution, conda installs, or network structure/drug lookups unless the user explicitly approves the operation and output locations.
4. Prefer explicit paths over auto-discovery for command wrappers: pass `*_path`, `simpleaf_bin`, `alevin_fry_home`, `genome_dir`, `db_fasta`, and output directories deliberately.
5. Record produced artifacts and assumptions: GWAS canonical column names, allele harmonization decisions, AIRR `obs` chain fields, FASTQ sample names, genome/index/reference versions, and molecular query source.

## Domain Map

| User asks for | Use | First checks | Output signal |
| --- | --- | --- | --- |
| GWAS QC/association, eQTL, fine-map, coloc, MR, scDRS | `ov.genetics` | Summary-stat columns, genotype orientation, alleles, sample size, optional backend availability | DataFrames, filtered AnnData, backend result objects, plots |
| 10x V(D)J, AIRR TSV, clonotypes, clonal expansion, repertoire overlap | `ov.airr` | `AnnData.obs` AIRR chain slots or contig columns; `clone_id` before expansion metrics | AIRR AnnData, `obs` columns, diversity/overlap matrices, plots |
| SRA to FASTQ/counts, STAR, featureCounts, kb, simpleaf, 16S, DADA2, phylogeny | `ov.alignment` | FASTQ pair naming, reference/index paths, external binary paths, `auto_install` policy | Files, matrices, AnnData, command logs |
| Protein structure, known drugs, pockets, docking | `ov.mol` | Target ID type, network permission, Python/extras, docking backend availability | `MolStructure`, pocket/drug DataFrames, docking results, views |

## Read Next

- [Specialist workflows](references/genetics-airr-mol-alignment.md) for domain-specific implementation patterns.
- [API reference](references/api-reference.md) for concrete functions, parameters, and outputs.
- [Data formats](references/data-formats.md) for GWAS, AIRR, FASTQ, amplicon, and molecular input schemas.
- [Troubleshooting](references/troubleshooting.md) for optional extras, external binaries, downloads, allele harmonization, and docking issues.
- [Input validator](scripts/check_specialist_inputs.py) for safe read-only validation before running OmicVerse APIs.
