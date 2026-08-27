---
name: data-sources
description: "Select, validate, and use Earth2Studio gridded, forecast,
  observational, tabular, satellite, cloud-store, and local data sources without
  confusing source contracts or variable lexicons."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Earth2Studio data sources

Use this skill when a workflow must choose or call an Earth2Studio data source,
forecast source, tabular observation source, or local Xarray source. It teaches
source selection, request-shape validation, lexicon translation, time windows,
and safe offline checks. It does **not** run model inference, select a prognostic/
diagnostic model, or perform full remote downloads.

## Decide the source contract first

Choose the smallest contract that matches the data:

| Need | Interface | Call | Result |
|---|---|---|---|
| Gridded analysis/initial state | `DataSource` | `(time, variable)` | `xarray.DataArray` |
| Forecast product with explicit origin and lead | `ForecastSource` | `(time, lead_time, variable)` | `xarray.DataArray` |
| Sparse observations or metadata | `DataFrameSource` | `(time, variable, fields=None)` | `pandas.DataFrame` |
| Sparse forecast observations | `ForecastFrameSource` | `(time, lead_time, variable, fields=None)` | `pandas.DataFrame` |

A DataSource's array normally has `time`, `variable`, then spatial/product
coordinates. A ForecastSource adds `lead_time`; DataFrame sources expose
`SCHEMA`, and `fields` must be a subset. Do not pass a forecast source to an
API expecting a plain source, or vice versa.

For a source choice, record product family, time coverage/cadence, variable
vocabulary, grid, output type, cache policy, optional dependencies,
credentials, and network policy. The built-in catalogue is broad but not
exhaustive; availability, licenses, historical range, and variable support
vary. See [api-reference.md](references/api-reference.md) for representative
families and decision-level prerequisites.

## Request data with normalized coordinates

1. Use UTC request times. A single `datetime`, list, or NumPy datetime array is
   accepted. Time normalization converts timezone-aware values to naive UTC;
   naive values are treated as UTC.
2. Use Earth2Studio variable IDs, not a backend's native field spelling. Pass a
   string or an ordered list/array of strings.
3. For a forecast source, pass a `timedelta`, list, or NumPy timedelta array as
   `lead_time`; preserve the distinction between initialization `time` and
   valid time `time + lead_time`.
4. Inspect the returned coordinates and shape before handing data onward:
   requested time and variable IDs should be represented, and forecast output
   must contain `lead_time`. Do not assume every source supports every ID,
   cadence, level, or lead.
5. For observation/tabular sources, request only needed `fields` after checking
   `source.SCHEMA`. A DataFrame can contain observation values, `time`,
   `variable`, `lat`, `lon`, `elev`, station/type, quality, or product-specific
   metadata; it is not an N-D grid.

The source's synchronous `__call__` is normal. If it supports `fetch`,
`await source.fetch(...)` has the same contract for an async caller or bounded
batch. Do not assume every source has an async implementation.

## Use the lexicon as the compatibility boundary

Earth2Studio IDs such as `t2m`, `u10m`, `v10m`, `msl`, `z500`, and `tcwv` are
standardized vocabulary entries, not promises that every source provides them.
Each source has a source-specific lexicon mapping an Earth2Studio ID to a
backend key, selector, or compound route. A lexicon may also attach a modifier
for unit, sign, decomposition, accumulation, or representation conversion.

Before a remote or local request:

- Verify every requested ID is in the selected source lexicon; a missing ID is
  a source capability error, not a reason to guess a native backend name.
- Read the mapped route and modifier behavior when units or levels matter.
- Treat pressure suffixes (`z500`, `t850`) as pressure levels, `m` suffixes
  (`u10m`) as height above surface, and `k`-style native levels as
  source/use-case-specific. Do not interpolate or compare custom levels as if
  they were interchangeable.
- Preserve source output variable coordinates as Earth2Studio IDs. If writing
  a custom source, map native names internally and return standardized IDs.

The mapping patterns and a missing-variable synthetic example are in
[lexicon-reference.md](references/lexicon-reference.md).

## Choose among source families

Use these families for routing, not as an exhaustive model/data list:

- **Gridded reanalysis/cloud stores:** ARCO, WeatherBench2 (`WB2ERA5` variants),
  NCAR/ERA5, CDS, CMIP6, and similar products. Check the `data` extra, date
  range, cache, and grid/level support. Large requests may download or cache
  substantial data.
- **Gridded analyses and forecasts:** GFS/GFS_FX, HRRR/HRRR_FX, IFS/IFS_FX,
  GEFS, CFS, and dynamical/forecast variants. Use a ForecastSource only when
  the source exposes explicit lead time; validate cycle/lead availability and
  whether a variable exists only for positive leads.
- **Observation/tabular:** GHCN daily/hourly, ISD, IEM ASOS, GDAS conventional,
  UFS/NNJA observation sources, and satellite sounder frames. Check the
  PyArrow schema, station/product scope, and tolerance window. Product-specific
  extras can include BUFR, GRIB, raster/STAC, or service clients.
- **Satellite, radar, and cloud imagery:** GOES/GOES GLM, Himawari, Meteosat,
  JPSS/MetOp, MRMS, OPERA, and Planetary Computer adapters. These generally
  need the `data` extra plus service-specific availability and may require
  public-cloud access, STAC metadata, or credentials. Confirm the sensor
  lexicon and spatial coordinates before requesting data.
- **Local/offline:** `DataArrayFile`, `DataSetFile`, `DataArrayDirectory`,
  `DataArrayPathList`, `InferenceOutputSource`, `Constant`, `Constant_FX`,
  `Random`, `Random_FX`, and `RandomDataFrame`. Prefer these for reproducible
  smoke tests, air-gapped runs, and pre-staged datasets.

Remote constructors may be cheap while construction; the first call can open
stores, list objects, download bytes, decode products, and populate a cache.
Keep credentials, network policy, cache location, and data license explicit;
never put credentials in a lexicon, source constructor, command line, or skill.

## Adapt source data for downstream utilities

Use `fetch_data(source, time, variable, lead_time=..., device=..., interp_to=...,
interp_method=..., legacy=...)` to obtain inference-ready data. It detects a
`lead_time` parameter; a plain DataSource is called at `time + lead` and
assembled with a lead dimension. `legacy=True` returns `(torch.Tensor,
CoordSystem)`; `legacy=False` returns Xarray, rejects `interp_to`, and needs
CuPy for CUDA. Curvilinear interpolation requires `interp_method="linear"`.

Use `fetch_dataframe(source, time, variable, fields=..., lead_time=..., device=...)`
for tabular sources; it attaches request metadata in `df.attrs`, returns pandas
on CPU, and needs CuPy/cuDF on CUDA. `prep_data_array` converts an existing
DataArray to `(tensor, CoordSystem)`. Exact signatures are in
[api-reference.md](references/api-reference.md); formats are in
[data-formats.md](references/data-formats.md).

## Local/offline workflow

1. Build or obtain a local Xarray file/store with `time` and `variable`, plus
   `lat`/`lon` or documented spatial coordinates when needed.
2. Use `DataArrayFile(path)` or `DataSetFile(path, array_name)`; use
   `DataArrayDirectory` for the year/month convention and `DataArrayPathList`
   for consistent multi-file collections (requiring `time`, `variable`,
   `lat`, and `lon`).
3. For outputs with `time` and `lead_time`, use `InferenceOutputSource` after
   filtering extras so one of those dimensions has length one.
4. Select one known time/variable and assert dimensions, labels, dtype, finite
   values, and equality. Run the bundled `--help` and tiny-fixture check; it
   never contacts a remote store.

Example shape (the exact spatial dimensions are source-dependent):

```python
from collections import OrderedDict
from datetime import datetime
import numpy as np
from earth2studio.data import Constant, Constant_FX, fetch_data

# A local deterministic fixture; no network or model package is needed.
source = Constant(OrderedDict([("lat", np.array([0.])), ("lon", np.array([0.]))]))
da = source(datetime(2024, 1, 1), ["t2m"])
forecast = Constant_FX(OrderedDict([("lat", np.array([0.])), ("lon", np.array([0.]))]))
x, coords = fetch_data(forecast, np.array([np.datetime64("2024-01-01")]),
                       np.array(["t2m"]),
                       lead_time=np.array([np.timedelta64(0, "h")]))
```

The snippet is intentionally a shape pattern, not an inference workflow. For
a fuller local file check, use [scripts/local_source_smoke.py](scripts/local_source_smoke.py).

## Time windows, tolerance, and recovery

A time tolerance is a selection policy, not a resampling instruction. Sources
that support it accept one `timedelta`/`np.timedelta64` for symmetric
`[-tol, +tol]`, or a `(lower, upper)` tuple for asymmetric bounds. Bounds must
satisfy `lower <= upper`; negative lower and positive upper are normal. The
observation row timestamp must be checked against the intended interval, and
empty results are not proof that a nearby record exists.

`TimeWindow` wraps a plain DataSource (not a ForecastSource) and fetches fixed
offsets, appending configured suffixes such as `_tm1`, `_t`, `_tp1`. It requires
non-empty equal-length `offsets`/`suffixes`; `group_by` controls output order.
Underlying missing-time and missing-variable behavior is preserved. See
[troubleshooting.md](references/troubleshooting.md) before widening a window or
changing a source.

Classify failures before retrying: missing lexicon ID, invalid schema/field,
unsupported time/lead, empty tolerance match, missing optional package,
credential/network failure, or malformed local dimensions. Fix the class-specific
cause; do not guess a backend name or silently widen time bounds.

## Limits and handoff

This sub-skill intentionally omits model inference, full remote acquisition,
credential setup, exhaustive source/model matrices, and backend-specific
network operations. It does not guarantee that a named family is installed or
that a public endpoint is reachable. For source construction, use the
repository's separate datasource-development workflow; for model execution,
route to the model/inference skill. Candidate native checks include the random,
constant, local-Xarray, TimeWindow, and lexicon tests; they are evidence for
validation planning, not a replacement for a request-specific source check.
