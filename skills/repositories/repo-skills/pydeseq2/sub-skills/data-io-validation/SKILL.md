---
name: data-io-validation
description: "Prepare, load, orient, and validate PyDESeq2 count and metadata
  inputs before differential expression modeling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data I/O And Validation

Use this sub-skill when a task is about getting data into PyDESeq2 safely: reading count and metadata CSVs, fixing sample/gene orientation, checking design prerequisites, constructing a `DeseqDataSet`, or exporting fitted data as picklable `AnnData`.

## Read First

- `references/data-formats.md`: expected schemas, loading patterns, validation checklist, filtering, `AnnData`, and script recipes.
- `references/troubleshooting.md`: symptoms and recoveries for count, metadata, design, orientation, and local CSV problems.
- `scripts/validate_pydeseq2_inputs.py`: network-free validator for local CSVs and optional design matrices.
- `scripts/run_local_csv_dea.py`: local CSV adaptation of the pandas I/O example with optional synthetic data and optional tiny fit smoke.

## Core Rules

- Counts must be samples x genes: rows are sample ids, columns are gene ids, and values are numeric non-negative integers.
- Metadata must be samples x variables: its index must be the same sample ids, in the same order, as the count index before constructing `DeseqDataSet`.
- If counts arrive as genes x samples, transpose them before validation or pass `--orientation genes-by-samples` to the bundled scripts.
- Formula designs such as `~condition` or `~group + condition` reference metadata columns; direct design matrices must have one row per sample and an index identical to metadata/counts.
- Filter missing design-factor samples before modeling, then optionally remove genes with low total counts.

## Recommended Workflow

1. Load with `pandas.read_csv(..., index_col=0)` or use `load_example_data(modality="raw_counts"|"metadata", dataset="synthetic")` for the built-in synthetic example.
2. Normalize orientation to samples x genes, then align metadata with `metadata = metadata.loc[counts.index]` only after confirming both sets of sample ids match.
3. From this sub-skill directory, run `python scripts/validate_pydeseq2_inputs.py --counts-csv counts.csv --metadata-csv metadata.csv --design '~condition' --orientation auto`.
4. Construct `DeseqDataSet(counts=counts_df, metadata=metadata, design="~condition")` only after validation passes.
5. Route full fitting with `dds.deseq2()` to `../dea-workflows/SKILL.md`; route result interpretation to `../statistics-and-results/SKILL.md`; route VST/normalization internals to `../model-fitting-internals/SKILL.md`.

## Safe Export

When a fitted `DeseqDataSet` must be pickled, export `dds.to_picklable_anndata()` instead of pickling the raw `DeseqDataSet`; this converts the formulaic design matrix metadata into a picklable `AnnData` representation.
