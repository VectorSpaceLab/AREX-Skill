# Network Inference Troubleshooting

## Purpose

Use this reference when pySCENIC GRN inference, correlation annotation, or module construction gives surprising warnings, empty outputs, or runtime errors. It focuses on the `grn`, `add_cor`, `arboreto_with_multiprocessing.py`, `add_correlation()`, and `modules_from_adjacencies()` surfaces.

## Fast Triage

1. Run the bundled helper with `--help` to confirm the helper itself is available.
2. Run the helper without options to check pySCENIC/Arboreto imports and command availability.
3. If you need deterministic toy inputs, run it with `--make-fixtures DIR --run-api-smoke`.
4. Validate expression orientation and gene overlap before rerunning expensive GRNBoost2 or GENIE3 inference.
5. Lower `min_genes` only for toy/smoke module tests; keep production thresholds biologically justified.

```bash
python scripts/grn_multiprocessing_smoke.py --make-fixtures ./pyscenic-grn-smoke --run-api-smoke
```

## TF List and Expression Gene Mismatch

Symptoms:

- `pyscenic grn` warns that expression data is available for less than 80% of the supplied transcription factors.
- GRN output has unexpectedly few TFs.
- Arboreto reports invalid or missing TF names.

Likely causes:

- TF list species does not match the expression matrix species.
- Expression gene symbols use Ensembl IDs, versioned IDs, aliases, or mixed case while the TF list uses symbols.
- CSV/TSV orientation is wrong, so cells are being treated as genes.
- The expression matrix was prefiltered and removed most TFs.

Recovery:

- Count overlap between `set(expression.columns)` and the TF list before running GRN.
- Confirm CSV/TSV orientation; add `--transpose` only when rows are genes and columns are cells.
- Use a TF list with the same organism and identifier namespace as the expression matrix.
- If the low overlap is intentional after filtering, document it and consider a targeted TF list instead of the full species list.

## Wrong CSV/TSV/Loom Orientation

Symptoms:

- pySCENIC says the expression matrix contains no genes.
- TF overlap is nearly zero.
- Output gene names look like cell barcodes.
- Correlation/module APIs complain about genes missing from the expression matrix.

Likely causes:

- CSV/TSV is genes-by-cells but `--transpose` was omitted.
- CSV/TSV is already cells-by-genes but `--transpose` was added.
- Loom row/column attributes do not use the default `Gene` and `CellID` names.

Recovery:

- For CSV/TSV, inspect the header and first column. pySCENIC expects cells as rows and genes as columns by default.
- Add `--transpose` only for genes-by-cells CSV/TSV files.
- For loom files, pass the correct `--gene_attribute` and `--cell_id_attribute` values.
- For Python APIs, always pass a DataFrame with cells as rows and genes as columns.

## Duplicate or Missing Genes

Symptoms:

- `modules_from_adjacencies()` raises an assertion that genes are present in the network but missing from the expression matrix.
- Correlation results contain unexpected `NaN` values.
- Duplicate gene columns lead to non-reproducible or surprising module membership.

Likely causes:

- Adjacency rows reference genes not present in `ex_mtx.columns`.
- Gene names changed between GRN inference and module construction.
- Expression matrix contains duplicate gene columns.

Recovery:

- Use the same expression matrix for `grn`, `add_cor`, and module construction whenever possible.
- Check `set(adjacencies.TF).union(adjacencies.target) - set(ex_mtx.columns)` before calling APIs.
- Resolve duplicate genes upstream. If duplicates remain, remember `modules_from_adjacencies()` keeps the first duplicate gene column during module construction.
- Do not silently drop missing genes from adjacencies unless the user explicitly accepts the biological consequences.

## Sparse and Loom Limitations

Symptoms:

- Sparse loom loading works for `pyscenic grn --sparse` but not for `pyscenic add_cor` or module construction.
- Dense conversion causes high memory use.
- API code expects a DataFrame but receives a sparse matrix tuple.

Likely causes:

- Sparse loading is implemented for GRN inference, while `add_cor` and module generation load dense expression matrices.
- Python APIs require a cells-by-genes DataFrame for correlation/module logic.

Recovery:

- Use `--sparse` only for the GRN step when the expression file is loom or another supported sparse-capable input.
- For `add_cor` and `modules_from_adjacencies()`, prepare a dense, filtered expression matrix with genes needed by the adjacency table.
- If memory is the problem, prefilter to the union of TFs and targets in the adjacency table before correlation/module construction.

## Dask Client Mode Mistakes

Symptoms:

- `pyscenic grn` hangs or fails while creating a Dask client.
- Workers cannot read expression or TF files.
- A scheduler address works interactively but pySCENIC jobs fail on worker nodes.

Likely causes:

- `--client_or_address` points to an unreachable or incompatible scheduler.
- Workers do not share access to the same input/output filesystem.
- `--num_workers` exceeds available CPU or memory.

Recovery:

- Start with local mode and a conservative `--num_workers`.
- For external schedulers, verify worker file access and package versions before launching GRN inference.
- Use `arboreto_with_multiprocessing.py` when the task only needs local multi-process execution and Dask is the unstable layer.

## Custom Multiprocessing Limitations

Symptoms:

- `arboreto_with_multiprocessing.py` works locally but cannot distribute across nodes.
- Large runs are slower or memory-constrained compared with a correctly configured Dask cluster.
- Multiprocessing command fails because the executable is not on `PATH`.

Likely causes:

- The fallback uses Python `multiprocessing.Pool`, not Dask.
- The installed package exposes the script only in environments where console scripts are correctly installed.
- Worker count is too high for local memory.

Recovery:

- Treat the fallback as a single-machine stability option.
- Run the bundled helper to check whether `arboreto_with_multiprocessing.py` is on `PATH`.
- Reduce `--num_workers` when memory pressure or process spawning is the failure mode.
- If the executable is missing but imports work, call the installed script through the environment's script discovery mechanism or reinstall pySCENIC so console scripts are created.

## Missing Genes in Correlations

Symptoms:

- `modules_from_adjacencies()` raises an assertion about genes in adjacencies missing from expression.
- `add_correlation()` fails during lookup or produces correlations for fewer genes than expected.

Likely causes:

- Adjacencies and expression matrix came from different preprocessing stages.
- Separator inference loaded the adjacency table incorrectly, so columns are not `TF`, `target`, and `importance`.
- Gene identifiers were renamed after GRN inference.

Recovery:

- Load adjacency files with the correct delimiter (`.csv` comma, `.tsv` tab).
- Validate required columns and data types before correlation.
- Recreate adjacencies from the same expression matrix when identifiers have changed.
- For diagnostics only, report the first missing genes and stop; do not auto-edit biological identifiers.

## Dropout Masking Behavior Changed

Symptoms:

- Results differ from older pySCENIC runs even with similar inputs.
- Activating/repressing labels change when `--mask_dropouts` is toggled.
- Very sparse data produces different module membership than expected.

Likely causes:

- Current pySCENIC defaults use all cells for correlation. Older pySCENIC behavior masked cells where either TF or target expression was zero.
- Dropout masking can change Pearson correlation sign and magnitude.

Recovery:

- For CLI correlation, set `pyscenic add_cor --mask_dropouts` when reproducing older masked behavior.
- For Python, set `add_correlation(..., mask_dropouts=True)`.
- For modules that compute correlations internally, set `modules_from_adjacencies(..., rho_mask_dropouts=True)`.
- Record the chosen masking setting in downstream analysis notes because it affects module and regulon composition.

## `min_genes` Filtering Removes Modules

Symptoms:

- `modules_from_adjacencies()` returns an empty list for a toy fixture or narrow TF subset.
- `ctx` later reports no modules or no loaded modules.

Likely causes:

- Default `min_genes=20` is appropriate for real modules but too strict for tiny synthetic examples.
- Correlation filtering keeps only activating modules and removes most links.
- Threshold/top-N settings are too narrow for the adjacency table.

Recovery:

- For smoke tests, use `min_genes=2` or another explicitly documented toy threshold.
- For production, inspect adjacency counts per TF before lowering `min_genes`.
- Set `keep_only_activating=False` when repressing modules are intentionally part of the analysis.
- Broaden `top_n_targets`, `top_n_regulators`, or threshold choices only when justified by the task.

## Empty or Malformed Output Files

Symptoms:

- Output file is empty or uses the wrong delimiter.
- Downstream loading treats the whole row as one column.
- `importance` is loaded as a string.

Likely causes:

- Output suffix does not match intended delimiter.
- `.csv` and `.tsv` files were mixed without changing reader settings.
- A command wrote to stdout when `-o` was omitted and logs were captured instead.

Recovery:

- Use `.csv` for comma-separated output and `.tsv` for tab-separated output.
- Always pass `-o`/`--output` for long-running GRN commands.
- Validate that adjacency files have `TF`, `target`, and `importance` columns before correlation or module construction.

## When To Stop and Ask

Stop and ask the user before proceeding when:

- Gene identifier conversion requires biological decisions such as organism, transcript-to-gene aggregation, or alias mapping.
- The only available fix requires downloading TF lists, motif databases, or large resources.
- Cluster/Dask scheduler details, shared filesystem mounts, or hardware limits are unknown.
- A run would launch expensive GRNBoost2/GENIE3 inference rather than just creating templates or smoke fixtures.
