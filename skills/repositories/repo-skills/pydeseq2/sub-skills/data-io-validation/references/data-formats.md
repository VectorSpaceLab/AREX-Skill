# PyDESeq2 Data Formats

PyDESeq2 expects count data and sample metadata to be aligned before any modeling. Validate this layer before routing to full DEA workflows.

## Installation And Imports

PyDESeq2 requires Python 3.11 or newer and can be installed with a generic package command:

```bash
pip install pydeseq2
```

Common imports for data preparation are:

```python
import pandas as pd
from anndata import AnnData
from pydeseq2.dds import DeseqDataSet
from pydeseq2.utils import load_example_data
```

## Count Matrix Schema

- Shape: samples x genes.
- Rows: sample identifiers such as `sample1`, `sample2`; the index must be unique.
- Columns: gene identifiers such as `gene1`, `gene2`; column names should be unique.
- Values: raw read counts as numeric, finite, integer, non-negative values.
- Avoid normalized, transformed, TPM/FPKM, negative, fractional, string, or missing values in `counts`.

If a CSV has genes as rows and samples as columns, load it with `index_col=0` and transpose:

```python
counts_df = pd.read_csv("counts.csv", index_col=0).T
```

If a CSV is already samples x genes, do not transpose:

```python
counts_df = pd.read_csv("counts.csv", index_col=0)
```

## Metadata Schema

- Shape: samples x variables.
- Rows: the same sample identifiers as `counts_df.index`.
- Columns: design variables such as `condition`, `group`, `batch`, or continuous covariates.
- Values: no missing values in columns used by the design formula or direct design matrix.

Align only after checking the same sample ids are present:

```python
missing_in_metadata = counts_df.index.difference(metadata.index)
missing_in_counts = metadata.index.difference(counts_df.index)
if len(missing_in_metadata) or len(missing_in_counts):
    raise ValueError("counts and metadata do not contain the same sample ids")
metadata = metadata.loc[counts_df.index]
```

## Built-In Synthetic Example

`load_example_data(modality="raw_counts", dataset="synthetic", debug=False, debug_seed=42)` returns a `pandas.DataFrame` of raw counts with samples x genes orientation. For PyDESeq2 0.5.4, the synthetic counts shape is `(100, 10)`.

`load_example_data(modality="metadata", dataset="synthetic", debug=False, debug_seed=42)` returns metadata with shape `(100, 2)` and columns `condition` and `group`.

Use the loader for quick API exploration. Use `scripts/validate_pydeseq2_inputs.py --use-synthetic` or `scripts/run_local_csv_dea.py --use-synthetic` when you want the bundled scripts' deterministic, network-free in-memory fixture.

## Filtering Before Construction

For formula designs, remove samples with missing design values before constructing `DeseqDataSet`:

```python
design_columns = ["condition"]
samples_to_keep = ~metadata[design_columns].isna().any(axis=1)
counts_df = counts_df.loc[samples_to_keep]
metadata = metadata.loc[samples_to_keep]
```

Low-count genes can be filtered before fitting. A common smoke-test threshold is total count >= 10:

```python
genes_to_keep = counts_df.columns[counts_df.sum(axis=0) >= 10]
counts_df = counts_df.loc[:, genes_to_keep]
```

Do not remove all genes. If a threshold is too strict, lower it or inspect library sizes and gene totals.

## Formula Designs

`DeseqDataSet` accepts a Wilkinson/formulaic formula string through `design`, with default `"~condition"`.

```python
dds = DeseqDataSet(counts=counts_df, metadata=metadata, design="~condition")
```

Rules:

- Every variable named in the formula must exist as a metadata column.
- Missing values in used columns must be filtered or imputed before construction.
- One-level categorical factors and rank-deficient combinations may construct with warnings, but full differential expression fitting cannot be trusted until the design is fixed.
- For multi-factor workflows such as `"~group + condition"`, confirm the intended coefficient/contrast route in `../statistics-and-results/SKILL.md` after fitting.

## Direct Design Matrices

`DeseqDataSet` also accepts `design=<pandas.DataFrame>`.

```python
design_matrix = pd.DataFrame(
    {"intercept": 1.0, "condition_B_vs_A": [0, 1, 0, 1]},
    index=counts_df.index,
)
dds = DeseqDataSet(counts=counts_df, metadata=metadata, design=design_matrix)
```

Rules:

- The design matrix index must exactly equal `counts_df.index` and `metadata.index` after alignment.
- The number of rows must equal the number of samples.
- Values must be numeric and free of missing values.
- The matrix should be full column rank; otherwise PyDESeq2 warns that DEA fitting is not valid.
- Downstream statistics with direct design matrices usually need numeric contrast vectors rather than formula factor triplets; route contrast selection to `../statistics-and-results/SKILL.md`.

## AnnData Initialization

Use `AnnData` when data is already in single-cell-style containers or when passing preassembled `X` and `obs`:

```python
adata = AnnData(X=counts_df.astype(int), obs=metadata)
dds = DeseqDataSet(adata=adata, design="~condition")
```

Rules:

- `adata.X` must follow the same count-value rules as `counts_df`.
- `adata.obs` must hold metadata indexed by samples.
- If `adata` is provided, `counts` and `metadata` keyword arguments are ignored by PyDESeq2.

## Picklable Export

After fitting or constructing a `DeseqDataSet`, use `to_picklable_anndata()` when the object must be serialized:

```python
adata_for_pickle = dds.to_picklable_anndata()
```

The exported `AnnData` preserves fields such as `X`, `obs`, `obsm`, `var`, `varm`, `uns`, and `layers`, while making the design matrix picklable.

## Bundled Script Recipes

The bundled scripts adapt the package's pandas CSV I/O flow into self-contained helpers: they require explicit local CSV paths or `--use-synthetic`, never download example data, and keep full DEA/statistics choices routed to sibling sub-skills.

Validate local CSVs with automatic orientation detection:

```bash
python sub-skills/data-io-validation/scripts/validate_pydeseq2_inputs.py \
  --counts-csv counts.csv \
  --metadata-csv metadata.csv \
  --design '~condition' \
  --orientation auto \
  --min-gene-total 10
```

Validate genes x samples counts by forcing transpose:

```bash
python sub-skills/data-io-validation/scripts/validate_pydeseq2_inputs.py \
  --counts-csv counts.csv \
  --metadata-csv metadata.csv \
  --orientation genes-by-samples \
  --design '~condition'
```

Check a direct design matrix CSV:

```bash
python sub-skills/data-io-validation/scripts/validate_pydeseq2_inputs.py \
  --counts-csv counts.csv \
  --metadata-csv metadata.csv \
  --design-matrix-csv design_matrix.csv
```

Construct a `DeseqDataSet` from local CSVs and optionally export a picklable `AnnData` after a smoke fit:

```bash
python sub-skills/data-io-validation/scripts/run_local_csv_dea.py \
  --counts-csv counts.csv \
  --metadata-csv metadata.csv \
  --orientation auto \
  --design '~condition' \
  --run-deseq2 \
  --export-picklable-anndata fitted_adata.pkl
```
