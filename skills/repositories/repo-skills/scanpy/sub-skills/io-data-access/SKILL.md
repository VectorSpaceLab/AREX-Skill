---
name: io-data-access
description: "Use when working with Scanpy input/output, AnnData persistence,
  10x HDF5/MTX ingestion, Visium spatial reads, built-in datasets, annotation
  queries, sc.get extraction helpers, backed reads, layers, and raw data
  access."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Scanpy IO and Data Access

Use this sub-skill when a task is about getting data into or out of Scanpy, preserving AnnData slots, loading 10x Genomics or Visium outputs, selecting bundled datasets, running annotation/enrichment queries, or extracting values with `sc.get`.

## Route Tasks

- Use `references/io-formats.md` for `sc.read`, `sc.read_h5ad`, `sc.read_10x_h5`, `sc.read_10x_mtx`, `sc.read_visium`, `sc.write`, `adata.write_h5ad`, backed mode, layers, raw, and AnnData storage conventions.
- Use `references/get-datasets-queries.md` for `sc.get.obs_df`, `sc.get.var_df`, `sc.get.rank_genes_groups_df`, `sc.get.aggregate`, `sc.datasets`, and `sc.queries` workflows.
- Use `references/troubleshooting.md` for missing 10x files, Visium image assets, backed-mode mutation limits, sparse/dense surprises, ambiguous gene keys, dataset downloads, and query dependency/network failures.
- Use `scripts/scanpy_io_roundtrip.py` to sanity-check an installed Scanpy runtime with a tiny `.h5ad` roundtrip, layer preservation, backed read inspection, and optional `sc.get.obs_df` extraction.

## Common Decisions

- Prefer `sc.read_h5ad(path, backed=None)` for normal `.h5ad` loading; use `backed="r"` for read-only large-file inspection and `backed="r+"` only for deliberate backed mutation.
- Prefer `sc.read_10x_h5(path, gex_only=True)` for Cell Ranger HDF5 feature-barcode matrices; set `gex_only=False` when antibody, CRISPR, or custom feature rows must be preserved.
- Prefer `sc.read_10x_mtx(dir, var_names="gene_symbols", make_unique=True, compressed=True, sparse_format="csr")` for Cell Ranger v3+ matrix directories; adjust `prefix`, `compressed=False`, or `var_names="gene_ids"` for nonstandard layouts or uniqueness needs.
- Prefer `sc.read_visium(dir, load_images=True)` only when Space Ranger spatial assets are available; use `load_images=False` for counts-only loading. The API is deprecated in current Scanpy releases, so route new spatial workflows to Squidpy when that integration is in scope.
- Prefer `sc.write(path, adata)` or `adata.write_h5ad(path)` for persistence; verify `.X`, `.layers`, `.raw`, `.obs`, `.var`, `.obsm`, and `.uns` fields that downstream steps rely on after roundtrips.

## Boundaries

- Do not cover matrix transformations such as filtering, normalization, HVG selection, scaling, batch correction, or QC metric calculation; route those to `../preprocessing-qc/SKILL.md` when present.
- Do not cover graph construction, clustering, embeddings, trajectory analysis, or differential-expression computation; route those to `../graph-embedding-analysis/SKILL.md` when present.
- Do not cover plotting output, figure export, or report styling; route plotting requests to `../plotting-reporting/SKILL.md` when present.
- Do not cover optional external integrations beyond IO/query dependencies; route cross-package integration design to `../external-integrations/SKILL.md` when present.
