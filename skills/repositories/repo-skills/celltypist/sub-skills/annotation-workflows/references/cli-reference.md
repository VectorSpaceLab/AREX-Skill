# Annotation CLI Reference

The `celltypist` console script is appropriate when the user wants shell commands, table exports, or simple batch annotation. For in-memory `AnnData` objects, use the Python API in `api-reference.md`.

## Basic prediction

Create the output directory before running the CLI:

```bash
mkdir -p results
celltypist --indata query_counts.csv --model local_model.pkl --outdir results --quiet
```

Key flags:

- `-i, --indata FILE`: input count matrix (`.csv`, `.txt`, `.tsv`, `.tab`, `.mtx`) or `.h5ad`; genes should be gene symbols.
- `-m, --model TEXT`: model path or built-in model name. If omitted, CellTypist uses its default built-in model name and may need the model cache/network.
- `--transpose-input`: transpose gene-by-cell inputs so CellTypist can annotate cell-by-gene data.
- `-o, --outdir PATH`: output directory; defaults to current working directory but must already exist.
- `-p, --prefix TEXT`: prefix added to output filenames.
- `--quiet`: suppress banner/config logging.

Default table outputs when `--xlsx` is not set:

- `<prefix>predicted_labels.csv`
- `<prefix>decision_matrix.csv`
- `<prefix>probability_matrix.csv`

## Probability-match multi-label mode

CLI mode values use underscores, while the Python API uses spaces.

```bash
celltypist \
  --indata query_counts.csv \
  --model local_model.pkl \
  --mode prob_match \
  --p-thres 0.35 \
  --outdir results \
  --prefix sample_ \
  --quiet
```

- `--mode best_match` chooses the largest score/probability per cell.
- `--mode prob_match` labels each cell with every class whose probability is above `--p-thres`; no class over threshold becomes `Unassigned`.

## Matrix Market input

Both sidecar files are required for `.mtx` and `.mtx.gz`:

```bash
celltypist \
  --indata query.mtx \
  --model local_model.pkl \
  --gene-file genes.txt \
  --cell-file cells.txt \
  --outdir results \
  --quiet
```

For gene-by-cell Matrix Market files:

```bash
celltypist \
  --indata query_gene_by_cell.mtx \
  --model local_model.pkl \
  --transpose-input \
  --gene-file genes.txt \
  --cell-file cells.txt \
  --outdir results \
  --quiet
```

If CellTypist reports sidecar length mismatches, check orientation first; the sidecar lengths must match the matrix dimensions after applying `--transpose-input` semantics.

## `.h5ad` input

```bash
celltypist --indata query.h5ad --model local_model.pkl --outdir results --quiet
```

`.h5ad` must contain log1p-normalized expression to 10,000 counts per cell in `.X` or valid `.raw.X`. Raw-count `.h5ad` files should be normalized before CLI annotation or converted to a raw count table for CellTypist's table loader.

## Majority voting

Automatic over-clustering:

```bash
celltypist \
  --indata query_counts.csv \
  --model local_model.pkl \
  --majority-voting \
  --outdir results \
  --quiet
```

Precomputed over-clustering file:

```bash
celltypist \
  --indata query_counts.csv \
  --model local_model.pkl \
  --majority-voting \
  --over-clustering clusters.txt \
  --min-prop 0.2 \
  --outdir results \
  --quiet
```

- `--over-clustering` can be a file with one cluster assignment per cell or an `.obs` column name when input is `.h5ad`.
- `--over-clustering auto` is the CLI default and maps to Python `over_clustering=None`.
- `--use-GPU` only affects automatic over-clustering and requires `rapids_singlecell`; CellTypist warns and switches to CPU if it is unavailable.
- Majority voting is skipped for inputs with 50 or fewer cells.

## Excel and plotting flags

```bash
celltypist \
  --indata query_counts.csv \
  --model local_model.pkl \
  --outdir results \
  --prefix run1_ \
  --xlsx \
  --quiet
```

- `--xlsx` writes a single `<prefix>annotation_result.xlsx` with predicted labels, decision matrix, and probability matrix sheets.
- `--plot-results` also generates figures and may compute neighbors/UMAP; route plot-focused decisions to `../visualization-and-results/SKILL.md`.

## Model listing and updating

These commands are model-management tasks, not annotation tasks:

```bash
celltypist --show-models
celltypist --update-models
```

They may contact the remote model server or rely on the model cache. Route cache, download, and offline model setup to `../model-management/SKILL.md`.
