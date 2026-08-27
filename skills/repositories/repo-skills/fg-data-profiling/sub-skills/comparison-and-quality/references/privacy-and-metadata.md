# Privacy, Metadata, and Data Dictionaries

## When to read

Read this when the report should hide raw values, replace sample rows, or carry
dataset/column metadata for a shared report.

## Privacy-first report settings

```python
profile = ProfileReport(
    df,
    title="Private report",
    sensitive=True,
    samples=None,
    duplicates=None,
    minimal=True,
)
```

If the user still wants a sample section, replace it with a synthetic sample
that preserves the shape without preserving the real data:

```python
profile = ProfileReport(
    df,
    sensitive=True,
    sample={
        "name": "Synthetic sample",
        "data": synthetic_df,
        "caption": "Synthetic rows only; no real records are shown.",
    },
)
```

## Phone-number and identifier caveat

Reading private identifiers as numeric can leak aggregates even when samples are
hidden. For phone-like or identifier columns, keep the string type while loading
input data:

```python
pd.read_csv("filename.csv", dtype={"phone": str})
```

## Metadata fields

The dataset metadata object supports fields inspired by schema.org Dataset:

- `description`
- `creator`
- `author`
- `copyright_holder`
- `copyright_year`
- `url`

Column dictionaries live under `variables.descriptions`.

```python
profile = ProfileReport(
    df,
    dataset={
        "description": "Generated from a reproducible sample.",
        "creator": "Analytics team",
        "url": "https://example.com/source",
    },
    variables={"descriptions": {"amount": "Transaction amount in USD"}},
)
```

## Type schema

`type_schema` lets you override inference for known columns without forcing the
rest of the DataFrame to a fixed type.

```python
type_schema = {"country": "categorical", "event_time": "timeseries"}
```

Use this when the data catalog or upstream system already knows the intended
semantic type of selected columns.

## Safe privacy validation

Use the sensitive smoke helper with a tiny synthetic DataFrame to confirm that
real-looking names are absent from the generated HTML before applying the same
pattern to private datasets.
