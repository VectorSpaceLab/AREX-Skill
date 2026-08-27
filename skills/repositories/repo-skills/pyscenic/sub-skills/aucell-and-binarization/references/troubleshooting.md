# AUCell And Binarization Troubleshooting

Use this guide when AUCell scoring, thresholding, output interpretation, plotting, loom/h5ad output, or RSS results look wrong.

## Matrix Orientation Is Wrong

Symptoms:

- Output rows are genes instead of cells, or output columns are cells instead of regulons.
- Signature-enriched cells do not score higher than unrelated cells.
- CLI output shape is the transpose of the expected cells x regulons matrix.

Checks and fixes:

- Python `aucell` expects `exp_mtx.index` to be cells and `exp_mtx.columns` to be genes.
- Text CLI input defaults to rows=cells, columns=genes.
- Add `pyscenic aucell --transpose` only when text input is genes x cells.
- Loom storage is rows=genes and columns=cells, but the loader returns cells x genes.
- Treat AUC and binary matrices as cells x regulons unless you deliberately transposed text output.

## Signature Or Regulon Format Is Wrong

Symptoms:

- CLI reports an unknown signature file format.
- All signatures disappear, fail to load, or get unexpected names.
- Gene weights are ignored unexpectedly.

Checks and fixes:

- CLI signature inputs are `.gmt`, `.yaml`/`.yml`, `.dat`, or `.csv`/`.tsv` enriched motif tables.
- Python API expects `ctxcore.genesig.GeneSignature` objects or compatible regulons.
- For GMT files, keep signature name, description, and genes separated consistently; pySCENIC guesses common separators but malformed files can still load incorrectly.
- For weighted recovery in the CLI, pass `--weights`; without it the CLI sets `noweights=True`.
- For Python API, set `noweights=False` to use weights and `noweights=True` to ignore them.

## Empty Or Non-Overlapping Signatures

Symptoms:

- A signature column is all zero or nearly constant.
- The result has expected columns but no meaningful activity separation.
- A fake or species-mismatched gene set appears to run without a hard error.

Checks and fixes:

- Compare each signature's genes to `exp_mtx.columns` before scoring.
- Check gene symbol case, species nomenclature, Ensembl-vs-symbol mismatches, and delimiter mistakes.
- Remove or flag signatures with no overlap; pySCENIC can score them but biological interpretation is invalid.
- Use a tiny positive-control signature made from highly expressed genes to verify the scoring path.

## Multiprocessing Or Shared Memory Problems

Symptoms:

- AUCell is slower with many workers on small data.
- A worker process exits or memory usage spikes during scoring.
- Results are difficult to debug because failures happen in child processes.

Checks and fixes:

- Use `num_workers=1` for smoke tests, small matrices, and debugging.
- `aucell4r` copies rankings into shared memory when `num_workers > 1`; large cells x genes matrices can still require substantial memory.
- Reduce workers when signature count is small, process startup cost dominates, or system memory is limited.
- Fix `seed` to make tie handling and thresholding repeatable while debugging.

## Output Transpose Confusion

Symptoms:

- Downstream code expects cells x regulons but receives regulons x cells.
- CLI stdout or text output differs from Python API orientation.

Checks and fixes:

- Python `aucell`, `binarize`, `regulon_specificity_scores`, and plotting helpers use cells x regulons.
- CLI text input with `--transpose` may also transpose stdout/text output in the command path; inspect the first column and header before feeding results downstream.
- Prefer explicit shape assertions: output index equals input cell IDs, output columns equal signature/regulon names.

## Loom Or h5ad Output Fails

Symptoms:

- CLI fails when writing `.loom` or `.h5ad` output.
- Metadata is missing or cell/gene attributes do not match expected names.
- h5ad output fails when input is not h5ad.

Checks and fixes:

- Loom output copies the input loom and appends AUC metadata; provide a valid loom expression input when writing loom output.
- h5ad output expects h5ad input and optional AnnData support.
- Verify cell and gene attribute names for loom input; defaults are `CellID` and `Gene`.
- For plain activity matrices, write CSV/TSV first and route detailed export/SCope/AnnData work to `../data-io-and-export/SKILL.md`.

## `threshold_overides` Keyword Error

Symptoms:

- Python raises `TypeError: binarize() got an unexpected keyword argument 'threshold_overrides'`.
- Manual threshold mappings are ignored because the wrong spelling was used.

Fix:

- Use the pySCENIC API spelling `threshold_overides`, with one `r` in `overides`.

```python
binary_mtx, thresholds = binarize(
    auc_mtx,
    threshold_overides={"MY_REGULON": 0.12},
    seed=13,
    num_workers=1,
)
```

## Unimodal Threshold Behavior Looks Too Conservative

Symptoms:

- Automated binarization marks no cells active for a regulon.
- The threshold is above nearly all observed AUC values.
- A histogram has one broad peak instead of two clear groups.

Explanation and fixes:

- `derive_threshold(..., method="hdt")` first checks for bimodality.
- If the AUC distribution is unimodal, pySCENIC returns `mean + 2 * std` instead of a Gaussian-mixture trough.
- Plot the distribution with `plot_binarization` and record whether the regulon lacks a clear on/off split.
- Use a manual `threshold_overides` value only when there is a defensible biological or external-threshold reason.
- Try `method="bic"` for diagnosis, but do not treat a different threshold as automatically better.

## RSS Values Are NaN Or Uninformative

Symptoms:

- `regulon_specificity_scores` produces NaN-like or flat values.
- Top RSS regulons do not correspond to any cell type.

Checks and fixes:

- Ensure `cell_type_series.index` uses the same cell IDs as `auc_mtx.index`.
- Reindex labels with `cell_type_series.reindex(auc_mtx.index)` so RSS receives labels in AUC row order.
- Remove all-zero or constant AUC columns before interpreting specificity.
- Confirm labels are not all the same cell type unless a single-type RSS summary is intentionally requested.
- RSS is a summary statistic, not a substitute for inspecting AUC distributions and binarized activity.

## Plotting Fails In Headless Runs

Symptoms:

- Matplotlib raises display/backend errors in CI or a terminal-only environment.
- Plot commands hang waiting for an interactive backend.

Fix:

- Set a non-interactive backend before importing `pyplot` in scripts.

```python
import matplotlib
matplotlib.use("Agg")
```

Then save figures to explicit output paths instead of calling interactive display functions.
