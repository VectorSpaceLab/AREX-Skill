# IO Troubleshooting

Start every diagnosis with: exact path, format/extension, file size, Vaex and
plugin versions, whether the path is local or remote, the opening/export command,
selected columns/filter/group, and whether Pandas/PyArrow/Astropy can read the
same file.

## Fast triage commands

```python
import pathlib
import vaex

path = pathlib.Path("data.hdf5")
print(path.exists(), path.stat().st_size if path.exists() else None)

df = vaex.open(str(path))
print(len(df), df.get_column_names())
print(df.head(3))
```

```bash
# Column discovery before CLI conversion.
vaex convert --list input.csv output.hdf5

# From this sub-skill directory, local-only bundled helper diagnostics.
python scripts/convert_csv_hdf5.py --list-columns input.csv output.hdf5
python scripts/io_roundtrip_smoke.py --formats hdf5 arrow parquet csv --output-dir ./tmp-vaex-io-smoke
```

## Failure matrix

| Symptom | Likely causes | What to do |
| --- | --- | --- |
| `vaex.open` raises unsupported/unknown format | Wrong extension, unregistered opener, optional plugin missing, file is not the format it claims | Confirm extension and magic with another reader; install/import `vaex-hdf5` or `vaex-astro` if needed; try `vaex.open(path, group=...)` for HDF5 |
| File opens in Pandas but not Vaex | Pandas HDF5 row layout, CSV dialect handled by Pandas but not Arrow lazy open, object columns | Convert through Pandas -> `vaex.from_pandas(...).export_hdf5(...)`; use `from_csv` with Pandas kwargs; validate dtypes |
| HDF5 opens only with a group or fails by default | Vaex table stored outside `/table`, multiple groups, non-Vaex HDF5 layout | Inspect HDF5 groups with an HDF5 tool or producer metadata; open with `group="/name"`; re-export to Vaex HDF5 when needed |
| `No module named vaex.hdf5` or HDF5 export/open error | Missing `vaex-hdf5` distribution or incompatible `h5py` stack | Install the Vaex HDF5 package matching the Vaex version; retry a tiny export/open roundtrip |
| FITS/VOTable fails | Missing `vaex-astro`/Astropy, unsupported HDU/table/column type, TAP URL used without network | Import `vaex.astro`; test a local tiny file; skip TAP unless network is authorized; use Astropy to normalize unusual tables |
| CSV lazy open infers wrong schema | Mixed types, missing headers, delimiter/quote/null conventions, too-small inference fraction | Use `from_csv_arrow` with explicit PyArrow options or `from_csv` with Pandas kwargs; convert and validate dtypes before scaling |
| CSV conversion uses too much memory | Chunk size too large, wide rows, Pandas-backed conversion, downstream sorting/shuffling | Lower `chunk_size`; avoid sort/shuffle unless needed; convert selected columns only; ensure enough disk for temp chunks |
| `vaex convert` deletes failed output | Default failure cleanup removes partial output | Pass `--no-delete`; use a temp output path; use bundled helper `--no-delete`/`--overwrite` policy |
| `vaex convert` says a column is missing | CLI column names do not exactly match, spaces/special characters, header missing | Run `vaex convert --list`; quote exact names; pass proper CSV header/read options through Python helper when needed |
| Arrow/Parquet/Feather roundtrip changes string/null behavior | Large-string reduction, nullable masks, dictionary/categorical encoding | Use `to_arrow_table`/PyArrow schema inspection; test null counts and representative rows; set explicit Arrow types when producing data |
| Cloud path fails | Missing `s3fs`/`gcsfs`/Arrow S3 support, credentials/profile issue, wrong region/endpoint, cache permissions, network unavailable | Treat as optional; confirm authorization; test dependency imports; pass `fs_options`; try local sample first |
| Export to cloud fails | Backend does not support requested write mode, credentials/permissions, HDF5 remote write limitation | Prefer Parquet/Arrow/CSV; use `export_many`; never overwrite remote output without explicit user approval |

## HDF5: Pandas vs Vaex diagnosis

Pandas and Vaex use different HDF5 layouts. If a file opens with
`pandas.read_hdf` but not `vaex.open`, use this conversion route:

```python
import pandas as pd
import vaex

pdf = pd.read_hdf("source.h5", key="table")
df = vaex.from_pandas(pdf, copy_index=False)
df.export_hdf5("source_vaex.hdf5")
check = vaex.open("source_vaex.hdf5")
assert len(check) == len(pdf)
```

If the file was produced by Vaex but has custom groups:

```python
df = vaex.open("multi_group.hdf5", group="/numbers")
```

Avoid editing HDF5 internals by hand; re-export through Vaex when possible.

## CSV chunk memory pressure

Signs: process killed, swap growth, Pandas parser memory spikes, or temporary
chunks fill disk.

Actions:

1. Lower `chunk_size` substantially and rerun on a sample.
2. Select only required columns before export where possible.
3. Avoid `--sort` and `--shuffle` during ingestion unless they are required.
4. Use Arrow lazy open (`vaex.open(csv)` or `from_csv_arrow(..., lazy=True)`) for
   exploratory inspection before conversion.
5. Put output and temporary chunks on a filesystem with enough free space.
6. Validate after conversion; do not trust partial output from a killed process.

## Destructive cleanup and overwrite safety

Vaex's `vaex convert` defaults to deleting the output file when export fails.
This protects users from accidentally using a partial output, but can surprise
when debugging. Use:

```bash
vaex convert --no-delete input.csv output.hdf5
```

The bundled helper has separate safeguards:

- It refuses to overwrite an existing output unless `--overwrite` is passed.
- It writes to a temporary HDF5 path and replaces the output only after success.
- `--no-delete` keeps the temporary failed file for inspection.
- It rejects remote paths to avoid credentialed/destructive side effects.

## Column name pitfalls

- Use `df.get_column_names()` in Python or `vaex convert --list` in CLI.
- For Python access, use `df["#"]`, `df["column with spaces"]`, or
  `df.get_column_names()`; dot access only works for identifier-like columns.
- For shell commands, quote column names individually. Do not rely on wildcard
  expansion for names containing spaces.
- If a CSV has no header, provide names via Pandas/Arrow read options in Python
  before converting; the plain `vaex convert` CLI cannot express every CSV
  dialect option.

## Plugin and optional dependency checks

```python
checks = ["vaex", "vaex.hdf5", "vaex.astro"]
for name in checks:
    try:
        __import__(name)
        print(name, "ok")
    except Exception as exc:
        print(name, type(exc).__name__, exc)
```

- `vaex-hdf5` is required for Vaex HDF5 read/write.
- `vaex-astro` plus Astropy is required for FITS/VOTable/TAP and astro accessors.
- S3/GCS may require PyArrow filesystem support, `s3fs`, or `gcsfs` depending on
  scheme/options.
- Cloud credentials should come from user-approved environment/profile handling,
  not embedded code.

## Roundtrip mismatch diagnosis

When output opens but values differ:

1. Check whether a filter, fraction, selection, sort, shuffle, or optimization was
   requested.
2. Compare column names and dtypes first; dtype changes often explain value
   formatting differences.
3. Compare counts and null counts before comparing exact values.
4. Compare stable aggregates on numeric columns.
5. Only compare row order if no shuffle/sort/filter/partition operation changed
   ordering semantics.
6. For CSV, inspect delimiter, quoting, null values, decimal separators, and
   date parsing.
7. For Arrow/Parquet, inspect schema metadata and nullable masks.

## When to stop and ask the user

Stop before proceeding if any of these are required but unspecified:

- Network/cloud/TAP access, credentials, bucket names, or signed URLs.
- Overwriting existing local or remote outputs.
- Deleting partial conversion artifacts that may be needed for recovery.
- Accepting dtype precision loss from `--downcast`, `--downcast-float`, or
  `--optimize`.
- Converting a file whose legal/privacy boundary is unclear.
