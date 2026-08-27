# Data Formats and Input Constraints

## When to read

Read this when a user asks which data shapes or files can be profiled, or when
input loading fails before report generation.

## DataFrame inputs

Core workflows use a non-empty pandas DataFrame:

```python
import pandas as pd
from data_profiling import ProfileReport

df = pd.read_csv("data.csv")
if df.empty:
    raise ValueError("ProfileReport requires a non-empty DataFrame for eager profiling")
profile = ProfileReport(df, minimal=True)
```

A lazy `ProfileReport()` with no DataFrame can be configured before a DataFrame
is attached, but `lazy=False` and ordinary eager report generation require data.

## CLI/file-reader supported extensions

The command-line path uses pandas readers for common file types. It supports:

| Extension | Reader behavior |
| --- | --- |
| `.csv` or unknown extension | `pandas.read_csv`; unknown extensions warn and are assumed CSV-like |
| `.json` | `pandas.read_json` |
| `.jsonl` | `pandas.read_json(..., lines=True)` |
| `.dta` | `pandas.read_stata` |
| `.tsv` | `pandas.read_csv(..., sep="\t")` |
| `.xls`, `.xlsx` | `pandas.read_excel` |
| `.hdf`, `.h5` | `pandas.read_hdf` |
| `.sas7bdat`, `.xpt` | `pandas.read_sas` |
| `.parquet` | `pandas.read_parquet` |
| `.pkl`, `.pickle` | `pandas.read_pickle` |
| `.bz2`, `.gz`, `.xz`, `.zip` | Compression suffix is stripped and pandas handles decompression when valid |
| `.tar` | Rejected; use Python's `tarfile` module or extract first |

For advanced file handling, load the data yourself with pandas and pass the
DataFrame to `ProfileReport` instead of relying on the CLI reader.

## Semantic data types

The report infers semantic variable types such as numerical, categorical, text,
boolean, datetime, URL, file, image, path, and time-series. You can override
selected columns with `type_schema` when inference is not enough.

```python
profile = ProfileReport(
    df,
    type_schema={"url_column": "url", "sales": "timeseries"},
    vars={"url": {"active": True}},
)
```

Some semantic types need explicit activation or explorative mode, especially
URL/path/file/image analysis.

## Large or expensive data

For large datasets, start with one or more of these patterns:

- `minimal=True`
- sampled DataFrame with a dataset description
- disable expensive sections through the configuration sub-skill
- target interactions only for columns of interest
- use Spark only after optional backend readiness is confirmed

## Privacy-sensitive input

If the dataset includes names, phone numbers, addresses, medical data, or other
private values, route to the comparison/quality sub-skill before showing samples
or duplicate rows. In particular, keep phone numbers and identifiers as strings
when reading data so numeric aggregates do not expose sensitive ranges.
