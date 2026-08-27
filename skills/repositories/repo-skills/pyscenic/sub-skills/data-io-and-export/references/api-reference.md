# Data I/O And Export API Reference

This reference covers pySCENIC file loading, conversion, metadata append, and export helpers. Unless stated otherwise, expression and AUCell matrices in Python are `pandas.DataFrame` objects with rows as cells and columns as genes or regulons.

## Matrix Loading And Saving

### `pyscenic.cli.utils.load_exp_matrix(fname, transpose=False, return_sparse=False, attribute_name_cell_id="CellID", attribute_name_gene="Gene")`

Loads an expression matrix from extension-dispatched input.

- `.csv` and `.tsv`: read with first row as column names and first column as row index. By default, rows are cells and columns are genes. Set `transpose=True` when the text file is genes x cells.
- `.loom`: reads loom rows from the row attribute named by `attribute_name_gene` and columns from the column attribute named by `attribute_name_cell_id`, then returns cells x genes. With `return_sparse=True`, returns `(sparse_matrix, genes, cells)` instead of a `DataFrame`.
- `.h5ad`: imports `anndata.read_h5ad`, reads with `backed="r"`, and maps observations to cells and variables to genes. With `return_sparse=True`, returns the sparse matrix plus gene and cell names.
- Unknown or unsupported suffixes raise `ValueError('Unknown file format ...')`.

### `pyscenic.cli.utils.save_matrix(df, fname, transpose=False)`

Saves a 2D matrix from a cells x columns `DataFrame`.

- `.csv` and `.tsv`: writes text with separator inferred from the suffix; set `transpose=True` to write genes/regulons as rows and cells as columns.
- `.loom`: calls the loom writer and stores rows as genes/features and columns as cells.
- `.h5ad` is accepted by the extension validator in some paths but is not implemented in `save_matrix`; use the `pyscenic aucell` h5ad output path or AnnData APIs instead.
- Unknown suffixes raise `ValueError`.

### `pyscenic.cli.utils.save_df_as_loom(df, fname)`

Writes a single-layer loom from a cells x genes or cells x regulons `DataFrame`.

- Loom row attribute: `Gene`, from `df.columns`.
- Loom column attribute: `CellID`, from `df.index`.
- Loom layer data: `df.T.values`, so loom physical orientation is rows=features and columns=cells.

## Signature, Module, And Motif Files

### `pyscenic.cli.utils.load_signatures(fname)`

Loads gene signatures or regulons for AUCell-like consumers.

- `.csv` and `.tsv`: read enriched motif tables through the motif loader and convert them to regulons.
- `.yaml` and `.yml`: load serialized regulons/signatures from YAML.
- `.gmt`: guess tab, semicolon, or comma-style separators and load GMT signatures.
- `.dat`: unpickle stored regulons/signatures.
- Unknown suffixes raise `ValueError`.

### `pyscenic.cli.utils.load_modules(fname)`

Loads module collections for motif pruning inputs.

- `.yaml` and `.yml`: load YAML modules.
- `.dat`: unpickle module objects; this is the faster path for large module collections.
- `.gmt`: load GMT gene signatures.
- Unknown suffixes raise `ValueError('Unknown file format for ...')`.

### `pyscenic.cli.utils.load_adjacencies(fname)`

Reads adjacency tables as CSV or TSV using extension-inferred separators. The first three columns are typed as transcription factor string, target string, and numeric importance.

### `pyscenic.cli.utils.save_enriched_motifs(df, fname)`

Writes motif enrichment results.

- `.csv` and `.tsv`: write the table directly.
- `.json`: convert rows to regulons and write a mapping from regulon name to target genes.
- `.dat`: pickle converted regulons.
- `.gmt`: write converted regulons as GMT.
- `.yaml` and `.yml`: serialize converted regulons/signatures.
- Unknown suffixes raise `ValueError`.

## CLI Conversion

### `csv2loom INPUT.csv OUTPUT.loom [-t|--transpose]`

Converts a text expression matrix into loom.

- Input is described as CSV with rows=cells and columns=genes; because it delegates to `load_exp_matrix`, `.tsv` also works when the path suffix is `.tsv`.
- Use `--transpose` when the text input is genes x cells.
- Output loom uses `CellID` and `Gene` attributes and physical rows=genes, columns=cells.
- The installed `setup.py` advertises `csv2loom` as a console script. If the console script is missing, use `python -m pyscenic.cli.csv2loom` only after confirming the package installation exposes the module.

## AUCell Metadata Append

### `pyscenic.cli.utils.append_auc_mtx(fname, ex_mtx, auc_mtx, regulons, seed=None, num_workers=1)`

Appends AUCell results and regulon metadata into an existing loom file.

- `fname`: existing loom file to mutate.
- `ex_mtx`: cells x genes expression matrix matching the loom cell and gene identifiers.
- `auc_mtx`: cells x regulons AUC matrix.
- `regulons`: sequence of regulon/signature objects with names, genes, optional weights, and optional context.
- Adds column attribute `RegulonsAUC`, row attribute `Regulons`, and compressed global `MetaData` with regulon threshold entries.
- Computes thresholds with `pyscenic.binarization.binarize`; route biological threshold interpretation to the AUCell and binarization sub-skill.

The `pyscenic aucell` CLI uses this function when output suffix is `.loom`: it first copies the input expression loom and then appends metadata. Therefore loom output from `pyscenic aucell` expects the input expression matrix to be loom, not CSV/TSV.

## SCope Loom Export

### `pyscenic.export.export2loom(ex_mtx, regulons, out_fname, cell_annotations=None, tree_structure=(), title=None, nomenclature="Unknown", num_workers=cpu_count(), embeddings={}, auc_mtx=None, auc_thresholds=None, compress=False)`

Creates a SCope-oriented loom file from a cells x genes expression matrix and regulons.

- Computes `auc_mtx` with AUCell when not supplied; pass a precomputed cells x regulons matrix to avoid recomputation.
- Computes thresholds with binarization when `auc_thresholds` is not supplied.
- Creates a default t-SNE embedding from the AUC matrix when `embeddings` is empty; pass explicit two-column embeddings for deterministic or precomputed layouts.
- `embeddings` maps display names to `DataFrame` objects indexed by cell ID with exactly two columns. The first mapping becomes the default SCope embedding.
- `cell_annotations` maps cell ID to annotation labels. Missing annotations default to `-`.
- `tree_structure` may contain up to three strings and is written to `SCopeTreeL1`, `SCopeTreeL2`, and `SCopeTreeL3` file attributes.
- `compress=True` compresses the SCope `MetaData` attribute with zlib/base64.
- Warns when regulon names contain no space; SCope-friendly names often include a TF part and a gene-count/context part such as `TF (12g)`.

## AnnData Metadata Export

### `pyscenic.export.add_scenic_metadata(adata, auc_mtx, regulons=None, bin_rep=False, copy=False)`

Adds SCENIC metadata to an AnnData-like object.

- Requires `auc_mtx` to be a cells x regulons `DataFrame` with the same number of rows as `adata.n_obs`.
- Writes `adata.obsm['X_aucell']` with AUC values.
- With `bin_rep=True`, writes `adata.obsm['X_aucell_bin']` after binarization.
- Adds per-regulon observation columns named `Regulon(<name>)`.
- When regulons are supplied, adds per-gene membership columns to `adata.var` and `adata.uns['aucell']` metadata containing regulon names and motif logo references when present.
- `copy=True` returns a modified copy; otherwise the object is modified in place and returned.

The `pyscenic aucell` CLI h5ad output path requires h5ad input, copies it, calls this function, and writes the copied AnnData file.

## Regulon Graph Export

### `pyscenic.export.export_regulons(regulons, fname)`

Writes regulons as a directed GraphML network.

- Each transcription factor becomes a node with group `transcription_factor`.
- Each target gene becomes an activated or inhibited target node based on whether the regulon's context contains `activating`.
- Each TF-target edge carries `weight`, `interaction`, and regulon context attributes.
- Output is GraphML written through NetworkX; use a `.graphml` suffix for clarity even though the function does not dispatch by extension.

## Console Entry-Point Caveat

The package metadata advertises console scripts named `pyscenic`, `csv2loom`, `db2feather`, `invertdb`, and `gmt2regions`. This checkout contains `pyscenic` and `csv2loom` sources, but the legacy `db2feather`, `invertdb`, and `gmt2regions` modules are not present. Treat missing legacy commands as an installation/source discrepancy, not as supported commands for this generated skill.