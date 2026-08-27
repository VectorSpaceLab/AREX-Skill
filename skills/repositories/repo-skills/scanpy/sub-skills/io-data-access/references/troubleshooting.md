# Troubleshooting IO and Data Access

## 10x MTX Path, Prefix, or Compression Fails

Symptoms:

- `FileNotFoundError` for `matrix.mtx.gz`, `features.tsv.gz`, or `barcodes.tsv.gz`.
- Empty or wrong-shaped AnnData after pointing to a parent directory.
- STARsolo or custom Cell Ranger exports load only after manual file renaming.

Fixes:

- Point `sc.read_10x_mtx` at the directory containing the matrix files, not a parent project directory.
- For Cell Ranger v3+ compressed output, keep defaults: `compressed=True` with `matrix.mtx.gz`, `features.tsv.gz`, and `barcodes.tsv.gz`.
- For uncompressed v3-style output or STARsolo, set `compressed=False` so Scanpy looks for `matrix.mtx`, `features.tsv`, and `barcodes.tsv`.
- For prefixed files such as `patientA_matrix.mtx.gz`, set `prefix="patientA_"`.
- Legacy v2 output uses `genes.tsv`; `compressed` does not affect legacy detection.
- Choose `sparse_format="csr"` unless a downstream workflow explicitly benefits from `"csc"` or `"coo"`.

## 10x HDF5 Genome or Feature Rows Look Wrong

Symptoms:

- Legacy multi-genome HDF5 files raise a genome-selection `ValueError`.
- Antibody capture, CRISPR guide, or custom feature rows are missing.
- `.var["feature_types"]` contains only `Gene Expression` after loading.

Fixes:

- Inspect the error message for available genomes and pass a valid `genome=` value for legacy multi-genome files.
- Set `gex_only=False` when non-gene-expression feature types are needed.
- After loading all feature types, subset explicitly, for example `adata[:, adata.var["feature_types"] == "Antibody Capture"]`.
- Record feature-type decisions in analysis metadata so downstream preprocessing does not silently mix modalities.

## Duplicate Gene Symbols or Ambiguous Keys

Symptoms:

- Warnings about variable names not being unique.
- `sc.get.obs_df(..., gene_symbols="symbol")` raises duplicate-entry errors.
- A key exists both in `.obs.columns` and gene identifiers.
- `Could not find keys ... in columns of adata.obs or adata.var_names` appears despite expected symbols being present.

Fixes:

- Prefer `var_names="gene_ids"` when ingesting 10x data if stable unique identifiers matter.
- Keep `make_unique=True` for symbol-based 10x reads, or run `adata.var_names_make_unique()` before expression lookups.
- Rename `.obs` columns that collide with gene names, or request unambiguous keys.
- If `.var[gene_symbols]` contains duplicates, extract by `.var_names` or deduplicate the symbol column before calling `sc.get.obs_df`.
- Confirm whether the expression source is `.X`, `layer=...`, or `.raw`; symbol availability can differ in `.raw.var`.

## Backed Read Limitations

Symptoms:

- Preprocessing or tool functions raise `NotImplementedError` for backed arrays.
- Layer or `.raw` operations fail after `sc.read_h5ad(path, backed="r")`.
- A file cannot be overwritten or removed because an AnnData backing file is still open.

Fixes:

- Use backed mode for inspection, slicing, or selected extraction; load into memory with `adata = adata.to_memory()` before transformations.
- Use `backed="r+"` only for intentional backed mutation and close backed files when done.
- For `sc.get.obs_df` on backed AnnData, keep requested gene keys unique; Scanpy handles ordered backed indexing internally.
- Avoid assuming `.layers` and `.raw` are freely mutable in backed mode.
- In scripts, close with `adata.file.close()` when available before deleting or replacing the backing file.

## Sparse and Dense Surprises

Symptoms:

- A pandas export unexpectedly materializes a large sparse matrix in memory.
- Expression extraction returns dense arrays or DataFrames.
- Sparse slicing is slow for the chosen direction.

Fixes:

- Treat `sc.get.obs_df` and `sc.get.var_df` as tabular extraction helpers that can densify requested values.
- Keep requested gene or observation lists small when extracting from large sparse matrices.
- For 10x MTX reads, use `sparse_format="csr"` for common observation-oriented workflows and `"csc"` when variable-oriented slicing dominates.
- Avoid converting full `.X` to a dense DataFrame unless the matrix is known to be small.

## Raw and Layer Confusion

Symptoms:

- Expression values from `sc.get.obs_df` do not match expected counts or normalized values.
- `AssertionError` occurs when both `use_raw=True` and `layer=` are passed.
- Downstream exports mix `.X` values with `.layers["counts"]` or `.raw.X` unintentionally.

Fixes:

- Decide the expression source before extraction: `.X` by default, `layer="counts"` for a named layer, or `use_raw=True` for `.raw`.
- Do not pass `use_raw=True` and `layer=` together.
- When exporting tables, include the source matrix name in filenames or metadata, such as `obs_df_counts.csv` or `obs_df_raw.csv`.
- Inspect `adata.layers.keys()` and `adata.raw is not None` before selecting a source.
- After a roundtrip, verify that required layers and `.raw` are still present before continuing.

## Dataset Downloads and Query Network Failures

Symptoms:

- Built-in datasets fail on first call because downloads are unavailable.
- Query functions raise `ImportError` for `pybiomart` or `gprofiler-official`.
- Query functions return empty DataFrames or fail due to remote service issues.
- BioMart caching creates `.pybiomart.sqlite` in an unexpected working directory.

Fixes:

- Use local datasets such as `sc.datasets.blobs()` or packaged reduced datasets for deterministic smoke tests.
- Set `sc.settings.datasetdir` to a persistent user cache directory before calling network datasets.
- Treat datasets and queries as optional network operations; catch errors and provide an offline fallback.
- Install query dependencies only when needed: `pybiomart` for BioMart queries and `gprofiler-official` for enrichment.
- For reproducible pipelines, persist retrieved annotation/enrichment tables and read them back with pandas.
- If using BioMart cache, run from a deliberate project directory or disable `use_cache`.

## Visium Image Files Missing

Symptoms:

- `sc.read_visium` raises `OSError` for `spatial/tissue_positions*` or `spatial/scalefactors_json.json`.
- Missing `tissue_hires_image.png` or `tissue_lowres_image.png` warnings/errors appear.
- `.uns["spatial"]` or `.obsm["spatial"]` is absent or incomplete.
- A stored `source_image_path` exposes a private path in reusable output.

Fixes:

- Verify the Space Ranger directory has the count file and a `spatial/` subdirectory.
- Use `count_file="raw_feature_bc_matrix.h5"` if loading raw counts instead of filtered counts.
- Set `load_images=False` when only count data is needed or image assets are absent.
- If image-based plotting is required, restore `tissue_hires_image.png`, `tissue_lowres_image.png`, `scalefactors_json.json`, and tissue positions before loading.
- Use `library_id=` when combining multiple Visium libraries to avoid overwriting `.uns["spatial"]` keys.
- Do not persist machine-specific `source_image_path` values in shared examples or public skill content.
