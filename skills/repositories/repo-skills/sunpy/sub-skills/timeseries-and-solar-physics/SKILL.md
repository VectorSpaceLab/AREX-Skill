---
name: timeseries-and-solar-physics
description: "Build, load, inspect, transform, plot, and round-trip SunPy
  TimeSeries data locally, and apply SunPy solar constants, models, and
  differential-rotation helpers without conflating local analysis with remote
  acquisition."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 2-Clause
---

# SunPy time series and solar physics

Use this route when the task is about one-dimensional, time-indexed solar or
space-weather measurements, a deterministic local time-series analysis, solar
constants/models, or differential rotation. The verified public API surface is
SunPy `0.1.dev1+gd2ae0740e` and Python `>=3.12`; treat other releases as
potentially version-sensitive.

## Route the request first

- **Create or analyze a local series**: start with
  [workflows](references/workflows.md) and [units and data](references/units-and-data.md).
- **Load a local mission file**: read the source-loader section in
  [the API reference](references/api-reference.md), then use a local path and
  an explicit `source=` when detection is ambiguous.
- **Search or fetch GOES/HEK/CDAWeb data**: stop here and hand acquisition to
  [`data-access-and-io`](../data-access-and-io/SKILL.md). This route consumes a
  local file or already-created object; it does not perform an unbounded search
  or download.
- **Construct/transform coordinate frames**: hand frame construction and
  transformations to [`coordinates-and-time`](../coordinates-and-time/SKILL.md).
  `solar_rotate_coordinate()` is included here only as the time-dependent
  differential-rotation operation after a valid coordinate exists.
- **Rotate or plot mission images/maps**: hand map construction and image
  rendering to [`maps-and-visualization`](../maps-and-visualization/SKILL.md).
  `differential_rotate()` is map-oriented and should normally be used there.

Read [troubleshooting](references/troubleshooting.md) when an import, optional
reader, unit, time-index, metadata, or headless plotting check fails.

## Core operating contract

A `TimeSeries` has three coupled pieces:

1. A pandas `DataFrame` whose index is the observation time and whose columns
   are channels.
2. `meta`, represented by `TimeSeriesMetaData`, containing time ranges,
   applicable column names, and metadata dictionaries.
3. `units`, a mapping from every column name to an Astropy unit.

Keep the index sorted, time-like, and the same length as each value column.
Keep units synchronized after pandas operations. Validate with
`ts.columns`, `ts.shape`, `ts.time_range`, `ts.units`, `ts.to_dataframe()`, and
`ts.quantity(column)`; these are stronger signals than a printed repr.

## Choose the constructor correctly

- `sunpy.timeseries.TimeSeries(*args, allow_errors=False, **kwargs)` is a
  **factory**. It dispatches DataFrames, Astropy Tables, accepted data/header
  pairs, local paths/globs/directories, URLs/URIs, existing TimeSeries objects,
  and registered source classes. Multiple inputs return a list unless
  `concatenate=True` is passed.
- `sunpy.timeseries.GenericTimeSeries(data, meta=None, units=None, **kwargs)` is
  the direct generic constructor. Prefer it when the data is already a local
  DataFrame and no instrument parser is needed.
- A bare Python `dict` or arbitrary `list` is not a generic data container for
  the factory. It can be expanded as a list of *accepted inputs*, but a dict
  or list of numeric values normally reaches dispatch and raises
  `NoMatchError`. Build a DataFrame first, then call `GenericTimeSeries(df,
  meta, units)` or `TimeSeries(df, meta, units)`.
- A valid source parser may return a source subclass; a generic local DataFrame
  returns `GenericTimeSeries`. Do not assume that every `TimeSeries` result has
  a mission-specific `source`.

See [the API table](references/api-reference.md) for exact signatures and
return-shape details.

## Deterministic local workflow

1. Normalize timestamps into a pandas datetime-like index and make a small
   DataFrame. Use explicit units such as `u.W / u.m**2`, `u.ct`, or
   `u.dimensionless_unscaled`.
2. Construct with `GenericTimeSeries(df, meta, units)` (or the factory with the
   same three positional groups).
3. Inspect `ts.to_dataframe()`, `ts.to_table()` (date column first, units
   attached), `ts.to_array()`, `ts.time`, `ts.time_range`, and
   `ts.meta.to_string(depth=...)`.
4. Select with `extract(column_name)` or `quantity(column_name)`. Add a new
   channel with `add_column(name, Quantity)`; remove one with
   `remove_column(name)`. These return new objects rather than modifying the
   original data object.
5. Restrict with `truncate(TimeRange(...))`, two parseable time strings, or
   integer slice arguments. Re-sort with `sort_index()` if inputs were not
   chronological.
6. For resampling, use pandas on a copy of `ts.to_dataframe()`, for example
   `df.resample("10min").mean()`, then reconstruct with the existing metadata
   and units. SunPy does not provide a separate TimeSeries `resample()` method.
7. Combine compatible intervals with `ts.concatenate(other, same_source=True)`
   or create from multiple accepted inputs with `concatenate=True`. The
   implementation concatenates and sorts; do not assume overlapping timestamps
   are deduplicated. Check the resulting index, shape, and units and apply an
   explicit duplicate policy to a copied DataFrame when needed.
8. Use `plot(axes=ax, columns=[...])` for controlled Matplotlib output. Use
   `peek()` for a quick diagnostic figure, not as the primary plotting API.
   Set `MPLBACKEND=Agg` or create/close figures explicitly in headless jobs.
   `quicklook()` opens a browser and is therefore interactive/optional.

Run the bundled [TimeSeries round-trip helper](scripts/timeseries_roundtrip.py)
when a compact executable smoke is useful. It uses synthetic local data and a
temporary ECSV file:

```bash
python scripts/timeseries_roundtrip.py --help
MPLBACKEND=Agg python scripts/timeseries_roundtrip.py
```

## Local source-specific loading

For a local mission file, call the factory with a `pathlib.Path` or path string.
Use an explicit source when metadata cannot uniquely identify the parser:

- GOES XRS: `TimeSeries(path, source="XRS")`; the registered
  `XRSTimeSeries` reader supports relevant FITS and GOES netCDF/HDF5 forms.
- SDO EVE: `source="EVE"` for the EVE L0CS text form; EVE ESP FITS uses the
  registered ESP source (`source="ESP"`).
- Fermi/GBM summary: `source="GBMSummary"` and the registered
  `GBMSummaryTimeSeries` parser.
- PROBA2/LYRA: `source="LYRA"` and the registered `LYRATimeSeries` parser.
- CDF: with the CDF optional dependency available, `TimeSeries(path)` can
  read Space Physics Guidelines-style CDF data. A file may produce multiple
  generic series (for example, separate data groups); inspect whether the
  result is a list before indexing or concatenating.

For all loaders, validate the resulting class, columns, time span, units, and
finite/missing-value policy before scientific use. Source examples that fetch
sample data or query GOES/HEK remain documentation-only. Acquire files through
the data-access route, then pass the local result here.

## Solar constants, models, and rotation

Use `sunpy.sun.constants` for Astropy constants and solar time parameters:
`constants.get(key)`, `constants.find(substring)`, and `constants.print_all()`
are the stable discovery operations. Common aliases include `mass`, `radius`,
`luminosity`, `sfu`, `sidereal_rotation_rate`, `first_carrington_rotation`, and
`mean_synodic_period`. Convert constants explicitly with Astropy units rather
than stripping `.value` prematurely.

Use `sunpy.sun.models.interior` and `.evolution` as unit-bearing Astropy
`QTable` model data, and `sunpy.sun.models.differential_rotation(duration,
latitude, model="howard", frame_time="sidereal")` for a longitude change.
Supported models are `howard`, `snodgrass`, `allen`, and `rigid`; supported
frame times are `sidereal` and `synodic`. The result is an Astropy
`Longitude`. Use `u.day`/`u.s` and `u.deg` quantities, including arrays when
needed.

For an existing valid solar `SkyCoord`,
`sunpy.physics.differential_rotation.solar_rotate_coordinate(coordinate,
observer=...)` or `time=...` returns the rotated coordinate. Supply exactly one
of `observer` and `time`; `time=` assumes an Earth observer and emits a warning.
Do not supply both or neither. Keep frame construction, observer selection, and
coordinate transforms in the coordinates route. For maps, use
`differential_rotate(smap, observer=... or time=...)` only after reviewing the
map route: it requires image/WCS inputs, may require scikit-image, and is more
expensive than the scalar model calculation.

Run the bundled [differential-rotation helper](scripts/differential_rotation_smoke.py)
for a deterministic physics smoke without network or map data:

```bash
python scripts/differential_rotation_smoke.py --help
python scripts/differential_rotation_smoke.py --duration-days 2 --latitude 30
```

## Validation and recovery signals

A successful local run has a non-empty DataFrame, a time range matching the
index extrema, one unit entry per column, stable column names after round-trip,
and a returned rotation with angular units. If a loader returns a list, inspect
each element instead of treating the list as a series. If a plot fails, first
validate non-empty data and switch to `MPLBACKEND=Agg`; if a unit or source is
unknown, preserve the warning and resolve it before analysis. Use the detailed
failure matrix in [troubleshooting](references/troubleshooting.md).
