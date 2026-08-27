# AUCell And Binarization API Reference

This reference covers pySCENIC activity scoring after regulons or gene signatures already exist. Expression matrices are expected as cells x genes unless a loader or CLI flag explicitly transposes them. AUCell and binarization matrices are cells x regulons/signatures.

## Core AUCell APIs

### `pyscenic.aucell.create_rankings(ex_mtx, seed=None)`

- Input: `pandas.DataFrame` with cells as rows and genes as columns.
- Output: a ranking `DataFrame` with the same shape and labels.
- Ranking semantics: highly expressed genes get low rank numbers; missing values are pushed to the bottom; tied values keep first-order ranking after optional seeded column shuffling.
- Use `seed` for repeatable tie handling.

### `pyscenic.aucell.derive_auc_threshold(ex_mtx)`

- Input: cells x genes expression matrix.
- Output: `Series` indexed by quantiles `[0.01, 0.05, 0.10, 0.50, 1]` containing fractions of genes detected per cell.
- Use it to choose an `auc_threshold` that avoids scoring too many genes beyond the detected portion of most cells.
- Example interpretation: `thresholds[0.01]` targets a threshold where, for 99% of cells, ranked genes used in AUCell have detected expression.

### `pyscenic.aucell.aucell(exp_mtx, signatures, auc_threshold=0.05, noweights=False, normalize=False, seed=None, num_workers=256)`

- Input `exp_mtx`: cells x genes `DataFrame`.
- Input `signatures`: sequence of `ctxcore.genesig.GeneSignature` objects; regulons from pySCENIC motif pruning are accepted here.
- `auc_threshold`: fraction of ranked genes used for recovery-curve AUC.
- `noweights`: when `True`, ignore gene weights in signatures/regulons.
- `normalize`: when `True`, divide each regulon's AUC values by that regulon's maximum so columns peak at `1.0`.
- `seed`: passed to `create_rankings`; use it for deterministic ranking tie behavior.
- `num_workers`: process count for scoring. Use `1` for smallest fixtures, debugging, and platforms where forked multiprocessing is risky.
- Output: cells x regulons/signatures `DataFrame`.

### `pyscenic.aucell.aucell4r(df_rnk, signatures, auc_threshold=0.05, noweights=False, normalize=False, num_workers=256)`

- Input `df_rnk`: ranking matrix from `create_rankings`, cells x genes.
- Use this when rankings are precomputed or shared across multiple signature sets.
- Output is the same cells x regulons/signatures AUC matrix as `aucell`.
- With `num_workers > 1`, rankings are copied to shared memory and each worker scores a chunk of signatures; reduce workers if memory or process-start overhead dominates.

## Signature And Regulon Inputs

Use Python `GeneSignature` objects for direct API calls. Typical sources are:

- `ctxcore.genesig.GeneSignature(name="Regulon", gene2weight={"GeneA": 1.0, "GeneB": 0.5})` for tiny or custom inputs.
- `GeneSignature.from_gmt(path, field_separator="\t", gene_separator="\t")` for GMT signature files.
- Regulons returned by pySCENIC motif pruning and conversion utilities.

The `pyscenic aucell` CLI loads signatures from these extension families:

- `.gmt`: gene set text files; separator is guessed from tab, semicolon, or comma-like structure.
- `.yaml` or `.yml`: serialized regulons/signatures.
- `.dat`: pickled regulons/signatures.
- `.csv` or `.tsv`: enriched motif table converted to regulons before scoring.

Validate gene identifier overlap before interpreting AUCs. Signatures with no overlap can produce all-zero or uninformative activity rather than a useful biological score.

## CLI Contract

`pyscenic aucell EXPRESSION SIGNATURES [options]` quantifies activity for gene signatures across cells.

Important options:

- `-o, --output`: write CSV/TSV, loom, or h5ad output; stdout is CSV-like text.
- `-t, --transpose`: use for text expression matrices stored genes x cells; the CLI internally converts to cells x genes.
- `-w, --weights`: use gene weights associated with signatures where available. Without it, CLI calls `aucell(..., noweights=True)`.
- `--auc_threshold FLOAT`: fraction of ranked genes used for AUC; default `0.05`.
- `--num_workers INT`: worker processes; default is CPU count.
- `--seed INT`: deterministic ranking tie behavior.
- Loom-related flags such as cell and gene attribute names affect loom input and output metadata.

Expression file handling:

- Text `.csv`/`.tsv` defaults to rows=cells, columns=genes.
- Text genes x cells matrices require `--transpose`.
- Loom files are stored rows=genes, columns=cells and are loaded as cells x genes.
- h5ad input uses AnnData observation names as cells and variable names as genes.

Output behavior:

- CSV/TSV/stdout are AUC matrices, cells x regulons by default.
- If `--transpose` was used and output is stdout or text, output may be transposed to match the requested text orientation; check rows and columns before downstream use.
- Loom output copies the expression loom then appends AUCell metadata, including derived thresholds and regulon membership.
- h5ad output requires h5ad input and optional AnnData support; AUCell metadata is added to a copied AnnData file.

## Binarization APIs

### `pyscenic.binarization.derive_threshold(auc_mtx, regulon_name, seed=None, method="hdt")`

- Input `auc_mtx`: cells x regulons AUC matrix.
- Input `regulon_name`: column name to threshold.
- `method="hdt"`: Hartigan's Dip Test decides whether the distribution is bimodal.
- `method="bic"`: compares one-component and two-component Gaussian mixtures with BIC.
- If the AUC distribution is unimodal, the threshold is `mean + 2 * std`.
- If bimodal, a two-component Gaussian mixture is fit and the trough between peaks is used.

### `pyscenic.binarization.binarize(auc_mtx, threshold_overides=None, seed=None, num_workers=1)`

- Input: cells x regulons AUC matrix.
- `threshold_overides`: optional mapping from regulon name to manual threshold. The public parameter is misspelled as `threshold_overides`, not `threshold_overrides`.
- `seed`: controls stochastic Gaussian mixture behavior in threshold derivation.
- `num_workers`: process count for deriving thresholds across regulons.
- Output: `(binary_mtx, thresholds)` where `binary_mtx` is cells x regulons with `0`/`1` calls and `thresholds` is a `Series` indexed by regulon name.
- Binary calls use strict `auc_mtx > thresholds` comparison.

## Plotting And RSS

### `pyscenic.plotting.plot_binarization(auc_mtx, regulon_name, threshold, bins=200, ax=None)`

Plots an AUC distribution for one regulon and draws the threshold line. Use a non-interactive Matplotlib backend in scripts or CI.

### `pyscenic.rss.regulon_specificity_scores(auc_mtx, cell_type_series)`

- Input `auc_mtx`: cells x regulons AUC matrix.
- Input `cell_type_series`: `pandas.Series` with cell identifiers as index and cell type labels as values.
- Output: cell type x regulon RSS `DataFrame`.
- Internally compares each regulon's AUC distribution to binary cell-type labels using Jensen-Shannon distance.
- Ensure `cell_type_series` is indexed and ordered like `auc_mtx.index`; use `cell_type_series.reindex(auc_mtx.index)` before calling when labels came from another table.

### `pyscenic.plotting.plot_rss(rss, cell_type, top_n=5, max_n=None, ax=None)`

Plots RSS values for one cell type and labels the top regulons. Input `rss` is the cell type x regulon matrix from `regulon_specificity_scores`.

## Practical Defaults

- Use `num_workers=1` for small fixtures, smoke tests, notebook debugging, and reproducibility checks.
- Use `seed` for deterministic AUCell tie handling and thresholding.
- Start with `auc_threshold=0.05`, then inspect `derive_auc_threshold(ex_mtx)` for sparse or shallow datasets.
- Use unweighted scoring for GMT gene sets or when weights are not meaningful; use weights when working with weighted regulons and the question requires weighted recovery.
- Treat normalized AUCs as convenient within-regulon scaling, not as a replacement for thresholding or between-regulon calibration.
