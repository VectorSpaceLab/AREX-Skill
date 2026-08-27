# Extraction Helpers, Datasets, and Queries

## `sc.get` Extraction Helpers

| API | Current signature pattern | Use for | Key behavior |
| --- | --- | --- | --- |
| `sc.get.obs_df` | `obs_df(adata, keys=(), obsm_keys=(), *, layer=None, gene_symbols=None, use_raw=False)` | Build an observation-indexed DataFrame from `.obs`, gene expression, and selected `.obsm` columns. | Keys can refer to `.obs.columns`, `.var_names`, or `.var[gene_symbols]`. `use_raw=True` cannot be combined with `layer`. |
| `sc.get.var_df` | `var_df(adata, keys=(), varm_keys=(), *, layer=None)` | Build a variable-indexed DataFrame from `.var`, cell expression, and selected `.varm` columns. | Keys can refer to `.var.columns` or `.obs_names`; expression values become variable-indexed columns. |
| `sc.get.rank_genes_groups_df` | `rank_genes_groups_df(adata, group, *, key="rank_genes_groups", pval_cutoff=None, log2fc_min=None, log2fc_max=None, gene_symbols=None)` | Convert `sc.tl.rank_genes_groups` output from `.uns` into a tidy DataFrame. | `group=None` returns all groups and keeps a `group` column; a single group omits the column for backward compatibility. |
| `sc.get.aggregate` | `aggregate(adata, by, func, *, axis=None, mask=None, dof=1, layer=None, obsm=None, varm=None)` | Aggregate expression or embeddings by categorical labels for pseudobulk-style summaries. | Metrics are stored as output layers; valid functions include `count_nonzero`, `sum`, `mean`, `var`, and `median`. |

## `obs_df` Patterns

```python
df = sc.get.obs_df(
    adata,
    keys=["cell_type", "MS4A1", "CD8A"],
    obsm_keys=[("X_umap", 0), ("X_umap", 1)],
)
```

- If a key exists in both `.obs.columns` and gene identifiers, Scanpy raises a `KeyError`; rename the annotation or use an unambiguous gene key.
- If `gene_symbols=` is supplied, keys can match `.var[gene_symbols]`. Duplicate symbol matches raise a `KeyError`; use `.var_names` or deduplicate the symbol column before extraction.
- `obsm_keys` columns are named like `X_umap-0`. Sparse `.obsm` matrices are converted to dense vectors for requested columns.
- Use `layer="counts"` to extract values from a layer. Use `use_raw=True` to extract from `.raw`; do not pass both.
- Backed AnnData is supported for valid expression-key extraction, but the returned DataFrame is in memory.

## `var_df` Patterns

```python
df = sc.get.var_df(adata, keys=["n_cells", "cell_001"], varm_keys=[("PCs", 0)])
```

- Keys can combine `.var` annotations and observation names.
- Expression values are transposed so the returned DataFrame is indexed by `.var_names`.
- `varm_keys` columns are named like `PCs-0` and may come from NumPy, sparse, or pandas-backed `.varm` entries.
- Use `layer=` when variable-level summaries should come from a specific layer rather than `.X`.

## `rank_genes_groups_df` Patterns

```python
markers = sc.get.rank_genes_groups_df(
    adata,
    group="B cells",
    key="rank_genes_groups",
    pval_cutoff=0.05,
    log2fc_min=0.25,
    gene_symbols="symbol",
)
```

- For non-logistic methods, returned columns include `names`, `scores`, `logfoldchanges`, `pvals`, and `pvals_adj`.
- For logistic regression, returned columns include `names` and `scores` only.
- When `sc.tl.rank_genes_groups(..., pts=True)` was used, Scanpy also merges `pct_nz_group` and `pct_nz_reference`.
- Use `key=` when differential-expression results were stored with `key_added=`.
- `gene_symbols=` joins the chosen `.var` column onto the result using gene names from the differential-expression table.

## `aggregate` Patterns

```python
agg = sc.get.aggregate(
    adata,
    by=["sample", "cell_type"],
    func=["mean", "count_nonzero"],
    layer="counts",
    mask="passes_qc",
)
```

- `by` can be one categorical column or multiple columns. Missing group combinations are omitted.
- The output `.obs` contains grouping columns and `n_obs_aggregated`; each requested metric is stored in `agg.layers[metric]`.
- `axis=None` defaults to `axis=0` unless `varm=` is supplied. Use `axis=1` to aggregate variables by `.var` labels.
- Pass only one of `layer`, `obsm`, or `varm`; Scanpy raises `TypeError` if more than one is provided.
- `obsm` can only be used when aggregating observations; `varm` can only be used when aggregating variables.
- For Dask-backed arrays, feature-axis chunking must be compatible with the aggregation implementation.

## Built-in Datasets

| Dataset API | Access pattern | Notes |
| --- | --- | --- |
| `sc.datasets.blobs` | Local synthetic data. | Creates Gaussian blobs with `.obs["blobs"]`; no network required. |
| `sc.datasets.krumsiek11` | Bundled text data. | Reads a packaged text matrix and annotates `.obs["cell_type"]`. |
| `sc.datasets.pbmc68k_reduced` | Packaged `.h5ad`. | Good small example containing annotations and embeddings; no network needed when package data is present. |
| `sc.datasets.pbmc3k` | Downloads and caches raw PBMC `.h5ad`. | Raw 10x PBMC matrix with `.var["gene_ids"]`; network required on first use. |
| `sc.datasets.pbmc3k_processed` | Downloads and caches processed PBMC `.h5ad`. | Includes labels, embeddings, neighbors, PCA, and `rank_genes_groups`; useful for `sc.get.rank_genes_groups_df` examples. |
| `sc.datasets.visium_sge` | Downloads Space Ranger Visium files, then calls `read_visium`. | Deprecated in favor of Squidpy datasets; may download counts, spatial tarball, and optional high-resolution TIFF. |
| Other named datasets | `ebi_expression_atlas`, `moignard15`, `paul15`, `toggleswitch`. | Some use packaged files; others require network and optional readers such as Excel support. |

Dataset downloads use `sc.settings.datasetdir`. In reusable code, set it to a caller-selected cache directory and handle network failure explicitly.

## Online Queries

| API | Dependency | Purpose | Notes |
| --- | --- | --- | --- |
| `sc.queries.biomart_annotations(org, attrs, *, host="www.ensembl.org", use_cache=False)` | `pybiomart` | Retrieve selected BioMart attributes for an organism. | `use_cache=True` may create a `.pybiomart.sqlite` file in the current directory. |
| `sc.queries.gene_coordinates(org, gene_name, *, gene_attr="external_gene_name", chr_exclude=(), host="www.ensembl.org", use_cache=False)` | `pybiomart` | Retrieve chromosome/start/end rows for one gene. | Use `chr_exclude` to remove non-standard contigs. |
| `sc.queries.mitochondrial_genes(org, *, attrname="external_gene_name", host="www.ensembl.org", use_cache=False, chromosome="MT")` | `pybiomart` | Retrieve mitochondrial gene identifiers. | Change `chromosome` for organisms with different mitochondrial chromosome names. |
| `sc.queries.enrich(container, *, org="hsapiens", gprofiler_kwargs={})` | `gprofiler-official` | Run g:Profiler enrichment for a list or mapping of genes. | Also dispatches on AnnData with `enrich(adata, group, key="rank_genes_groups", ...)`. |

For offline or deterministic workflows, prefer precomputed annotation tables over live queries. If using queries, catch `ImportError`, HTTP/network failures, and empty result DataFrames, then persist retrieved annotations into the project data area for reproducibility.
