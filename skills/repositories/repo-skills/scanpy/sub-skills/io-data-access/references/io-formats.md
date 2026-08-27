# IO Formats and AnnData Persistence

## Core Readers and Writers

| API | Current signature pattern | Use for | Notes |
| --- | --- | --- | --- |
| `sc.read` | `read(filename, backed=None, *, sheet=None, ext=None, delimiter=None, first_column_names=False, backup_url=None, cache=False, cache_compression=sc.settings.cache_compression, **kwargs)` | Dispatching common numeric matrix formats into AnnData. | If `filename` lacks a known extension, Scanpy treats it as a key under `sc.settings.writedir`; pass `ext=` for unusual filenames. |
| `sc.read_h5ad` | `read_h5ad(filename, backed=None, as_sparse=(), as_sparse_fmt=csr_matrix, chunk_size=6000)` | Loading persisted AnnData from `.h5ad`. | Imported from AnnData IO. Use `backed="r"` for read-only large-file inspection; many Scanpy transformations require in-memory data. |
| `sc.write` | `write(filename, adata, *, ext=None, convert_strings_to_categoricals=True, compression="gzip", compression_opts=None)` | Writing AnnData through Scanpy's wrapper. | Extension usually controls format. String columns are converted to categoricals by default where AnnData supports it. |
| `adata.write_h5ad` | `adata.write_h5ad(filename, compression=None, ...)` | Direct AnnData persistence. | Use this when you do not need Scanpy's `sc.write` dispatch wrapper. |

Supported `sc.read` inputs include `.h5ad`, `.zarr`, `.h5`, `.loom`, `.mtx`, `.csv`, `.tsv`, `.tab`, `.data`, `.txt`, `.xlsx`, `.soft.gz`, and compressed text variants. For metadata-only annotation tables, prefer `pandas.read_*` and attach fields to `.obs`, `.var`, `.uns`, `.obsm`, or `.varm` explicitly.

## AnnData Slots to Preserve

- `.X` is the primary observation-by-variable matrix used by most Scanpy methods.
- `.layers[name]` stores alternate matrices with the same shape as `.X`, commonly `counts` or normalized variants.
- `.raw` stores a frozen expression snapshot with its own `.X` and `.var`; use it deliberately because it can hide differences from current `.X`.
- `.obs` and `.var` store observation and variable annotations; keep `.obs_names` and `.var_names` unique for reliable joins and `sc.get` lookup.
- `.obsm`, `.varm`, `.obsp`, and `.varp` store multi-dimensional arrays and pairwise matrices; verify shapes after concatenation or custom IO.
- `.uns` stores unstructured metadata such as spatial image metadata, differential-expression results, and pipeline parameters.

## 10x HDF5

Use:

```python
adata = sc.read_10x_h5(filename, genome=None, gex_only=True, backup_url=None)
```

Behavior to remember:

- Cell Ranger v3+ feature-barcode files store data under `/matrix`; Scanpy reads feature metadata into `.var`, including `gene_ids`, `feature_types`, and additional feature columns when present.
- `gex_only=True` filters `.var["feature_types"] == "Gene Expression"`; set it to `False` to retain antibody capture, CRISPR guide capture, or custom feature types.
- Legacy multi-genome HDF5 files require `genome=` when multiple genomes are present; invalid genome names raise a `ValueError` that lists available genomes.
- Probe barcode matrices may expose columns such as `probe_ids`, `probe_region`, `gene_name`, `filtered_probes`, and `filtered_barcodes`, depending on the file.
- The returned AnnData uses barcodes as observations and gene names or probe names as variables.

## 10x MTX Directories

Use:

```python
adata = sc.read_10x_mtx(
    path,
    var_names="gene_symbols",
    make_unique=True,
    cache=False,
    cache_compression=sc.settings.cache_compression,
    gex_only=True,
    prefix=None,
    compressed=True,
    sparse_format="csr",
)
```

Expected layouts:

| Layout | Files | Options |
| --- | --- | --- |
| Cell Ranger v2 legacy | `matrix.mtx`, `genes.tsv`, `barcodes.tsv` | `compressed` has no effect after legacy detection. |
| Cell Ranger v3+ compressed | `matrix.mtx.gz`, `features.tsv.gz`, `barcodes.tsv.gz` | Default `compressed=True`. |
| V3-style uncompressed or STARsolo | `matrix.mtx`, `features.tsv`, `barcodes.tsv` | Set `compressed=False`. |
| Prefixed outputs | `sample_matrix.mtx(.gz)`, `sample_features.tsv(.gz)`, `sample_barcodes.tsv(.gz)` | Set `prefix="sample_"`. |

Variable-name choices:

- `var_names="gene_symbols"` sets `.var_names` from the second feature column and stores IDs in `.var["gene_ids"]`.
- `var_names="gene_ids"` sets `.var_names` from the first feature column and stores symbols in `.var["gene_symbols"]`.
- `make_unique=True` appends suffixes to duplicate gene symbols. Use gene IDs or call `.var_names_make_unique()` when downstream code requires stable identifiers.
- Non-legacy v3 files populate `.var["feature_types"]`; with `gex_only=True`, non-expression rows are filtered after reading.
- `sparse_format` controls the loaded sparse representation: choose `"csr"` for common Scanpy row slicing, `"csc"` for variable-oriented slicing, or `"coo"` for specialized sparse workflows.

## Visium / Space Ranger

Use:

```python
adata = sc.read_visium(
    path,
    genome=None,
    count_file="filtered_feature_bc_matrix.h5",
    library_id=None,
    load_images=True,
    source_image_path=None,
)
```

Behavior to remember:

- `sc.read_visium` is deprecated in current Scanpy in favor of Squidpy's Visium reader, but remains useful for maintaining Scanpy-native workflows.
- Counts are loaded via `read_10x_h5(path / count_file, genome=genome)`.
- If `library_id` is omitted, Scanpy reads it from HDF5 attributes when available.
- With `load_images=True`, Scanpy expects a `spatial/` directory with `tissue_positions.csv` or `tissue_positions_list.csv`, `scalefactors_json.json`, `tissue_hires_image.png`, and `tissue_lowres_image.png`.
- Missing high/low image files are reported as warnings before image reading, but image read failures can raise `OSError`; missing positions or scalefactors raise errors.
- Successful spatial loads create `.uns["spatial"][library_id]["images"]`, `.uns["spatial"][library_id]["scalefactors"]`, `.uns["spatial"][library_id]["metadata"]`, and `.obsm["spatial"]`.
- `source_image_path` is stored in `.uns["spatial"][library_id]["metadata"]`; avoid embedding private machine paths in reusable examples.

## Backed Mode and Storage Conventions

- `sc.read_h5ad(path, backed="r")` keeps matrix data on disk. Use it for inspection, slicing, and selected extraction, not for general preprocessing.
- `sc.read_h5ad(path, backed="r+")` allows limited backed mutation. Do not assume ordinary Scanpy tools can update `.X`, `.layers`, `.obs`, or `.var` in backed mode.
- Load backed data into memory before transformations with `adata = adata.to_memory()`.
- `sc.get.obs_df` sorts backed variable indices internally before reading values, so it can extract selected genes from backed AnnData when keys are valid.
- Close backed files when finished, especially in scripts that overwrite or delete the `.h5ad` path.
- For public scripts, write temporary files under `tempfile.TemporaryDirectory()` unless the caller explicitly passes an output path.
