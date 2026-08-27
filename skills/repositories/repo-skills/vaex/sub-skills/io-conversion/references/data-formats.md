# Data Formats and Caveats

Vaex is strongest when tabular data can be represented as columns that are
memory-mappable or Arrow-compatible. Choose the format based on repeated-query
performance, interchange needs, storage/network cost, and optional plugin
availability.

## Format decision table

| Format | Open with Vaex | Export with Vaex | Best for | Caveats |
| --- | --- | --- | --- | --- |
| Vaex HDF5 (`.hdf5`) | `vaex.open(path, group="/table")` | `df.export_hdf5(...)` or `df.export("out.hdf5")` | Fast repeated local analytics, large memory-mapped columns | Requires `vaex-hdf5`; Pandas `.to_hdf` layout is usually not Vaex-compatible |
| Arrow IPC (`.arrow`) | `vaex.open(path)` | `df.export_arrow(...)` or `df.export("out.arrow")` | Interop and memory mapping | Arrow string/mask representations can affect performance; validate nullable columns |
| Feather (`.feather`) | `vaex.open(path)` | `df.export_feather(...)` or `df.export("out.feather")` | Arrow/Feather ecosystem handoff | Feather v2 compression choices; typically full table materialization for write |
| Parquet (`.parquet`) | `vaex.open(path)` or directory datasets | `df.export_parquet(...)` or `df.export("out.parquet")` | Compressed storage, cloud transfer, partitioned datasets | Compression/encoding can reduce memory-map advantages; validate row groups/partitioning |
| CSV (`.csv`) | `vaex.open(path)` for lazy Arrow-backed CSV; `from_csv`; `from_csv_arrow` | `df.export_csv(...)` or `df.export("out.csv")` | Ingestion and interchange | Schema inference, delimiter/null handling, and parsing speed matter; convert for repeated use |
| FITS (`.fits`) | `vaex.open(path)` with `vaex-astro` | `df.export_fits(...)` or `df.export("out.fits")` with `vaex-astro` | Local astronomy tables/TOPCAT style workflows | Optional plugin; supported table/column types only |
| VOTable (`.vot`) | `vaex.open(path)` with `vaex-astro` | Usually via Astropy/Vaex astro paths | Local astronomy interchange | Object or unsupported fields can be skipped/converted; TAP/network is separate |
| JSON/SAS/other Pandas-readable formats | Usually read with Pandas then `vaex.from_pandas` | JSON export may exist; otherwise use Pandas/Arrow route | One-off ingestion from broad ecosystem | Not the fast Vaex file-backed path; convert to HDF5/Arrow/Parquet after ingest |
| S3/GCS/cloud paths | `vaex.open("s3://..."|"gs://...", fs_options=...)` where dependencies/credentials exist | Arrow/Parquet/CSV cloud writes may work; HDF5 cloud write is limited | Remote storage and cloud compute | Optional deps/credentials/network/cache; never assume automated access |

## Memory mapping guidance

- HDF5, Arrow IPC, and FITS-style columnar binary files are the primary
  memory-mappable formats for large local data. Opening can be nearly instant
  because Vaex maps columns and evaluates lazily.
- Parquet is excellent for storage and cloud transfer, but compression and
  encoding mean some operations may decode more data than an HDF5/Arrow memory
  map. Use Parquet when interoperability and storage cost matter.
- CSV is text and not memory-mapped in the same sense. Vaex can lazily stream
  CSV through Arrow, but repeated analytics are usually faster after conversion
  to HDF5, Arrow, or Parquet.
- Globbing many files is convenient, but a single optimized local HDF5 or Arrow
  file can be faster than repeatedly concatenating many small files.

## HDF5 layouts

Vaex HDF5 files are column-oriented. Pandas `.to_hdf` writes a row/table layout
that often opens in Pandas but not in Vaex. Convert through Vaex instead:

```python
import pandas as pd
import vaex

pdf = pd.read_hdf("pandas_file.h5", key="table")
df = vaex.from_pandas(pdf, copy_index=False)
df.export_hdf5("vaex_file.hdf5", group="/table")
reopened = vaex.open("vaex_file.hdf5", group="/table")
```

HDF5 group rules:

- Vaex's default export group is `/table`.
- Use `mode="w"` for a new file and `mode="a"` to add another group.
- When appending groups, each group should contain a complete table. Do not try
  to append rows into the same group with `mode="a"`.
- If `vaex.open(path)` fails but `vaex.open(path, group="/some/group")` works,
  record the group requirement with the dataset.

## Arrow, Feather, and Parquet schemas

- `df.to_arrow_table(column_names=None, selection=None, strings=True,
  virtual=True, parallel=True, chunk_size=None, reduce_large=False)` is the
  direct in-memory Arrow handoff.
- `reduce_large=True` in export paths can convert Arrow large-string types to
  regular string types for broader consumer compatibility.
- `df.export_many("chunk_{i:05}.parquet", chunk_size=...)` writes multiple files
  that can be reopened with a glob. This is useful for cloud-style chunked
  outputs and parallel writing.
- Partitioned Parquet directories can be opened when PyArrow dataset support is
  available; validate partition column semantics with a tiny readback before
  scaling up.

Example Arrow handoff check:

```python
table = df.to_arrow_table(["id", "value"])
assert table.num_rows == len(df)
assert table.column_names == ["id", "value"]
df_roundtrip = vaex.from_arrow_table(table)
assert df_roundtrip.value.sum() == df.value.sum()
```

## CSV schema and chunking

Use CSV-specific controls when any of these are true: delimiters are not commas,
headers are missing, columns contain mixed types, strings can be null, dates need
explicit parsing, or column names are not reliable.

### Pandas-backed read

```python
df = vaex.from_csv(
    "input.csv",
    copy_index=False,
    sep=";",
    dtype={"id": "string"},
    na_values=["", "NA", "null"],
)
```

### Arrow-backed read

```python
import pyarrow as pa
import pyarrow.csv as pacsv

df = vaex.from_csv_arrow(
    "input.csv",
    lazy=True,
    parse_options=pacsv.ParseOptions(delimiter=";"),
    convert_options=pacsv.ConvertOptions(
        column_types={"id": pa.string()},
        strings_can_be_null=True,
    ),
)
```

### Chunk-size planning

- `from_csv(..., convert=True)` defaults to a memory-efficient conversion chunk
  size if none is provided; Vaex's conversion code uses a 5,000,000 row default.
- Export defaults are usually `chunk_size=1_048_576` rows. Lower chunk size if a
  row is wide or memory pressure appears; raise it only after measuring.
- Plan disk space for input + output + temporary chunks. CSV-to-HDF5 conversion
  can need about twice the final HDF5 size as working space.

## Pandas and Arrow table conversion

Route generic DataFrame construction details to `../dataframe-core/SKILL.md`, but
use these IO-focused conversion rules:

- `vaex.from_pandas(pdf, copy_index=False)` avoids adding a Pandas index column
  unless that index is meaningful data.
- If the Pandas index is needed, use `copy_index=True` and set `index_name` when
  the default name could collide.
- Convert Pandas data to Vaex HDF5/Arrow/Parquet before large repeated queries.
- Validate nullable Pandas dtypes (`Int64`, `Float32`, string extension arrays)
  with missing values, because downstream file formats may represent masks
  differently.
- `vaex.from_arrow_table(table)` is the cleanest bridge from Arrow producers
  (PyArrow CSV, Parquet datasets, DuckDB/Polars exports) when the schema is
  already Arrow-compatible.

## Column names and non-identifier columns

Vaex can store and reopen non-identifier column names such as `#` or Unicode
names, but expression and CLI usage must quote or select them carefully.

- Use `df.get_column_names()` or `vaex convert --list` before selecting columns.
- In Python, access non-identifier columns with `df["column name"]`, not dot
  syntax.
- In shell commands, quote column names with spaces or special characters as
  individual arguments.
- If a conversion CLI reports `column 'x' does not exist`, rerun with `--list`
  and copy the exact name.

## Cloud storage schema/caching caveats

Cloud support exists for S3/GCS and some Arrow/fsspec routes, but it is optional
for this skill's safe helpers.

- S3 schemes can include `s3://`, `fsspec+s3://`, or `arrow+s3://` depending on
  whether PyArrow or fsspec is used.
- GCS uses `gs://` or `fsspec+gs://` style paths.
- `fs_options` can carry `anon`/`anonymous`, `token`, `cache`, `region`,
  endpoint overrides, or credential selectors. Do not write secrets into scripts
  or logs.
- HDF5 cloud reads can use lazy local caching; Arrow/Parquet cloud behavior and
  cache usefulness differ by backend. Treat cache paths as private machine state.
- Prefer running compute in the same cloud region as the data for large Parquet
  or Arrow reads.

See `astro-and-cloud-io.md` for optional remote-path skip rules and examples.
