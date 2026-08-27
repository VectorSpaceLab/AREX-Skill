# Data Formats and AnnData Contracts

OmicVerse core workflows revolve around `AnnData` with observations as cells/spots/samples and variables as genes/features.

## AnnData Core Shape

| Component | Expected meaning | Common producers | Common consumers |
| --- | --- | --- | --- |
| `adata.X` | Main expression/count matrix, shape `n_obs × n_vars` | readers, `create_mock_dataset`, normalization functions | QC, preprocessing, plotting, downstream workflows |
| `adata.obs_names` | Cell/barcode/sample IDs | h5ad and 10x readers | metadata joins, plotting labels |
| `adata.var_names` | Gene/feature IDs or symbols | h5ad and 10x readers | HVG selection, gene coloring, subsetting |
| `adata.obs` | Per-observation metadata such as sample, condition, QC metrics, clusters | QC, clustering, user metadata | plotting, filtering, reports |
| `adata.var` | Per-feature metadata such as gene IDs, feature types, `highly_variable`, `mt` | IO, QC, HVG | preprocessing, plotting, reports |
| `adata.layers` | Alternate matrices such as `counts`, `scaled`, `regressed` | preprocessing and scaling | PCA, recovery, downstream methods |
| `adata.obsm` | Dense per-cell embeddings such as `X_pca`, `X_umap`, `spatial` | PCA, UMAP, spatial readers | embedding plots, neighbors, spatial workflows |
| `adata.obsp` | Pairwise sparse graphs such as `distances`, `connectivities` | neighbors | UMAP, clustering |
| `adata.uns` | Unstructured metadata, provenance, settings, graph metadata, report hints | most pipeline steps | reports, plotting, downstream methods |
| `adata.raw` | Optional frozen raw-ish expression snapshot | user code or selected workflows | gene expression plotting and annotation |

Always make `.var_names` unique before HVG selection and gene plotting:

```python
adata.var_names_make_unique()
```

## H5AD

Use h5ad when preserving full `AnnData` structure.

```python
adata = ov.io.read_h5ad("input.h5ad")
adata = ov.read("input.h5ad", backend="python")
adata.write_h5ad("processed.h5ad", compression="gzip")
```

For very large files, `ov.read("large.h5ad", backend="rust")` uses out-of-memory `anndataoom` when installed. The Rust backend can reject sparse matrices with unsorted minor indices. Recovery options are to read with the Python backend and rewrite sorted indices, or to use `ov.utils.convert_adata_for_rust(...)`.

## 10x Genomics HDF5

```python
adata = ov.io.read_10x_h5(
    "filtered_feature_bc_matrix.h5",
    genome=None,
    gex_only=True,
)
```

Expected output:

- `adata.obs_names`: cell barcodes.
- `adata.var_names`: feature/gene names.
- `adata.var['gene_ids']` and sometimes `adata.var['probe_ids']`.
- `adata.var['feature_types']` for v3 files.

Set `gex_only=False` to keep non-gene-expression features. For legacy multi-genome files, pass `genome="..."` when more than one genome is present.

## 10x Matrix Market Directory

```python
adata = ov.io.read_10x_mtx(
    "filtered_feature_bc_matrix",
    var_names="gene_symbols",
    make_unique=True,
    gex_only=True,
    prefix=None,
    compressed=True,
)
```

Accepted layouts:

- Modern Cell Ranger v3-style: `matrix.mtx.gz`, `features.tsv.gz`, `barcodes.tsv.gz`.
- Legacy layout: `matrix.mtx`, `genes.tsv`, `barcodes.tsv`.
- Plain text variants: set `compressed=False` when files are not gzip-compressed.
- Prefixed files: set `prefix="sample_"` for names such as `sample_matrix.mtx.gz`.

`var_names` controls the primary feature index:

| `var_names` | `adata.var_names` | Additional column |
| --- | --- | --- |
| `'gene_symbols'` | gene symbols, optionally made unique | `adata.var['gene_ids']` |
| `'gene_ids'` | gene IDs | `adata.var['gene_symbols']` |

When `gex_only=True`, rows with `feature_types != 'Gene Expression'` are dropped for v3 files.

## CSV, TSV, TXT, and Gzip Tables

`ov.read` returns a `pandas.DataFrame` for `.csv`, `.tsv`, `.txt`, and matching gzip text files.

```python
df = ov.read("counts.csv", index_col=0)
df = ov.io.read_csv("counts.csv", index_col=0, on_duplicate="warn")
df = ov.io.read_table("counts.tsv", index_col=0, on_duplicate="raise")
```

Prefer `ov.io.read_csv` or `ov.io.read_table` for sample matrices because they scan raw headers before pandas can auto-rename duplicate labels.

Duplicate policy:

| `on_duplicate` | Behavior |
| --- | --- |
| `'warn'` | Print a warning with duplicate labels and continue |
| `'raise'` | Raise `ValueError` before loading |
| `'ignore'` | Delegate directly to pandas behavior |

For sample × metadata analyses, run:

```python
result = ov.utils.preflight_alignment("counts.csv", "metadata.csv", sample_col="sample_id")
if result.needs_alignment:
    counts, metadata = ov.utils.align_to_common("counts.csv", "metadata.csv", result)
```

## Synthetic AnnData

Use synthetic data for smoke tests and examples:

```python
adata = ov.datasets.create_mock_dataset(
    n_cells=200,
    n_genes=500,
    n_cell_types=5,
    with_clustering=True,
    random_state=0,
)
```

Base synthetic output includes:

- `.obs['cell_type']`, `.obs['sample_id']`, `.obs['condition']`, `.obs['tissue']`.
- `.var['gene_symbols']`, `.var['highly_variable']`.
- With `with_clustering=True`, lightweight `.obsm['X_pca']`, `.obsm['X_umap']`, and `.obs['leiden']` may be added.

Do not use synthetic data for biological conclusions.

## Raw Counts Preservation

Before normalization, preserve raw counts in one of these locations:

```python
adata.layers["counts"] = adata.X.copy()
# or after preprocess:
ov.pp.preprocess(adata)
assert "counts" in adata.layers
```

For workflows that require raw counts and normalized data:

- Use `.layers['counts']` for raw integer-like counts.
- Use `.X` for current working matrix after normalization/logging.
- Use `.layers['scaled']` for PCA input after `ov.pp.scale`.
- Use `.raw` only when a downstream plot or method explicitly expects it.

## QC Columns

`ov.pp.qc_metrics` and `ov.pp.qc` use these standard columns:

| Slot | Column | Meaning |
| --- | --- | --- |
| `.obs` | `nUMIs` | Total counts per observation |
| `.obs` | `detected_genes` | Nonzero detected genes per observation |
| `.obs` | `mito_perc` | Mitochondrial fraction, not percent; `0.2` means 20% |
| `.obs` | `total_counts` | Scanpy-compatible total counts |
| `.obs` | `n_genes_by_counts` | Scanpy-compatible detected genes |
| `.obs` | `pct_counts_mt`, `pct_counts_ribo`, `pct_counts_hb` | Scanpy percent-scale values |
| `.var` | `mt`, `ribo`, `hb` | Feature flags for mitochondrial, ribosomal, and hemoglobin genes |

`ov.pl.qc` can draw threshold guide lines when passed the same `tresh` dict used by `ov.pp.qc`.

## Preprocessing Slots

After `ov.pp.preprocess(adata, mode='shiftlog|pearson', ...)`:

- `adata.layers['counts']` preserves raw counts.
- `adata.var['highly_variable']` and `adata.var['highly_variable_features']` mark HVGs.
- `adata.var` may include `means`, `variances`, and `residual_variances` depending on HVG method/backend.
- `adata.uns['status']['preprocess']` and `adata.uns['status_args']['preprocess']` record basic status.

After `ov.pp.scale(adata)`:

- `adata.layers['scaled']` contains scaled expression by default.
- `adata.uns['status']['scaled'] = True`.
- For sparse CPU data, `use_implicit_centering=True` can avoid materializing a dense scaled layer when `anndataoom` is available.

After `ov.pp.pca(adata)`:

- `adata.obsm['X_pca']` contains PC scores.
- `adata.varm['PCs']` contains loadings.
- `adata.uns['pca']['variance_ratio']` and related values describe variance.
- Alias keys such as `scaled|original|X_pca` can also appear.

After `ov.pp.neighbors(adata)`:

- `adata.uns['neighbors']` stores graph metadata.
- `adata.obsp['distances']` stores distances.
- `adata.obsp['connectivities']` stores weighted graph connectivity.

After `ov.pp.umap(adata)`:

- `adata.obsm['X_umap']` stores coordinates.
- If `key_added` is set, keyed UMAP outputs may be used instead.

## Saving Outputs

Recommended core outputs:

```python
adata.write_h5ad("processed.h5ad", compression="gzip")
ov.io.save(summary_object, "results/summary.pkl")
fig.savefig("figures/umap.png", dpi=150, bbox_inches="tight")
ov.report.from_anndata(adata, output="reports/core_report.html")
```

Use relative paths in portable scripts. Avoid embedding local environment prefixes, private paths, or credentials in saved reports or notebooks.

## Dataset Download Caveats

Named dataset loaders may fetch remote files into local cache directories and can fail from network, file corruption, or mirror changes. For reproducible tests:

- Prefer local `.h5ad` or `.mtx` fixtures.
- Use `create_mock_dataset` for import and API smoke checks.
- If a named loader fails after an interrupted download, delete the half-downloaded cache file and retry only when network use is acceptable.
