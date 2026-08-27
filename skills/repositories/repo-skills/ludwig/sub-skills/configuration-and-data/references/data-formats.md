# Data Formats and Dataset Layouts

## Accepted dataset sources

Ludwig accepts common local tabular formats through CLI/API data-format handling: CSV, TSV, JSON/JSONL, Parquet, Excel, Feather, HDF5, Pickle, SAS/SPSS/Stata, fixed-width, and HTML tables where dependencies support them. Pandas DataFrames and dictionaries are accepted in Python API flows.

## Column rules

- Each feature `name` (or explicit `column`) must be present in training data.
- Prediction data normally contains input feature columns only.
- Evaluation data must include ground-truth output columns.
- A split column may encode training/validation/test splits when present; otherwise Ludwig can split randomly.
- Timeseries forecasting needs enough history for the configured window size.

## Tiny local fixture workflow

```bash
python scripts/make_tiny_dataset.py --output-dir /tmp/ludwig-tiny --rows 12
ludwig preprocess --dataset /tmp/ludwig-tiny/dataset.csv --preprocessing_config /tmp/ludwig-tiny/config.yaml
```

Use `preprocess` as a lightweight data/config check before training when the user is unsure about columns or feature types.

## Dataset zoo caveats

Dataset-zoo examples can download data and populate caches. Do not use them for smoke tests unless the user explicitly approves network/cache side effects. Prefer generated local fixtures for skill-driven validation.
