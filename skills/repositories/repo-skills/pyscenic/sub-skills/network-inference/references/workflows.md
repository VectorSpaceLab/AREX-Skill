# Network Inference Workflows

## Purpose

Use this reference to construct practical pySCENIC Phase I workflows: infer weighted TF-target adjacencies with GRNBoost2 or GENIE3, add correlations, use the Dask-free multiprocessing fallback, and build modules for downstream motif pruning. Commands assume pySCENIC is installed and available on `PATH`.

## Input Checklist

Prepare these inputs before network inference:

- Expression matrix:
  - CSV/TSV: cells as rows and genes as columns by default, with the first column used as the row index.
  - CSV/TSV genes-by-cells: add `--transpose`.
  - Loom: rows are genes and columns are cells; pySCENIC uses `Gene` and `CellID` attributes by default.
- TF list: plain text with one transcription factor per line.
- Output adjacency path: `.csv` or `.tsv`; pySCENIC chooses the delimiter from the output suffix.
- Worker count and seed: set `--num_workers` to a bounded local value and `--seed` when reproducibility matters.

Run the bundled smoke helper to confirm imports and generate tiny fixtures/templates:

```bash
python scripts/grn_multiprocessing_smoke.py --make-fixtures ./pyscenic-grn-smoke --run-api-smoke
```

## Infer Adjacencies With `pyscenic grn`

GRNBoost2 is the default:

```bash
pyscenic grn \
  --method grnboost2 \
  --num_workers 8 \
  --seed 777 \
  -o adjacencies.tsv \
  expression_cells_by_genes.csv \
  tfs.txt
```

Use GENIE3 when the task explicitly asks for random-forest GENIE3 inference:

```bash
pyscenic grn \
  --method genie3 \
  --num_workers 8 \
  --seed 777 \
  -o adjacencies.tsv \
  expression_cells_by_genes.csv \
  tfs.txt
```

For genes-by-cells CSV/TSV input:

```bash
pyscenic grn \
  --transpose \
  --method grnboost2 \
  --num_workers 8 \
  --seed 777 \
  -o adjacencies.tsv \
  expression_genes_by_cells.tsv \
  tfs.txt
```

For loom input with default attributes:

```bash
pyscenic grn \
  --method grnboost2 \
  --num_workers 8 \
  --seed 777 \
  -o adjacencies.tsv \
  expression.loom \
  tfs.txt
```

For loom input with custom attributes:

```bash
pyscenic grn \
  --gene_attribute Gene \
  --cell_id_attribute CellID \
  --method grnboost2 \
  --num_workers 8 \
  --seed 777 \
  -o adjacencies.tsv \
  expression.loom \
  tfs.txt
```

### Dask Client Modes

`pyscenic grn` accepts `--client_or_address` and `--num_workers`:

- `--client_or_address local` is the default and asks pySCENIC to prepare a local Dask client.
- A scheduler address can be supplied when the environment already has a Dask scheduler reachable by all workers.
- `--num_workers` applies to local client preparation and should match available CPU and memory limits.

If Dask setup is unreliable or cluster workers cannot access the same files, use the multiprocessing fallback below.

## Dask-Free Arboreto Multiprocessing Fallback

The installed pySCENIC package exposes `arboreto_with_multiprocessing.py`. It runs Arboreto GRNBoost2 or GENIE3 through Python multiprocessing instead of Dask. It cannot distribute work across multiple nodes, but it is useful when Dask is the failure source.

```bash
arboreto_with_multiprocessing.py \
  --method grnboost2 \
  --num_workers 8 \
  --seed 777 \
  --output adjacencies.tsv \
  expression_cells_by_genes.csv \
  tfs.txt
```

GENIE3 fallback:

```bash
arboreto_with_multiprocessing.py \
  --method genie3 \
  --num_workers 8 \
  --seed 777 \
  --output adjacencies.tsv \
  expression_cells_by_genes.csv \
  tfs.txt
```

The fallback accepts the same expression orientation controls as `pyscenic grn`: `--transpose`, `--sparse`, `--gene_attribute`, and `--cell_id_attribute`.

## Add Correlations With `pyscenic add_cor`

Use this when a task asks to inspect activation/repression before motif pruning or when an adjacency file needs explicit `rho` and `regulation` columns:

```bash
pyscenic add_cor \
  --mask_dropouts \
  -o adjacencies_with_rho.csv \
  adjacencies.tsv \
  expression_cells_by_genes.csv
```

For genes-by-cells CSV/TSV expression input:

```bash
pyscenic add_cor \
  --transpose \
  --mask_dropouts \
  -o adjacencies_with_rho.csv \
  adjacencies.tsv \
  expression_genes_by_cells.tsv
```

Notes:

- `--mask_dropouts` uses only cells where both TF and target expression are non-zero for the correlation calculation.
- Without `--mask_dropouts`, current pySCENIC defaults use all cells.
- Sparse loading is disabled for `add_cor`; use dense-compatible inputs or pre-filter before this step.

## Build Modules in Python

Use Python when a task asks for precise threshold/top-N/min-gene control without running motif pruning:

```python
import pandas as pd
from pyscenic.utils import add_correlation, modules_from_adjacencies

ex_mtx = pd.read_csv("expression_cells_by_genes.csv", index_col=0)
adjacencies = pd.read_csv("adjacencies.tsv", sep="\t")

with_rho = add_correlation(adjacencies, ex_mtx, mask_dropouts=True)
modules = modules_from_adjacencies(
    with_rho,
    ex_mtx,
    thresholds=(0.75, 0.9),
    top_n_targets=(50,),
    top_n_regulators=(5, 10, 50),
    min_genes=20,
    keep_only_activating=True,
)
```

To include repressing modules:

```python
modules = modules_from_adjacencies(
    with_rho,
    ex_mtx,
    min_genes=20,
    keep_only_activating=False,
)
```

For tiny smoke fixtures, lower `min_genes` so modules are not filtered out:

```python
modules = modules_from_adjacencies(with_rho, ex_mtx, min_genes=2, keep_only_activating=False)
```

## Build Modules Through `pyscenic ctx` Without Owning Motif Pruning

The `ctx` command can create modules internally when its first input is an adjacency table and `--expression_mtx_fname` is supplied. Full motif pruning is outside this sub-skill, but these options map to module construction:

```bash
pyscenic ctx \
  adjacencies.tsv \
  ranking_database.feather \
  --annotations_fname motif_annotations.tbl \
  --expression_mtx_fname expression_cells_by_genes.csv \
  --thresholds 0.75 0.9 \
  --top_n_targets 50 \
  --top_n_regulators 5 10 50 \
  --min_genes 20 \
  --mode custom_multiprocessing \
  --num_workers 8 \
  -o regulons.csv
```

Use the motif-pruning workflow for database selection, annotations, pruning thresholds, output regulon formats, and RcisTarget troubleshooting.

## Low TF-Overlap Diagnostic Recipe

When `pyscenic grn` warns that expression data is available for less than 80% of the supplied transcription factors, inspect overlap before rerunning expensive inference:

```python
import pandas as pd

ex_mtx = pd.read_csv("expression_cells_by_genes.csv", index_col=0)
with open("tfs.txt") as handle:
    tf_names = [line.strip() for line in handle if line.strip()]

genes = set(ex_mtx.columns)
present = [tf for tf in tf_names if tf in genes]
missing = [tf for tf in tf_names if tf not in genes]
print(f"TF overlap: {len(present)}/{len(tf_names)} = {len(present) / max(len(tf_names), 1):.1%}")
print("First missing TFs:", missing[:20])
```

Common fixes are matching gene symbol conventions, using the correct species TF list, removing version suffixes only when biologically valid, and confirming that CSV/TSV orientation was not inverted.

## Source Script Handling

- `arboreto_with_multiprocessing.py` is represented as the recommended Dask-free fallback workflow and by the bundled smoke/template helper.
- `cli_test_script.sh` supplied useful GRN CLI examples, but it includes external database/resource paths and non-network phases, so only the safe GRN/add_cor patterns were distilled here.
- HPC-specific GRNBoost scripts/configs are reference evidence only. They assume scheduler and filesystem paths that should not be published as runnable skill helpers.
