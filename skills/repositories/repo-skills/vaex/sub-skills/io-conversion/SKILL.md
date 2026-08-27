---
name: io-conversion
description: "Open, convert, export, and validate local and optional remote
  tabular data with Vaex."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# IO Conversion

Use this sub-skill when the task is about getting tabular data into or out of
Vaex: opening local files, converting CSV/Arrow/Parquet/Feather/HDF5, exporting
DataFrames, checking roundtrips, or diagnosing format-specific failures.

## Route first

- For generic DataFrame construction, lazy DataFrame semantics, virtual columns,
  selections, and basic inspection, route to `../dataframe-core/SKILL.md`.
- For overall `vaex` command discovery, settings, aliases, environment variables,
  and non-conversion CLI commands, route to `../cli-settings/SKILL.md`.
- For expression syntax, filters used in conversion, groupby/binby/aggregation,
  joins, and analytic validation, route to `../expressions-analytics/SKILL.md`.
- Stay here for `vaex.open`, `open_many`, `from_csv`, `from_csv_arrow`,
  `from_pandas`, `from_arrow_table`, `df.export*`, `df.to_arrow_table`, local
  astro file openers, cloud path caveats, and `vaex convert` data semantics.

## Read order

1. `references/io-workflows.md` for actionable open/convert/export recipes,
   API signatures, `vaex convert` options, and roundtrip checks.
2. `references/data-formats.md` for format selection, memory-mapping behavior,
   schema caveats, and Pandas/Arrow/HDF5 handoff details.
3. `references/astro-and-cloud-io.md` for optional local astro formats and
   remote/cloud/TAP skip conditions. Do not run network or credentialed checks
   unless the user explicitly authorizes them.
4. `references/troubleshooting.md` when `vaex.open` fails, a plugin is missing,
   a CSV conversion is memory-heavy, conversion cleanup is surprising, or a file
   opens in Pandas but not in Vaex.

## Safe bundled helpers

- `scripts/io_roundtrip_smoke.py` creates tiny local data, exercises Vaex export
  and open roundtrips, and validates Pandas/Arrow table handoffs. It never uses
  network paths.
- `scripts/convert_csv_hdf5.py` converts a local CSV to Vaex HDF5 with optional
  column selection, filtering, sorting, fractioning, chunk size, listing, dry
  run, and safe partial-output handling. It rejects remote paths.

Run both helpers with `--help` first. They are safe from arbitrary working
directories and use installed public Vaex APIs rather than source-checkout files.

## Operating rules

- Prefer memory-mappable Vaex HDF5 or Arrow-family files for repeated large-data
  work; treat CSV as an ingestion/interchange format and convert when the same
  data will be queried repeatedly.
- Use `vaex.open(path)` for lazy file-backed access when the format is supported;
  use `vaex.open(path, convert="data.hdf5")` or the bundled conversion helper for
  large CSVs that need a faster local binary representation.
- Validate every conversion with at least: row count, column names, a small sample
  or checksum-like aggregate, and the exact group or file pattern used.
- Treat cloud storage, TAP, and credentialed URLs as optional trust-boundary work.
  Document the plan and skip by default in automated scripts.
- Never assume a Pandas-created HDF5 file is Vaex-readable. Convert through
  `vaex.from_pandas(...).export_hdf5(...)` when the source HDF5 layout is row
  oriented or otherwise Pandas-specific.
