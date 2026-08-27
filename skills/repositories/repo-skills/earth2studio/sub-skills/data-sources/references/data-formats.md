# Data formats and validation

## Gridded Xarray results

A `DataSource` returns an `xarray.DataArray` with named coordinates. At
minimum, use `time` and `variable`; a ForecastSource additionally uses
`lead_time`. Built-ins generally add spatial dimensions such as `lat` and
`lon`, but satellite, radar, native-level, and observation products can use
other named coordinates or 2-D curvilinear latitude/longitude coordinates.

Named dimensions, coordinate values, and the `variable` labels are the source
of truth. Do not index by an assumed positional order without inspecting
`da.dims` and `da.coords`. In particular, source implementations can construct
forecast arrays as `time, lead_time, variable, ...`, while interface prose may
show the conceptual dimensions in another order.

Validate a returned array before downstream use:

```python
import inspect

expected = {"time", "variable"}
if "lead_time" in inspect.signature(source.__call__).parameters:
    expected.add("lead_time")
missing = expected - set(da.dims)
if missing:
    raise ValueError(f"source result lacks dimensions: {sorted(missing)}")
if list(map(str, da.coords["variable"].values)) != requested_variables:
    raise ValueError("source did not return requested variable labels")
```

The signature check above is only a dispatch hint; a source can still be
misconfigured. Check the actual result and source documentation. Use
`np.asarray(da.values)` or `da.load()` only when the requested data size is
known. Remote arrays may be lazy or backed by downloaded chunks.

### Spatial coordinates

- Rectilinear grids expose one-dimensional `lat` and `lon` dimensions.
- Curvilinear grids may expose 2-D `lat`/`lon` coordinates attached to other
  dimensions. `prep_data_array` preserves these coordinates and its
  interpolation helper requires linear interpolation for curvilinear input.
- Downstream coordinate mappings can use `_lat`/`_lon` for a requested target
  grid. Do not silently assume longitude convention (`0..360` versus
  `-180..180`) or latitude direction; inspect the returned coordinates.
- Pressure-level IDs (`t850`, `z500`) encode a level in the variable ID; a
  source-native level coordinate is not interchangeable with a different
  source's custom level.

### Time and forecast coordinates

A plain source request is indexed by the requested observation/analysis times.
A native ForecastSource has initialization `time` and `lead_time`; valid time
is conceptually `time + lead_time`, but do not replace the two coordinates
unless the source contract explicitly calls for valid-time selection.

`fetch_data` adapts a plain source by requesting `time + lead` for each lead,
then assigns the original request time and a lead coordinate. This is a
convenience adapter, not a source-side forecast query.

For `InferenceOutputSource`, first filter extra coordinates (for example an
ensemble member) so one of `time` and `lead_time` has length one. The adapter
then creates a single valid-time coordinate. If both dimensions remain longer
than one, select a subset instead of attempting to broadcast a 2-D forecast.

## DataFrame results

A `DataFrameSource` or `ForecastFrameSource` returns rows, not a gridded tensor.
Typical columns include:

- `time`: observation timestamp;
- `variable`: requested Earth2Studio variable ID;
- `lat`, `lon`, `elev`: location metadata;
- `observation` or a source-specific value field;
- station, instrument, type, quality, pressure-quality, level category, or
  product metadata.

The source's `SCHEMA` is a PyArrow schema. It defines field names, types, and
sometimes metadata used to map native product names. `fields=None` selects all
supported fields. Passing a string, list, or compatible `pa.Schema` selects a
subset. A robust caller compares requested names and PyArrow types against
`source.SCHEMA` before fetching.

```python
import pyarrow as pa

fields = ["time", "lat", "lon", "observation", "variable"]
for name in fields:
    if name not in source.SCHEMA.names:
        raise ValueError(f"unsupported field {name!r}")
df = source(request_time, ["t2m"], fields=fields)
assert set(fields) == set(df.columns)
```

Some observation classes expose `resolve_fields` as a public helper. When
present, use it to validate a requested field list or schema; otherwise
validate against `SCHEMA` and let the source enforce exact types. A schema
field with the right name but a wrong type is a contract error, not a coercion
request.

`fetch_dataframe` adds `df.attrs["request_time"]` and
`df.attrs["request_lead_time"]`. Preserve these attributes if the request
metadata is needed for matching or scoring.

## Time-tolerance semantics

The common `TimeTolerance` shape is one `timedelta`/`np.timedelta64` or a
2-tuple of bounds. A scalar `tol` normalizes to `(-tol, +tol)`. A tuple is
used as supplied after conversion and must satisfy `lower <= upper`. For a
requested time `t`, a matching observation lies in the inclusive interval:

```text
[t + lower_bound, t + upper_bound]
```

A tuple such as `(timedelta(hours=-1), timedelta(hours=6))` is asymmetric:
records one hour before through six hours after the request are eligible. Do
not turn it into a symmetric six-hour window. Not every source exposes a
`tolerance` argument; exact-match Xarray sources use coordinate selection.

An empty DataFrame can be a valid result when no record falls in the interval.
Check source range, cycle/file availability, variable mapping, and timezone
normalization before widening the interval. If multiple records match, the
source's product-specific behavior controls ordering and deduplication; do not
assume the nearest record unless documented.

## Local file conventions

### One DataArray

A minimal local file for `DataArrayFile` contains dimensions/coordinates like:

```python
xr.DataArray(
    data=np.zeros((1, 1, 2, 3), dtype=np.float32),
    dims=["time", "variable", "lat", "lon"],
    coords={
        "time": [np.datetime64("2024-01-01T00:00")],
        "variable": ["t2m"],
        "lat": [-1.0, 1.0],
        "lon": [0.0, 1.0, 2.0],
    },
).to_netcdf("fixture.nc")
```

`DataArrayFile("fixture.nc")` opens it and `source(time, variable)` selects
coordinates. `DataSetFile` uses the same coordinate expectations but selects a
named array from a Dataset.

### Directory and multi-file sources

`DataArrayDirectory` expects year directories containing files whose names
carry a month token, such as a `2024/2024_01.nc` layout. Every requested time
is routed to its year/month file. Missing directories, months, or coordinate
values fail during initialization or selection.

`DataArrayPathList` accepts a glob string or explicit list. All files must be
readable and structurally consistent. Its validation requires `time`,
`variable`, `lat`, and `lon`; a file with only time and variable is sufficient
for `DataArrayFile` but not for this multi-file adapter.

### Inference output adapter

`InferenceOutputSource` converts Dataset data variables into a `variable`
dimension. Use `filter_dict` for dimensions such as ensemble. Required
selection and transformation rules are:

1. after filtering, `time`, `lead_time`, and `variable` must exist;
2. both `time` and `lead_time` cannot have length > 1;
3. one-length lead is added to each time; or one-length time is broadcast to
   each lead;
4. the result contains one `time` dimension of valid timestamps.

This adapter is for reading an already local/staged output; it does not fetch
or download a model result.

## Offline fixture checks

Use the bundled script from any working directory:

```bash
python /path/to/local_source_smoke.py --help
python /path/to/local_source_smoke.py
python /path/to/local_source_smoke.py --path ./fixture.nc --time 2024-01-01T00:00:00 --variable t2m
```

The default mode creates a temporary tiny NetCDF fixture, reads it through
`DataArrayFile`, and validates coordinate selection. It removes only its own
temporary file. The `--path` mode reads an explicitly supplied local file and
performs no network operation.
