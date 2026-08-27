# Data-source API reference

This reference is a compact operating reference for the public source and
adapter contracts. It intentionally names representative classes rather than
claiming an exhaustive catalogue.

## Four source protocols

```python
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pyarrow as pa
import torch
import xarray as xr

class DataSource:
    def __call__(self, time, variable) -> xr.DataArray: ...
    async def fetch(self, time, variable) -> xr.DataArray: ...

class ForecastSource:
    def __call__(self, time, lead_time, variable) -> xr.DataArray: ...
    async def fetch(self, time, lead_time, variable) -> xr.DataArray: ...

class DataFrameSource:
    SCHEMA: pa.Schema
    def __call__(self, time, variable, fields=None) -> pd.DataFrame: ...
    async def fetch(self, time, variable, fields=None) -> pd.DataFrame: ...

class ForecastFrameSource:
    SCHEMA: pa.Schema
    def __call__(self, time, lead_time, variable, fields=None) -> pd.DataFrame: ...
    async def fetch(self, time, lead_time, variable, fields=None) -> pd.DataFrame: ...
```

The accepted input types are broader than the abbreviated code above:
`time` may be a `datetime`, list of datetimes, or `TimeArray` (a NumPy
`datetime64` array); `variable` may be a string, list, or `VariableArray`;
`lead_time` may be a `timedelta`, list, or `LeadTimeArray` (a NumPy
`timedelta64` array). `fields` may be a string, list, `pa.Schema`, or `None`.

Use `__call__` for synchronous code. Use `await source.fetch(...)` only after
checking the object supports an async implementation. A runtime-checkable
protocol is an interface shape, not proof that the source can serve a
particular variable or date.

## Input normalization

The data helpers normalize NumPy/Pandas time values to Python datetimes and
convert timezone-aware values to naive UTC. A naive datetime is assumed to be
UTC. `prep_forecast_inputs` converts NumPy timedeltas to Python `timedelta`
values and then applies the ordinary time/variable normalization.

For a source with a native `lead_time` parameter, the request is one call:

```python
forecast_da = forecast_source(
    np.array([np.datetime64("2024-01-01T00:00")]),
    np.array([np.timedelta64(0, "h"), np.timedelta64(6, "h")]),
    np.array(["t2m", "u10m"]),
)
```

For a plain DataSource, `fetch_data` obtains each requested valid time
`time + lead_time`, adds a lead dimension, and concatenates the results. This
is useful, but it is not equivalent to a native forecast product when the
source has different valid-time semantics.

## Utility functions

### `fetch_data`

```python
fetch_data(
    source,
    time: TimeArray,
    variable: VariableArray,
    lead_time: LeadTimeArray = np.array([np.timedelta64(0, "h")]),
    device: torch.device = "cpu",
    interp_to: CoordSystem | None = None,
    interp_method: str = "nearest",
    legacy: bool = True,
) -> tuple[torch.Tensor, CoordSystem] | xr.DataArray
```

- `legacy=True` returns a Torch tensor plus an ordered coordinate mapping.
- `legacy=False` returns an Xarray DataArray; `interp_to` is rejected in this
  mode. CPU data uses NumPy-backed values; CUDA requires CuPy.
- With `interp_to`, rectilinear inputs use Xarray interpolation. A curvilinear
  input (2-D latitude/longitude coordinates) requires `interp_method="linear"`;
  other methods raise a `ValueError`.
- A CUDA legacy request requires a working Torch CUDA device. This helper moves
  values; it does not validate model variable compatibility.

### `fetch_dataframe`

```python
fetch_dataframe(
    source,
    time: TimeArray,
    variable: VariableArray,
    fields: FieldArray | None = None,
    lead_time: LeadTimeArray = np.array([np.timedelta64(0, "h")]),
    device: torch.device = "cpu",
) -> pd.DataFrame | cudf.DataFrame
```

A ForecastFrameSource receives `time, lead_time, variable, fields`. A plain
DataFrameSource receives the unique set of `time + lead_time` values and does
not receive lead time. The returned DataFrame gets `attrs` containing
`request_time` and `request_lead_time`. CUDA conversion requires `cudf` (and
its CUDA dependencies); otherwise keep `device="cpu"`.

### `prep_data_array`

```python
prep_data_array(
    da: xr.DataArray,
    device: torch.device = "cpu",
    interp_to: CoordSystem | None = None,
    interp_method: str = "nearest",
) -> tuple[torch.Tensor, CoordSystem]
```

The coordinate mapping is built from Xarray coordinates. `time`, `lead_time`,
and `variable` remain metadata dimensions; other dimensions/coordinates are
included for downstream spatial handling. Curvilinear latitude/longitude are
preserved as coordinate arrays; when interpolating, target coordinates are
stored as `_lat` and `_lon`.

## Local adapters

All of these are synchronous DataSource-shaped adapters and use Xarray
selection. The local path is supplied by the caller and is not downloaded by
the adapter.

| Adapter | Constructor | Required local shape/behavior |
|---|---|---|
| `DataArrayFile` | `DataArrayFile(file_path, **xr_args)` | Opens a DataArray-compatible file with `time` and `variable`. |
| `DataSetFile` | `DataSetFile(file_path, array_name, **xr_args)` | Opens one named DataArray from a Dataset. |
| `DataArrayDirectory` | `DataArrayDirectory(dir_path, **xr_args)` | Reads files under year/month directories; selection is by requested year/month. |
| `DataArrayPathList` | `DataArrayPathList(paths, **xr_args)` | Opens a glob or explicit file list; files must agree and provide `time`, `variable`, `lat`, `lon`. |
| `InferenceOutputSource` | `InferenceOutputSource(dataset_or_path, filter_dict={}, **xr_args)` | Converts a Dataset to `variable`; filters extra dimensions and resolves `time`/`lead_time`. |

`DataArrayFile`, `DataSetFile`, and the multi-file adapters use exact Xarray
`.sel`-style coordinate selection. A missing coordinate commonly raises a
selection error; this is not a tolerance search.

`InferenceOutputSource` accepts an Xarray Dataset or a path readable by
`xarray.open_dataset`. After `filter_dict`, it requires `time`, `lead_time`, and
`variable`. It rejects data where both `time` and `lead_time` have length > 1.
If `lead_time` has length 1, it adds that lead to every time and drops the lead
dimension. Otherwise it broadcasts the single time across leads, computes
valid times, removes the time dimension, and renames lead to time.

## Deterministic local fixtures

`Constant(domain_coords, value=1)` returns a non-random DataArray with
`time`, `variable`, and the supplied domain coordinates. `Constant_FX` adds
`lead_time`. `Random` and `Random_FX` have the same shape contracts but random
values. `RandomDataFrame(n_obs=10, tolerance=np.timedelta64(0), schema=None,
field_generators=None)` produces a tabular source with a default schema of
`time`, `lat`, `lon`, `observation`, and `variable`. Its tolerance is symmetric
and only controls generated observation timestamps; it is not an asymmetric
production observation matcher.

These fixtures are appropriate for protocol and shape checks without network,
credentials, a model checkpoint, or a cloud cache.

## Source family routing

Representative public classes include:

- Reanalysis/cloud grids: `ARCO`, `WB2ERA5`, `WB2ERA5_32x64`,
  `WB2ERA5_121x240`, `WB2Climatology`, `NCAR_ERA5`, `CDS`, `CMIP6`.
- Forecast/analysis products: `GFS`, `GFS_FX`, `HRRR`, `HRRR_FX`, `IFS`,
  `IFS_FX`, `GEFS_FX`, `CFS_FX`, and selected dynamical variants.
- Observation frames: `GHCNDaily`, `GHCNHourly`, `ISD`, `IEM_ASOS`,
  `NomadsGDASObsConv`, `UFSObsConv`, `NNJAObsConv`, and satellite sounder
  frame classes.
- Satellite/radar/cloud: `GOES`, `GOESGLM`, `HimawariAHI`, `MeteosatFCI`,
  `JPSS`, `MetOp*`, `MRMS`, `OPERA`, and Planetary Computer adapters.

This list is intentionally representative. Consult the installed package's
public API for the exact constructor and source-specific coverage before use.
Most remote families need the optional `data` dependency group; that group
contains the package set for GRIB/BUFR, STAC/raster, object-store, and service
access, but individual sources can still require a narrower optional package,
credential, or backend. Do not infer that a class is usable merely because its
name imports.
