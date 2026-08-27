# Data Formats And Export Schemas

pySCENIC uses file extensions to choose parsers and writers. Future agents should validate suffixes, orientation, and identifier attributes before running long SCENIC steps or writing final artifacts.

## Extension Dispatch

| Data kind | Supported extensions | Notes |
| --- | --- | --- |
| Expression matrix input | `.csv`, `.tsv`, `.loom`, `.h5ad` | Text defaults to cells x genes; loom physical layout is rows=genes and columns=cells; h5ad requires optional AnnData support. |
| Matrix output through `save_matrix` | `.csv`, `.tsv`, `.loom` | `.h5ad` is not implemented by `save_matrix` despite some validator paths accepting it. |
| AUCell CLI output | stdout, `.csv`, `.tsv`, `.loom`, `.h5ad` | Loom output copies a loom input then appends metadata; h5ad output requires h5ad input. |
| Signatures | `.gmt`, `.yaml`, `.yml`, `.dat`, `.csv`, `.tsv` | CSV/TSV inputs are motif enrichment tables converted to regulons. |
| Modules | `.yaml`, `.yml`, `.dat`, `.gmt` | `.dat` is the faster serialized module path for large collections. |
| Adjacencies | `.csv`, `.tsv` | First three columns are TF, target, and numeric importance. |
| Enriched motifs output | `.csv`, `.tsv`, `.json`, `.dat`, `.gmt`, `.yaml`, `.yml` | Non-table outputs convert motif rows to regulons first. |
| Regulon graph export | usually `.graphml` | `export_regulons` writes GraphML and does not validate suffix. |

`PurePath(path).suffixes` is used, so compressed names such as `matrix.tsv.gz` still contain `.tsv` for separator inference in text paths that use pySCENIC's open helpers. For plain pandas reads in `load_exp_matrix`, confirm compressed text support in the installed pandas version before relying on it.

## Orientation Rules

### Python API convention

Use cells x genes for expression matrices:

- `ex_mtx.index`: cell identifiers.
- `ex_mtx.columns`: gene identifiers.
- `auc_mtx.index`: cell identifiers.
- `auc_mtx.columns`: regulon or signature names.

### Text files

CSV/TSV expression input defaults to cells as rows and genes as columns. Use transpose options only for genes x cells files:

- Python: `load_exp_matrix(path, transpose=True)`.
- `csv2loom`: `csv2loom input.tsv output.loom --transpose`.
- `pyscenic grn`, `add_cor`, `ctx`, and `aucell`: `--transpose` when the expression text file is genes x cells.

When saving text output with `save_matrix(df, path, transpose=True)`, pySCENIC writes features/regulons as rows and cells as columns. Without transpose, it writes cells as rows.

### Loom files

Loom physical layout is rows=genes/features and columns=cells. pySCENIC hides this for expression reads and returns cells x genes. Default attributes are:

- Row attribute `Gene`: gene or feature identifiers.
- Column attribute `CellID`: cell identifiers.
- Column attribute `RegulonsAUC`: structured AUCell matrix appended by `append_auc_mtx`.
- Row attribute `Regulons`: structured regulon membership matrix appended by `append_auc_mtx` or written by `export2loom`.
- Global attribute `MetaData`: JSON or compressed JSON with regulon thresholds, embeddings, annotations, and clustering metadata.

For non-standard loom files, pass `attribute_name_cell_id` and `attribute_name_gene` to API loaders or use the CLI `--cell_id_attribute` and `--gene_attribute` options.

## CSV And TSV Separators

pySCENIC infers separators strictly from suffix:

- Any suffix list containing `.csv` uses comma.
- Any suffix list containing `.tsv` uses tab.
- Mismatched content and suffix can silently create a one-column frame or malformed labels. Check `df.shape`, `df.index`, and a few column names immediately after loading.

GMT signature loading is different: pySCENIC guesses a separator from tab, semicolon, then comma-like structure.

## SCope Loom Requirements

`export2loom` creates a loom file intended for SCope-like viewers. Prepare these inputs deliberately:

- Expression matrix: cells x genes, with cell IDs matching any AUC matrix, annotation mapping, and embedding indices.
- Regulons: names should be SCope-friendly. Names without spaces trigger a warning because SCope often expects a TF token separated from context, for example `TF (12g)`.
- Embeddings: mapping of display name to a two-column `DataFrame` indexed by cell ID. The first embedding is written as the default embedding. Use an ordered mapping when default choice matters.
- Tree structure: at most three levels; missing levels are filled as empty strings.
- Metadata compression: use `compress=True` only when the target consumer expects compressed SCope metadata.
- Cell annotations: mapping from cell ID to label. Missing annotations default to `-`.

If `auc_mtx` or embeddings are not supplied, `export2loom` computes them. For deterministic exports, pass precomputed AUCell values, thresholds, and embeddings.

## AnnData Metadata Layout

`add_scenic_metadata` modifies an AnnData-like object as follows:

- `obsm['X_aucell']`: dense AUC values, cells x regulons.
- `obsm['X_aucell_bin']`: optional binary values when `bin_rep=True`.
- `obs`: one column per regulon, named `Regulon(<regulon_name>)`.
- `var`: optional regulon membership columns when regulon objects are supplied.
- `uns['aucell']`: regulon names and motif logo references.

The function checks only row count, not exact cell-name equality. Future agents should align `auc_mtx.index` to `adata.obs_names` before calling it.

## GraphML Regulon Export

`export_regulons` emits a directed graph with transcription factors pointing to target genes. Use it when a downstream tool needs a network representation rather than motif tables or regulon objects. Verify that regulon context attributes are GraphML-serializable strings or scalar values; complex context values can fail in NetworkX GraphML writers.

## Safe Validation Pattern

Before large exports:

1. Load a tiny slice or fixture with the same suffix and orientation.
2. Confirm cells and genes land on the expected axis.
3. For loom, confirm row and column attribute names.
4. For h5ad, confirm optional AnnData import and backed-mode behavior.
5. For SCope, confirm regulon names, embeddings, tree levels, and metadata compression expectations.
6. Run the bundled `scripts/io_format_probe.py` in the target environment to check installed loader/writer behavior.