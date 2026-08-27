# TimeSeries and solar-physics API reference

This reference records the public signatures and observed return contracts for
SunPy `0.1.dev1+gd2ae0740e` under Python 3.12. Prefer runtime inspection with
`inspect.signature()` when a different SunPy release is installed.

## TimeSeries construction

| API | Inputs | Result and important behavior |
|---|---|---|
| `sunpy.timeseries.TimeSeries(*args, allow_errors=False, **kwargs)` | Accepted input groups: DataFrame, Astropy Table, `(data, meta[, units])`, local path/`Path`, directory/glob, URL/URI, or existing `GenericTimeSeries` | A single object for one parsed result; a list for multiple results; `concatenate=True` folds the results with `concatenate()`. `source=` selects a registered parser. |
| `sunpy.timeseries.GenericTimeSeries(data, meta=None, units=None, **kwargs)` | Usually a pandas DataFrame with a datetime-like index; optional dict/`MetaDict`/`TimeSeriesMetaData` and unit mapping | Direct generic object. Missing unit entries trigger an unknown-unit warning and become `u.dimensionless_unscaled`. |
| `TimeSeriesMetaData(meta=None, timerange=None, colnames=None)` | A metadata dict plus `TimeRange` and column list, a metadata tuple/list, or a prebuilt object | Metadata entries are `(TimeRange, [columns], MetaDict)`. Use `find`, `get`, `update`, `to_string`, and `concatenate`; avoid relying on private mutation helpers. |

The factory is not a general-purpose dict/list converter. A bare dict or list
of values is interpreted as a collection of factory inputs and normally raises
`NoMatchError`. Use a DataFrame as the first argument to the generic
constructor. A DataFrame can be passed to the factory as `TimeSeries(df, meta,
units)` because its dispatch path recognizes it.

## Core object properties and methods

| API | Signature | Result/notes |
|---|---|---|
| `columns` | property | List of DataFrame column names. |
| `shape` | property | `(n_rows, n_columns)`. |
| `time` | property | Astropy `Time` made from the DataFrame index; returned time format is `iso`. |
| `time_range` | property | `sunpy.time.TimeRange` from index minimum/maximum, or `None` for empty data. |
| `to_dataframe()` | `(**kwargs)` | The underlying pandas DataFrame. Treat it as the analysis representation and preserve units separately. |
| `to_table()` | `(**kwargs)` | New Astropy `Table` with a leading `date` column and units attached to data columns. |
| `to_array()` | `(**kwargs)` | NumPy array; kwargs pass to DataFrame `to_numpy()` when available. |
| `quantity(column)` | `(colname, **kwargs)` | Astropy `Quantity` using the values and `ts.units[colname]`. |
| `extract(column)` | `(column_name)` | New generic series containing that column, with NaN rows dropped. |
| `add_column()` | `(colname, quantity, unit=False, overwrite=True, **kwargs)` | New series. A Quantity is converted to the existing unit when overwriting; a raw array needs `unit=` for physical meaning. |
| `remove_column()` | `(colname)` | New series; raises `ValueError` if the column does not exist. |
| `sort_index()` | `(**kwargs)` | New `GenericTimeSeries` sorted by time. |
| `truncate()` | `(a, b=None, int=None)` | New series. `a` may be a `TimeRange`, a start string/value, or index integer; `b` is an optional end and `int` is a slice step. Metadata is trimmed too. |
| `concatenate()` | `(others, same_source=False, **kwargs)` | New series; accepts one series or an iterable. Data is passed through `pandas.concat` and sorted; do not assume overlapping timestamps are deduplicated. Differing source classes produce a `GenericTimeSeries`. With `same_source=True`, source classes must match or a `TypeError` is raised. Extra kwargs pass to `pandas.concat`. |
| `plot()` | `(axes=None, columns=None, **plot_args)` | Matplotlib `Axes`; data is plotted through pandas and a common unit labels the y-axis when all selected columns share one unit. |
| `peek()` | `(*, columns=None, title=None, **kwargs)` | A diagnostic Matplotlib `Figure`, wrapped by SunPy's display decorator. It rejects an empty series. |
| `quicklook()` | `()` | Writes a temporary HTML report and opens a browser. Treat as interactive and do not use in headless automation. |

`ts.data` exists but emits a warning discouraging direct use; prefer
`to_dataframe()`. Most transformations return a new object, but the returned
DataFrame from `to_dataframe()` is the actual internal DataFrame in this
release, so copy it before destructive pandas changes and reconstruct the
TimeSeries with metadata and units.

## Source loaders

The registered public classes and their `source=` selectors are:

| Selector | Class | Typical local input | Validation focus |
|---|---|---|---|
| `XRS`/`xrs` | `XRSTimeSeries` | GOES XRS FITS; relevant GOES netCDF/HDF5 | `xrsa`/`xrsb` or GOES-R quality/primary-channel columns; irradiance units; satellite metadata. |
| `EVE`/`eve` | `EVESpWxTimeSeries` | EVE L0CS text | Column names, missing-value replacement, irradiance/count units; level 0CS reader limitations. |
| `ESP`/`esp` | `ESPTimeSeries` | EVE/ESP FITS | `QD`, `CH_18`, `CH_26`, `CH_30`, `CH_36`; irradiance units. |
| `GBMSummary`/`gbmsummary` | `GBMSummaryTimeSeries` | Fermi/GBM summary FITS | Seven rebinned energy bands and `ct / s / keV` units. |
| `LYRA`/`lyra` | `LYRATimeSeries` | PROBA2/LYRA FITS | Time-unit header (`s` or `MIN`), channels, and irradiance units. |
| `NoRH`/`norh` | `NoRHTimeSeries` | NoRH FITS | Radio channel metadata and units. |
| `RHESSI`/`rhessi` | `RHESSISummaryTimeSeries` | RHESSI summary FITS | Detector units and source metadata. |
| `NOAAIndices`/`noaaindices` and `NOAAPredictIndices`/`noaapredictindices` | NOAA source classes | Supported local NOAA files | Date index, columns, and reader-specific metadata. |
| no selector | `GenericTimeSeries` for supported CDF fallback | Space Physics Guidelines-style CDF | May return multiple generic series; inspect list/object shape and units. |

These selectors are case-insensitive through the source validation logic, but
using the documented spelling improves reproducibility. A source selector does
not fetch data. Pass a local path obtained by a separate data-access workflow.

## Solar constants and models

| API | Contract |
|---|---|
| `sunpy.sun.constants.get(key)` | Returns an Astropy `Constant`; keys are strings in `constants.constants`, for example `mass`, `radius`, `luminosity`, `sidereal rotation rate`, and `mean synodic period`. |
| `sunpy.sun.constants.find(sub=None)` | Sorted list of keys containing a case-insensitive substring, or all keys for `None`. |
| `sunpy.sun.constants.print_all()` | Astropy `Table` containing key, name, value, uncertainty, unit, and reference. |
| `sunpy.sun.constants.mass`, `.radius`, `.luminosity`, `.sfu`, `.sidereal_rotation_rate` | Convenient unit-bearing constant aliases. `first_carrington_rotation` is an Astropy `Time`; `mean_synodic_period` is a constant. |
| `sunpy.sun.models.interior` / `.evolution` | Unit-bearing Astropy `QTable` model data with table metadata/source and an index. |
| `sunpy.sun.models.differential_rotation(duration, latitude, *, model='howard', frame_time='sidereal')` | `duration` quantity convertible to seconds; `latitude` quantity convertible to degrees; returns an Astropy `Longitude`. Models: `howard`, `snodgrass`, `allen`, `rigid`. Frame times: `sidereal`, `synodic`. Invalid model raises `ValueError`. |

The model accepts scalar or array latitudes. Do not pass unitless numbers to
unit-validated parameters; attach `u.day`/`u.s` and `u.deg` explicitly.

## Coordinate and map rotation helpers

- `solar_rotate_coordinate(coordinate, observer=None, time=None,
  **diff_rot_kwargs)` returns a rotated `SkyCoord`. Exactly one of `observer`
  or `time` is required. `observer` must be a frame or `SkyCoord` with a
  non-`None` `obstime`; `time=` assumes an Earth-based observer and warns.
- `differential_rotate(smap, observer=None, time=None, **diff_rot_kwargs)`
  returns a rotated `GenericMap`. It needs a map/WCS, can require scikit-image,
  rejects an entirely off-disk map, and may change dimensions for partial-disk
  maps. Route ordinary map work to `maps-and-visualization`.

The rotation model's `frame_time` keyword is distinct from the observer/time
choice in `solar_rotate_coordinate`; do not silently interpret a synodic model
as a new observer.
