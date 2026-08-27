---
name: diversity-tables
description: "Compute scikit-bio community diversity metrics and prepare
  BIOM-style table-like inputs for count workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Diversity Tables

Use this sub-skill when a task asks for alpha diversity, beta diversity, phylogenetic diversity, UniFrac, large beta-distance computation, BIOM-style tables, table-like count matrices, or table augmentation for biological community data.

## Read First

- `references/api-reference.md` for callable signatures, return types, metric discovery, table orientation, and augmentation APIs.
- `references/workflows.md` for input preparation, alpha/beta runs, Faith PD/UniFrac setup, block decomposition, and dense/table conversions.
- `references/troubleshooting.md` for invalid counts, sample/taxon length errors, callable-vs-string metrics, tree/taxa mismatch, table axis confusion, optional backend limits, and `validate=False` risks.
- `scripts/diversity_table_smoke.py` for a deterministic smoke check covering `sobs`, Bray-Curtis, Faith PD, UniFrac, and `Table` dense conversion.

## Typical Routing

- Compute richness, evenness, observed features, Chao1, Faith PD, or any per-sample metric with `skbio.diversity.alpha_diversity`.
- Compute Bray-Curtis, Jaccard, Euclidean, weighted UniFrac, unweighted UniFrac, or SciPy pairwise distances with `skbio.diversity.beta_diversity`.
- Use `skbio.diversity.block_beta_diversity` when many samples or features make full beta diversity expensive and block/map-reduce execution is appropriate.
- Use `skbio.diversity.partial_beta_diversity` only for explicit ID pairs and with caution because uncomputed distances are represented as zeros.
- Use `skbio.table.Table`, `skbio.table.example_table`, pandas DataFrames, NumPy arrays, or other supported table-like inputs when rows are samples and columns are features/taxa.
- Use `skbio.table.mixup`, `aitchison_mixup`, `compos_cutmix`, or `phylomix` only as table augmentation helpers for synthetic biological count/composition workflows.

## Boundaries

- Route tree construction, rooting, branch-length repair, and detailed `TreeNode` validation to `../trees-phylogeny/SKILL.md`.
- Route statistical testing, ordination, PERMANOVA/ANOSIM, and visualization of resulting `DistanceMatrix` objects to `../statistics-ordination/SKILL.md`.
- Route BIOM/TSV/FASTA/Newick file reading and metadata parsing to `../io-metadata/SKILL.md`.
- Keep this sub-skill focused on count/table preparation, diversity drivers, metrics, outputs, and table augmentation.
