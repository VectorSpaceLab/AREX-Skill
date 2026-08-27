# Vaex IO Workflows

This reference covers practical opening, conversion, export, and validation
patterns. It assumes `vaex` and any optional plugin packages needed for the
chosen format are already installed.

## Quick workflow selection

| Task | Prefer | Validate with |
| --- | --- | --- |
| Open an existing Vaex HDF5/Arrow/Parquet/Feather/FITS file | `vaex.open(path)` | `len(df)`, `df.get_column_names()`, a small `df.head()` or aggregate |
| Open several files as one DataFrame | `vaex.open("glob*.hdf5")` or `vaex.open_many([...])` | Row counts per file plus combined count |
| Work with a huge CSV without loading it all | `vaex.open("data.csv")` for lazy Arrow-backed CSV, or convert to HDF5/Parquet | Schema inference, sample rows, post-conversion row count |
| Convert CSV to Vaex HDF5 for repeated queries | `vaex.open(csv, convert="out.hdf5")`, `vaex.from_csv(..., convert=...)`, `vaex convert`, or `scripts/convert_csv_hdf5.py` | Open output with Vaex and compare columns/counts/aggregates |
| Export a Vaex DataFrame | `df.export("out.hdf5|arrow|parquet|feather|fits|csv")` or format-specific methods | Reopen output and compare expected rows/columns |
| Pass data to another library | `df.to_arrow_table(...)`, `df.to_pandas_df(...)`, `vaex.from_pandas(...)`, `vaex.from_arrow_table(...)` | Compare schema, nullable columns, and a small value sample |

## Opening files

Common APIs:

```python
import vaex

# Single local files. Extra reader kwargs pass through to the opener.
df = vaex.open("data.hdf5")
df = vaex.open("data.hdf5", group="/table")
df = vaex.open("data.arrow")
df = vaex.open("data.parquet")
df = vaex.open("data.feather")

# CSV: Vaex 4.14+ can lazily open CSV via Arrow-backed scanning.
df_csv_lazy = vaex.open("data.csv")

# Glob or explicit list; mixed formats are allowed when each file opens.
df_all = vaex.open("part-*.hdf5")
df_all = vaex.open_many(["part-0.hdf5", "part-1.hdf5"])
```

Verified public signatures for this skill version:

```text
vaex.open(path, convert=False, progress=None, shuffle=False, fs_options={}, fs=None, *args, **kwargs)
vaex.open_many(filenames)
vaex.from_csv(filename_or_buffer, copy_index=False, chunk_size=None, convert=False, fs_options={}, progress=None, fs=None, **kwargs)
vaex.from_csv_arrow(file, read_options=None, parse_options=None, convert_options=None, lazy=False, chunk_size='10MiB', newline_readahead='64kiB', schema_infer_fraction=0.01, fs_options={}, fs=None)
vaex.from_pandas(df, name='pandas', copy_index=False, index_name='index')
vaex.from_arrow_table(table)
```

Opening rules:

- `vaex.open` returns a DataFrame on success and raises for unsupported or broken
  files. Treat an exception as a format/plugin/schema problem, not as proof the
  file is empty.
- HDF5, Arrow, Parquet, Feather, and FITS are the formats to consider for large
  file-backed workflows. HDF5 and Arrow-family files are the common Vaex-native
  choices; Parquet is usually better for compressed/cloud interchange.
- HDF5 supports a `group` argument. Vaex writes to `/table` by default; if a file
  has multiple groups, open the group that was exported.
- `open_many` strips blank lines and ignores entries beginning with `#` when it
  receives a text-list style filename list through the convert CLI; for API use,
  pass concrete filenames.

## CSV ingestion and conversion

### Lazy CSV open

```python
df = vaex.open("large.csv")
print(len(df), df.get_column_names())
```

This streams/scans CSV data through Arrow. Schema detection reads metadata first,
so failures commonly come from bad delimiters, inconsistent types, or too little
schema-inference data. For Arrow CSV options, build explicit `pyarrow.csv`
`ReadOptions`, `ParseOptions`, or `ConvertOptions` and use `vaex.from_csv_arrow`.

### Read whole CSV through Pandas

```python
df = vaex.from_csv("small.csv", copy_index=False, sep=",", dtype={"id": "string"})
```

`from_csv` passes extra keyword arguments to Pandas when it reads into memory.
Use this for small/medium files or when Pandas options are needed. Use
`chunk_size` or conversion for files that do not fit in memory.

### Chunked CSV-to-HDF5 conversion

```python
df = vaex.from_csv(
    "large.csv",
    convert="large.hdf5",
    chunk_size=5_000_000,
    copy_index=False,
    progress=True,
)
```

During conversion Vaex reads CSV chunks, writes temporary HDF5 chunks, combines
them, then removes the temporary chunks. Plan for roughly twice the final HDF5
size as temporary free disk space. If you need explicit control over failed
output cleanup, use `vaex convert --no-delete` or the bundled helper.

### Arrow CSV reader

```python
import pyarrow as pa
import pyarrow.csv as pacsv

df = vaex.from_csv_arrow(
    "data.csv",
    lazy=True,
    convert_options=pacsv.ConvertOptions(
        column_types={"id": pa.string()},
        strings_can_be_null=True,
    ),
)
```

Use Arrow options for faster parsing, explicit null/string handling, alternate
delimiters, or lazy streaming. Pass `pa.string()`, `pa.int64()`, etc. in
`ConvertOptions(column_types={...})` when schema inference is not reliable.

## Conversion with `vaex.open(convert=...)`

```python
# Convert only when the input or requested output changed; then reopen output.
df = vaex.open("large.csv", convert="large.hdf5", progress=True)

# If convert=True, Vaex chooses a derived .hdf5 name.
df = vaex.open("large.csv", convert=True)
```

Use this when the input path can be opened by Vaex and you want a one-line
convert-and-open flow. Use the CLI or bundled helper when you need column
selection, filtering, sorting, or `--no-delete` semantics.

## `vaex convert` CLI

Run overall CLI help discovery through `../cli-settings/SKILL.md`; the conversion
semantics are here.

```bash
vaex convert [options] input output [columns ...]
```

Important options:

| Option | Behavior | Safe-use note |
| --- | --- | --- |
| `--list`, `-l` | Print input columns instead of exporting | Use first when column names are unknown or contain spaces/symbols |
| `--progress` / `--no-progress` | Enable or disable progress display | Use `--no-progress` in logs/CI if progress bars are noisy |
| `--no-delete` | Do not delete output on failure | Use during debugging or when failed partial files must be inspected |
| `--shuffle`, `-s` | Shuffle rows before export | Requires extra work; avoid unless row order randomization is intended |
| `--sort SORT` | Sort by a column/expression before export | Confirm the sort key exists and is feasible for data size |
| `--fraction FLOAT`, `-f FLOAT` | Export active fraction of input rows | Useful for samples; default `1.0` exports all active rows |
| `--filter EXPR` | Apply a Vaex filter expression before export | Expression syntax belongs in `../expressions-analytics/SKILL.md` |
| `--optimize` | Categorize, downcast, and float64-to-float32 before export | Can change dtypes; validate schema after conversion |
| `--categorize` | Run `df.optimize.categorize()` before export | Good for repeated low-cardinality strings; validate categories |
| `--downcast` | Run `df.optimize.downcast(...)` before export | Can reduce integer/float width; validate ranges |
| `--downcast-float` | Downcast float64 to float32 when downcasting/optimizing | Precision-changing; only use when acceptable |
| `input` | File path, glob, cloud URL, or `@filelist.txt` | `@filelist` means one input path per line; comments start with `#` |
| `output` | Output file, usually `.hdf5` for this CLI | Use a new path unless overwrite is intentional |
| `columns ...` | Optional output column subset | If any name is wrong, CLI prints a missing-column message and exits nonzero |

Example patterns:

```bash
# Inspect columns before converting.
vaex convert --list input.csv output.hdf5

# Convert selected columns, keep partial output if the run fails.
vaex convert --no-delete --no-progress input.csv output.hdf5 id amount status

# Convert with filtering/sorting. Quote expressions for your shell.
vaex convert --no-delete --filter 'amount > 0' --sort id input.csv output.hdf5 id amount status

# Convert a list of files into one HDF5 output.
vaex convert @filelist.txt combined.hdf5 id amount
```

## Bundled conversion helper

Use this skill's safer local-only wrapper when you want scripted CSV-to-HDF5
conversion without relying on shell-specific quoting or remote paths:

From this sub-skill directory, run:

```bash
python scripts/convert_csv_hdf5.py --help
python scripts/convert_csv_hdf5.py \
  input.csv output.hdf5 \
  --columns id amount status \
  --filter 'amount > 0' \
  --chunk-size 1000000 \
  --no-delete \
  --validate
```

The helper rejects remote paths, supports `--list-columns`, `--dry-run`,
`--progress/--no-progress`, `--shuffle`, `--sort`, `--fraction`, `--filter`,
`--optimize`, `--categorize`, `--downcast`, `--downcast-float`, and safe
partial-output handling. It uses public Vaex APIs (`vaex.open`, lazy DataFrame
transforms, `df.export_hdf5`) rather than copying Vaex's internal conversion
module.

## Exporting from a Vaex DataFrame

Verified public signatures for this skill version:

```text
df.export(path, progress=None, chunk_size=1048576, parallel=True, fs_options=None, fs=None, **kwargs)
df.export_hdf5(path, byteorder='=', progress=None, chunk_size=1048576, parallel=True, column_count=1, writer_threads=0, group='/table', mode='w')
df.export_csv(path, progress=None, chunk_size=1048576, parallel=True, backend='pandas', **kwargs)
df.export_many(path, progress=None, chunk_size=1048576, parallel=True, max_workers=None, fs_options=None, fs=None, **export_kwargs)
df.to_arrow_table(column_names=None, selection=None, strings=True, virtual=True, parallel=True, chunk_size=None, reduce_large=False)
```

The generic `df.export(path)` dispatches by extension:

- `.hdf5` -> Vaex HDF5 via `export_hdf5`.
- `.arrow` -> Arrow IPC stream via `export_arrow`.
- `.feather` -> Feather v2 via `export_feather`.
- `.parquet` -> Parquet via `export_parquet`.
- `.fits` -> FITS via `vaex-astro`.
- `.csv` -> CSV via `export_csv`.
- `.json` -> JSON export when available.

Examples:

```python
# HDF5, default group /table.
df.export_hdf5("clean.hdf5")

# Multiple groups in one HDF5 file.
df_numbers.export_hdf5("multi.hdf5", mode="w", group="/numbers")
df_food.export_hdf5("multi.hdf5", mode="a", group="/food")
df_food_back = vaex.open("multi.hdf5", group="/food")

# Arrow-family exports with chunking.
df.export("clean.arrow", chunk_size=1_048_576)
df.export("clean.parquet", chunk_size=1_048_576)
df.export("clean.feather")

# CSV export; pandas backend is flexible, Arrow backend is faster but stricter.
df.export_csv("clean.csv", backend="pandas", index=False, chunk_size=1_000_000)
df.export_csv("clean_arrow.csv", backend="arrow", chunk_size=1_000_000)

# Many chunks; if {i} is not present, Vaex adds -00001 style suffixes.
df.export_many("parts/chunk_{i:05}.parquet", chunk_size=1_000_000)
df_back = vaex.open("parts/chunk_*.parquet")
```

## Pandas and Arrow table handoffs

```python
import pandas as pd
import pyarrow as pa
import vaex

pdf = pd.DataFrame({"id": [1, 2], "value": [10.0, 20.0]})
df = vaex.from_pandas(pdf, copy_index=False)

# Keep only public tabular columns unless the Pandas index is meaningful.
df.export_hdf5("from_pandas.hdf5")

arrow_table = df.to_arrow_table(column_names=["id", "value"])
df2 = vaex.from_arrow_table(arrow_table)
```

Validation should compare column order/names, dtypes, null counts, and a small
sample. For Pandas nullable integer/string dtypes, test at least one missing
value path because roundtrips can differ by backend.

## Roundtrip validation checklist

For any conversion/export:

1. Record input paths, output path, selected columns, filters, sort/shuffle,
   fraction, HDF5 group, chunk size, backend, and optional dtype optimizations.
2. Open the output with `vaex.open(output, group=...)` or `vaex.open(pattern)`.
3. Assert expected `len(df_out)` and `df_out.get_column_names()`.
4. Compare a deterministic aggregate on stable numeric columns, for example
   `df_out[column].sum()` or `df_out[column].count()`.
5. Compare a small ordered sample only when row order is expected to be stable.
   Do not use strict row-order checks after `--shuffle`.
6. If the source is CSV, inspect inferred dtypes and null parsing explicitly.
7. If a file will be consumed outside Vaex, validate with that consumer too
   (for example PyArrow for Parquet/Feather or Pandas for CSV).

The bundled `scripts/io_roundtrip_smoke.py` demonstrates these checks on tiny
local files.
