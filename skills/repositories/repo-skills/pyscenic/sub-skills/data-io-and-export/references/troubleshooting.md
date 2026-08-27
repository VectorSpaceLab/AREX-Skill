# Data I/O And Export Troubleshooting

Use this guide for pySCENIC load/save, conversion, loom, h5ad, AnnData, SCope, GraphML, and entry-point issues.

## CSV/TSV Separator Or Extension Mismatch

Symptoms:

- Loaded matrix has one data column when many genes were expected.
- Cell identifiers appear as one long comma- or tab-containing string.
- `ValueError: Unknown file format` for a text matrix.

Checks and fixes:

- Match suffix to content: comma-separated files need `.csv`; tab-separated files need `.tsv`.
- pySCENIC chooses separators from suffix, not file sniffing, for expression matrix text I/O.
- Keep the first row as headers and the first column as row labels for expression matrices.
- For compressed or multi-suffix names, ensure one suffix is still `.csv` or `.tsv`.

## Transpose And Orientation Mistakes

Symptoms:

- Cells appear as genes or genes appear as cells after loading.
- AUCell output has unexpected row/column labels.
- Loom conversion writes cell IDs into gene attributes.

Checks and fixes:

- Python APIs expect expression matrices as cells x genes.
- Text inputs stored genes x cells require `transpose=True` or CLI `--transpose`.
- Loom physical layout is rows=genes and columns=cells; pySCENIC loads it back as cells x genes.
- Run `scripts/io_format_probe.py` to verify loader and writer behavior in the current environment.

## Loom Attribute Names

Symptoms:

- Loading loom raises a missing-key error for `Gene` or `CellID`.
- Loom output contains data but downstream tools cannot identify cells or genes.
- AUCell append does not line up with expected cell names.

Checks and fixes:

- Default row attribute is `Gene`; default column attribute is `CellID`.
- For non-standard loom files, pass API arguments `attribute_name_gene` and `attribute_name_cell_id`, or CLI flags `--gene_attribute` and `--cell_id_attribute`.
- Confirm expression matrix, AUC matrix, and regulon membership all use the same gene and cell identifier namespace.
- `pyscenic aucell -o output.loom` expects the expression input to be loom because it copies the input loom before appending metadata.

## h5ad And AnnData Caveats

Symptoms:

- `ModuleNotFoundError: No module named 'anndata'`.
- h5ad loading fails in backed mode or exposes `.X` differently than expected.
- `pyscenic aucell` h5ad output errors when expression input is CSV/TSV.

Checks and fixes:

- h5ad support is optional and requires AnnData to be importable.
- `load_exp_matrix` reads h5ad with `read_h5ad(..., backed='r')`; backed objects and sparse arrays vary by AnnData version.
- `pyscenic aucell -o output.h5ad` requires h5ad input, copies that file, and adds metadata to the copy.
- Align `auc_mtx.index` to `adata.obs_names`; `add_scenic_metadata` checks row count but does not guarantee name alignment.
- If h5ad behavior is version-sensitive, load the file with AnnData yourself, normalize to an in-memory object, and call `add_scenic_metadata` intentionally.

## SCope Loom Export Problems

Symptoms:

- SCope or a loom viewer cannot find embeddings, thresholds, or annotations.
- Export warns that regulon names are incompatible with SCope.
- `Exception: The embedding should have two columns.`
- Metadata appears compressed when the consumer expects plain JSON, or vice versa.

Checks and fixes:

- Use regulon names with a TF token and context separated by a space, such as `TF (12g)`, when targeting SCope.
- Pass embeddings as a mapping of name to two-column `DataFrame`; indices should match expression cell IDs.
- Use an ordered mapping when the first/default embedding matters.
- Provide at most three `tree_structure` levels.
- Pass precomputed `auc_mtx`, thresholds, and embeddings for deterministic exports; otherwise `export2loom` can compute AUCell, thresholds, and t-SNE.
- Set `compress=True` only when the target SCope workflow expects compressed metadata.

## Output Extension Errors

Symptoms:

- `ValueError: Unknown file format` while saving.
- `.h5ad` output through `save_matrix` does not behave like CSV/TSV/loom.
- A GraphML export succeeds but has an unexpected extension.

Checks and fixes:

- Use `.csv`, `.tsv`, or `.loom` for `save_matrix`.
- Use the `pyscenic aucell` h5ad output branch or `add_scenic_metadata` for h5ad workflows.
- Use `.csv`, `.tsv`, `.json`, `.dat`, `.gmt`, `.yaml`, or `.yml` for `save_enriched_motifs`.
- Use a clear `.graphml` suffix for `export_regulons`; the function delegates directly to NetworkX and does not dispatch by suffix.

## Optional Dependency Failures

Symptoms:

- `ModuleNotFoundError` for `loompy`, `anndata`, `networkx`, or `ctxcore`.
- The bundled I/O probe reports that loom checks were skipped.

Checks and fixes:

- Core pySCENIC imports require its runtime dependencies, including pandas/numpy/ctxcore; loom work requires `loompy`; h5ad work requires `anndata`; GraphML export requires `networkx`.
- The generated helper script is safe to run without loompy: it reports text I/O checks and skips loom checks when loom support is not importable.
- Do not treat skipped optional checks as proof that loom or h5ad export works; install or activate an environment with the relevant optional dependency first.

## Missing Legacy Console Scripts

Symptoms:

- `db2feather`, `invertdb`, or `gmt2regions` command is advertised in packaging metadata but fails at import or command lookup.
- `pkg_resources` or console script resolution reports `pyscenic.cli.db2feather` or similar missing.

Checks and fixes:

- This checkout advertises `db2feather`, `invertdb`, and `gmt2regions` in package entry points, but the corresponding source modules are absent.
- Document this as a package/source discrepancy and avoid promising those commands in workflows.
- Use currently present and verified entry points such as `pyscenic` and `csv2loom` for this sub-skill's runtime guidance.
- Route database conversion or legacy command requests to the CLI/container sub-skill only after verifying the installed package actually exposes the command.

## GraphML Export Failures

Symptoms:

- NetworkX GraphML writer rejects an attribute type.
- Target nodes or edges do not show expected activating/inhibiting labels.

Checks and fixes:

- `export_regulons` labels edges as activating only when the regulon context contains `activating`; otherwise it uses inhibiting labels.
- Ensure context attributes are strings or simple scalar values before exporting to GraphML.
- Confirm each regulon has `transcription_factor`, `gene2weight`, and `context` attributes.