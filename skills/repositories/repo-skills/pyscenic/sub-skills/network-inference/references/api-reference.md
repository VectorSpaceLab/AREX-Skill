# Network Inference API Reference

## Purpose

Use this reference when a task needs Python-level pySCENIC network inference support: adding TF-target correlations, building TF-target modules from an adjacency table, or translating CLI options into API calls. Facts here are distilled from the installed package signatures and source evidence for `pyscenic.utils` and `pyscenic.math`.

## Core Data Contracts

### Expression Matrix

- Python APIs expect a `pandas.DataFrame` shaped `n_cells x n_genes`.
- Rows are cells and columns are gene symbols. CSV/TSV CLI inputs follow the same convention by default.
- If a CSV/TSV file is stored as genes-by-cells, use `--transpose` on `pyscenic grn` and `pyscenic add_cor`, or transpose the DataFrame before using Python APIs.
- Loom files are naturally stored as genes-by-cells, but pySCENIC loads them into the same cells-by-genes DataFrame contract for non-sparse operations.
- Duplicate expression columns are removed inside `modules_from_adjacencies()` by keeping the first duplicate gene before calculating modules.

### Adjacency Table

`add_correlation()` and `modules_from_adjacencies()` expect these columns:

| Column | Meaning |
| --- | --- |
| `TF` | Transcription factor name. Must be present as a gene column in the expression matrix for correlation/module generation. |
| `target` | Target gene name. Must also be present in the expression matrix. |
| `importance` | Arboreto link weight from GRNBoost2 or GENIE3. |

`add_correlation()` returns a new DataFrame with:

| Column | Meaning |
| --- | --- |
| `TF` | Original TF. |
| `target` | Original target. |
| `importance` | Original link weight. |
| `regulation` | `1` for activation, `-1` for repression, `0` for weak/undetermined correlation. |
| `rho` | Pearson correlation between TF and target expression. |

## `add_correlation()`

Verified signature:

```python
add_correlation(adjacencies, ex_mtx, rho_threshold=0.03, mask_dropouts=False)
```

Behavior:

- Computes Pearson correlation for each TF-target pair in `adjacencies`.
- Marks activation when `rho > rho_threshold`, repression when `rho < -rho_threshold`, and neutral otherwise.
- Requires `rho_threshold > 0`.
- With `mask_dropouts=False`, correlations use all cells and are computed from a correlation matrix over genes present in the adjacency table.
- With `mask_dropouts=True`, cells where either the TF or target expression equals zero are excluded for that pair, using the masked correlation implementation in `pyscenic.math`.
- Missing TF or target genes in the expression matrix are a hard data issue. Validate gene overlap before calling this API.

Minimal pattern:

```python
import pandas as pd
from pyscenic.utils import add_correlation

ex_mtx = pd.read_csv("expression_cells_by_genes.csv", index_col=0)
adjacencies = pd.read_csv("adjacencies.csv")
with_rho = add_correlation(adjacencies, ex_mtx, rho_threshold=0.03, mask_dropouts=True)
with_rho.to_csv("adjacencies_with_rho.csv", index=False)
```

## `modules_from_adjacencies()`

Verified signature:

```python
modules_from_adjacencies(
    adjacencies,
    ex_mtx,
    thresholds=(0.75, 0.9),
    top_n_targets=(50,),
    top_n_regulators=(5, 10, 50),
    min_genes=20,
    absolute_thresholds=False,
    rho_dichotomize=True,
    keep_only_activating=True,
    rho_threshold=0.03,
    rho_mask_dropouts=False,
)
```

Behavior:

- Builds candidate TF-target modules from weighted adjacency links using three families of selection rules:
  - `thresholds`: per-TF modules above weight quantiles by default.
  - `top_n_targets`: top targets per TF by `importance`.
  - `top_n_regulators`: targets where a TF is among the top regulators for the target gene.
- Adds the transcription factor itself to each module.
- Filters out modules smaller than `min_genes` after adding the TF.
- Converts the expression matrix to floating point and removes duplicate gene columns by keeping the first occurrence.
- When `absolute_thresholds=False`, `thresholds` values are quantiles. For example, `0.75` means the 75th percentile of `importance`, not an absolute weight cutoff.
- When `absolute_thresholds=True`, `thresholds` values are direct `importance` cutoffs.
- When `rho_dichotomize=True`, the function uses existing `regulation` and `rho` columns if present; otherwise it computes them using `add_correlation()`.
- When `keep_only_activating=True`, only positively correlated targets become modules. Set `keep_only_activating=False` to include repressing modules too.
- `rho_mask_dropouts` controls dropout masking only when correlations are calculated inside `modules_from_adjacencies()`.

Minimal activating-only pattern:

```python
import pandas as pd
from pyscenic.utils import modules_from_adjacencies

ex_mtx = pd.read_csv("expression_cells_by_genes.csv", index_col=0)
adjacencies = pd.read_csv("adjacencies.csv")
modules = modules_from_adjacencies(adjacencies, ex_mtx, min_genes=20)
```

Pattern for both activating and repressing modules with dropout-masked correlations:

```python
modules = modules_from_adjacencies(
    adjacencies,
    ex_mtx,
    thresholds=(0.75, 0.9),
    top_n_targets=(50,),
    top_n_regulators=(5, 10, 50),
    min_genes=20,
    keep_only_activating=False,
    rho_mask_dropouts=True,
)
```

## Correlation Details

- pySCENIC uses Pearson correlation, not Spearman correlation, for TF-target activation/repression labels.
- The default dropout behavior changed from older pySCENIC releases: current defaults use all cells (`mask_dropouts=False` and `rho_mask_dropouts=False`) to match the R SCENIC behavior.
- Dropout masking can change both the sign and magnitude of `rho`, especially for sparse single-cell matrices with many zeros.
- If `add_correlation()` receives a pair where all non-zero paired observations vanish after masking or one side has zero variance, the underlying masked correlation can return `NaN`.

## API Versus CLI Mapping

| CLI option | Python API equivalent |
| --- | --- |
| `pyscenic add_cor --mask_dropouts` | `add_correlation(..., mask_dropouts=True)` |
| `pyscenic ctx --mask_dropouts` when input is adjacencies and an expression matrix is supplied | `modules_from_adjacencies(..., rho_mask_dropouts=True)` |
| `pyscenic ctx --thresholds 0.75 0.9` | `modules_from_adjacencies(..., thresholds=(0.75, 0.9))` |
| `pyscenic ctx --top_n_targets 50` | `modules_from_adjacencies(..., top_n_targets=(50,))` |
| `pyscenic ctx --top_n_regulators 5 10 50` | `modules_from_adjacencies(..., top_n_regulators=(5, 10, 50))` |
| `pyscenic ctx --min_genes 20` | `modules_from_adjacencies(..., min_genes=20)` |
| `pyscenic ctx --all_modules` | `modules_from_adjacencies(..., keep_only_activating=False)` |

The `ctx` command also performs motif enrichment/pruning and belongs to the motif-pruning workflow. Use this sub-skill only for the module-generation part of that command.

## Safety Checks Before API Calls

Before calling these APIs for a user dataset, check:

1. Expression matrix columns are gene symbols and rows are cells.
2. `adjacencies` has exactly the expected semantic columns: `TF`, `target`, and `importance`.
3. All TF and target genes in `adjacencies` are present in `ex_mtx.columns` before correlation/module generation.
4. `importance` is numeric and not a string column accidentally loaded from a malformed separator.
5. Duplicate expression genes are intentional; if duplicates exist, document that pySCENIC keeps the first duplicate during module generation.
6. `min_genes` is small enough for synthetic or tiny fixtures; the production default of `20` often filters out toy modules.
