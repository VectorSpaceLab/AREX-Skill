# Units, time indexes, metadata, and local data

## DataFrame contract

The safe input shape is a pandas `DataFrame` with one row per observation and a
DatetimeIndex (or an index convertible to one). Each value column must have the
same length as the index. Normalize timestamps before construction:

```python
import pandas as pd

df.index = pd.to_datetime(df.index)
df = df.sort_index()
if not df.index.is_unique:
    # Decide whether duplicates are real observations or need aggregation.
    df = df[~df.index.duplicated(keep="first")]
```

Do not silently remove duplicate observations in a scientific analysis; the
snippet is only a deterministic policy when the input contract says duplicates
are accidental. Check timezone assumptions and record them. SunPy's
`TimeSeries.time` exposes an Astropy `Time`, while pandas operations use the
DataFrame index representation.

## Unit mapping

`units` is a dictionary whose keys must match DataFrame columns and whose values
must be Astropy units. Good patterns include:

```python
units = {
    "irradiance": u.W / u.m**2,
    "count_rate": u.ct / u.s,
    "latitude": u.deg,
    "quality_flag": u.dimensionless_unscaled,
}
```

`GenericTimeSeries` fills missing unit entries with
`u.dimensionless_unscaled` after warning. This is a fallback for incomplete
metadata, not a physical interpretation. Inspect `ts.units` and fail the
analysis if a required physical column is dimensionless unexpectedly.

Use `ts.quantity(name)` to bind values to their declared unit. Use Astropy
conversion before adding or comparing quantities:

```python
scaled = (ts.quantity("irradiance") * 1.0).to(u.mW / u.m**2)
updated = ts.add_column("irradiance_mW", scaled)
```

When adding a raw NumPy/pandas array, pass `unit=`. When overwriting a column
with a Quantity, SunPy converts to the existing column unit if `overwrite=True`.
Never assign a Quantity directly into a DataFrame column and assume SunPy will
update `ts.units`; update the mapping deliberately and reconstruct if needed.

CDF units deserve extra scrutiny. CDF unit strings do not have one universally
parseable Astropy spelling. SunPy has common mappings, but can warn on an
unknown string and assign dimensionless units. Preserve the warning and either:

1. register a known custom definition with Astropy, e.g.
   `u.add_enabled_units([u.def_unit("#/cc", represents=u.cm**-3)])`, or
2. map the source variable to a documented Astropy unit before calculation.

Do not guess from the variable name. Keep the source string, selected unit, and
conversion in the analysis record.

## Metadata contract

`meta` may be a plain dict, `OrderedDict`, `MetaDict`, or a prebuilt
`TimeSeriesMetaData`. A plain dict is associated with the whole input range and
all input columns. The structured metadata object stores entries as:

```text
(TimeRange, [column names], MetaDict(metadata))
```

Useful read operations are:

```python
ts.meta.metadata       # source entries
ts.meta.timeranges      # entry ranges
ts.meta.columns         # columns mentioned by metadata
ts.meta.metas          # metadata dictionaries
ts.meta.find(time=..., colname=...)
ts.meta.get("TELESCOP", time=..., colname=...)
ts.meta.to_string(depth=2)
```

`find()` and `get()` return a filtered
`TimeSeriesMetaData` object. `update(dictionary, overwrite=False)` protects
existing keys unless explicitly overridden. After a truncate or concatenate,
inspect metadata entries because ranges and column associations are adjusted.

New columns do not automatically gain a metadata entry describing their
instrument provenance. Add a clear metadata record in your analysis layer if
that provenance matters; do not claim that an instrument header describes a
computed channel.

## Astropy Table inputs and outputs

The factory can consume an Astropy `Table`. The time column must be first, or a
single primary-key index. Quantity columns carry units and `table.meta` becomes
metadata. A Table with multiple index columns is invalid for this conversion.
On output, `to_table()` creates a new `date` column at position zero and sets
units on value columns. Check both `table.colnames` and `table[column].unit`
when round-tripping.

## Local files and optional formats

- FITS source files use the registered instrument parser when metadata or
  `source=` identifies it. FITS I/O and reader selection are owned by the data
  access route; this route validates the resulting object.
- GOES XRS supports the source implementation's FITS and relevant netCDF/HDF5
  paths. Confirm the result's columns and irradiance units; do not assume all
  GOES product generations have the same fields.
- EVE L0CS text, EVE/ESP FITS, GBM summary FITS, LYRA FITS, and other registered
  mission formats need their source selector when automatic detection is not
  unique.
- CDF reading is optional and depends on the installed CDF reader. It is local
  only in this route. A CDF can contain multiple variables/groups and thus
  return a list. Some variables may be empty; treat an empty series as a
  loader result requiring inspection, not a valid zero-valued observation.

For a local fixture, use a temporary file and a tiny input. Do not copy a
repository fixture path into a runtime command, and do not bundle large
mission assets. Remote sample constants are not local guarantees: a sample
identifier may trigger a download, so remote examples are reference-only.
