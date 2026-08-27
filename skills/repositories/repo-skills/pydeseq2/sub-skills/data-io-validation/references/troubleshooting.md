# Data I/O Troubleshooting

Use this reference to diagnose failures before full PyDESeq2 modeling. Fix input data and design structure first, then route fitting/statistics questions to sibling sub-skills.

## Count Matrix Failures

| Symptom | Likely Cause | Recovery |
| --- | --- | --- |
| `NaNs are not allowed in the count matrix.` | Missing values in the count table. | Re-export raw counts, fill only if biologically justified, or drop affected genes/samples; do not pass missing counts to PyDESeq2. |
| `The count matrix should only contain numbers.` | CSV columns loaded as strings because of labels, comments, thousands separators, or mixed values. | Load with `index_col=0`, inspect non-numeric cells, remove non-count columns, then coerce only true count columns. |
| `The count matrix should only contain integers.` | Fractional values, normalized abundances, TPM/FPKM, or decimal CSV formatting. | Use raw integer read counts. Rounding normalized values is not a valid substitute. |
| `The count matrix should only contain non-negative values.` | Negative values from transformed data, subtraction, or malformed export. | Use raw counts before transforms; inspect upstream pipeline. |
| AnnData shape/index errors during `DeseqDataSet(...)` | Counts and metadata sample indexes differ or are ordered differently. | Compare `counts.index` and `metadata.index`, fix sample ids, then reorder metadata with `metadata.loc[counts.index]`. |
| Many index mismatches after CSV loading | Counts are genes x samples, but PyDESeq2 expects samples x genes. | Transpose counts or rerun validator with `--orientation genes-by-samples` or `--orientation auto`. |

## Metadata And Formula Failures

| Symptom | Likely Cause | Recovery |
| --- | --- | --- |
| Formula column missing or formulaic errors mentioning an unknown variable | The formula references a metadata column that does not exist. | Check spelling and case; use `metadata.columns`; update the formula or rename metadata columns. |
| `NaNs are not allowed in the design.` | A column used by `design` contains missing values, or a direct design matrix has missing values. | Filter samples with missing design values before construction: `metadata[design_columns].isna().any(axis=1)`. |
| One-level factor warning | A categorical design variable has only one observed level after filtering. | Add samples from the missing level, use a different design variable, or remove the factor; DEA contrasts require comparison information. |
| Rank-deficient design warning | Design columns are linear combinations of each other, or factors are perfectly confounded. | Remove redundant variables, merge sparse levels, simplify the formula, or collect a design with independent batch/condition structure. |
| Fitting fails after a warning about rank or too many variables | The design has as many or more effective columns than samples, or lacks full rank. | Reduce design complexity before running `dds.deseq2()`; validation can warn but cannot make the model estimable. |

## Direct Design Matrix Failures

| Symptom | Likely Cause | Recovery |
| --- | --- | --- |
| Error when `design` is a `DataFrame` | Design matrix index or length does not match samples. | Ensure `design_matrix.index.equals(counts.index)` and one row per sample. |
| `NaNs are not allowed in the design.` | Missing value in direct design matrix. | Impute intentionally or drop affected samples before constructing `DeseqDataSet`. |
| Rank-deficient design warning | Intercept/dummy columns are duplicated or confounded. | Drop one redundant dummy column or rebuild the matrix with a single intercept and independent covariates. |
| Later contrast code cannot use `['condition', 'B', 'A']` | Direct matrix designs do not carry formulaic factor metadata in the same way. | Use numeric contrast vectors and route details to `../statistics-and-results/SKILL.md`. |

## Orientation Decision Guide

- If `counts.index` overlaps strongly with `metadata.index`, counts are probably samples x genes.
- If `counts.columns` overlaps strongly with `metadata.index`, counts are probably genes x samples and should be transposed.
- If both overlap poorly, sample ids may be formatted differently; fix identifiers rather than forcing a transpose.
- If both overlap well, the dataset may have ambiguous sample/gene names; require the user to confirm orientation.

The validator reports overlap counts and selected orientation so agents can explain mismatch failures instead of silently transposing the wrong table.

## Low-Count Gene Filtering

Filtering genes with very low total counts is usually performed before fitting:

```python
genes_to_keep = counts_df.columns[counts_df.sum(axis=0) >= 10]
counts_df = counts_df.loc[:, genes_to_keep]
```

If all genes are filtered out, lower the threshold or inspect whether counts were oriented incorrectly. A genes x samples table interpreted as samples x genes can make gene totals meaningless.

## Network-Free Local CSV Use

Do not use example defaults that download CSVs from the internet. The bundled `run_local_csv_dea.py` requires explicit local `--counts-csv` and `--metadata-csv`, or `--use-synthetic` for PyDESeq2's installed synthetic loader.

Recommended local smoke commands:

```bash
python sub-skills/data-io-validation/scripts/validate_pydeseq2_inputs.py --use-synthetic --design '~condition'
python sub-skills/data-io-validation/scripts/run_local_csv_dea.py --use-synthetic --design '~condition'
```

Add `--run-deseq2` only when a tiny fit is acceptable for the task. Full modeling choices belong in `../dea-workflows/SKILL.md`.

## AnnData And Pickling

If pickling a raw `DeseqDataSet` fails because the design matrix carries formulaic metadata, export a picklable `AnnData` instead:

```python
adata = dds.to_picklable_anndata()
```

This is relevant after `DeseqDataSet` construction or fitting. It is not a substitute for validating the original count and metadata inputs.
