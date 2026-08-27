# Deterministic workflows

Use these recipes for local, bounded analysis. They intentionally separate
object construction from acquisition and avoid sample-data managers, network
URLs, credentials, browser windows, and large files.

## 1. Build and validate a synthetic series

```python
import pandas as pd
import astropy.units as u
from sunpy.timeseries import GenericTimeSeries

index = pd.date_range("2020-01-01T00:00:00", periods=4, freq="min")
df = pd.DataFrame(
    {"flux": [1.0, 2.0, 3.0, 4.0], "counts": [10, 11, 9, 12]},
    index=index,
)
ts = GenericTimeSeries(
    df,
    meta={"instrument": "synthetic", "purpose": "local smoke"},
    units={"flux": u.W / u.m**2, "counts": u.ct},
)
assert ts.shape == (4, 2)
assert ts.time_range.start.isot.startswith("2020-01-01T00:00:00")
assert ts.quantity("flux").unit == u.W / u.m**2
```

Expected observations: the object is a `GenericTimeSeries`; `columns` follows
the DataFrame order; `time_range` uses the index extrema; `meta.metadata` has
one entry associated with both columns; every column has a unit. If a column is
omitted from `units`, SunPy warns and assigns a dimensionless unit. Treat that
as a data-quality issue, not as proof that the physical quantity is
unitless.

## 2. Convert between DataFrame, Table, and array

```python
df_again = ts.to_dataframe().copy()
table = ts.to_table()
array = ts.to_array()
assert list(table.colnames) == ["date", "flux", "counts"]
assert table["flux"].unit == u.W / u.m**2
assert array.shape == df_again.shape
```

The `date` column is added to the Astropy Table; it is not an additional
DataFrame value column. To round-trip a Table into a series, make its time
column first (or its single primary-key index), then use `TimeSeries(table)`.
A Table with more than one index column is rejected. When a Table contains
quantity columns, units are inferred; explicit metadata/units may be supplied
and are merged by the factory.

## 3. Add, extract, truncate, and resample

```python
from sunpy.time import TimeRange

flux = ts.quantity("flux")
with_extra = ts.add_column("double_flux", 2 * flux)
flux_only = with_extra.extract("flux")
window = with_extra.truncate(TimeRange("2020-01-01 00:01", "2020-01-01 00:02"))

# Resampling is a pandas operation, followed by explicit reconstruction.
downsampled_df = with_extra.to_dataframe().resample("2min").mean()
downsampled = GenericTimeSeries(downsampled_df, with_extra.meta, with_extra.units)
```

`add_column`, `extract`, `truncate`, and `concatenate` return new series. The
metadata is narrowed during truncation and merged during concatenation. For a
newly computed column, add the correct unit; when aggregating, confirm that the
operation preserves the intended dimensional meaning. If a resampling method
changes columns or drops all rows, update metadata/units and validate before
reconstruction.

## 4. Concatenate local intervals

```python
first = ts.truncate(0, 2)
second = ts.truncate(2, 4)
combined = first.concatenate(second)
assert combined.time_range.start == first.time_range.start
assert set(combined.columns) == set(ts.columns)
```

For files from the same instrument, the factory can combine paths:

```python
combined = TimeSeries([path1, path2], source="XRS", concatenate=True)
```

Use `same_source=True` when a source-class match is a safety requirement. If
series have different source classes, the general concatenate operation can
produce a generic series, while `same_source=True` deliberately raises
`TypeError`. Check for overlapping/duplicate times and inspect the metadata
entries after the merge.

## 5. Headless plotting

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ts.plot(axes=ax, columns=["flux"])
fig.savefig("timeseries-check.png", dpi=120)
plt.close(fig)
```

Use a temporary output path in automation and clean it up. `plot()` returns an
Axes, while `peek()` returns a diagnostic Figure through SunPy's display
wrapper. A series with zero rows cannot be plotted. `quicklook()` creates an
HTML file and invokes `webbrowser.open_new_tab`; do not use it in a service,
CI, or notebook-free environment.

## 6. Load a local mission file

The acquisition route is responsible for finding/fetching a file. Once the
path is local:

```python
from pathlib import Path
from sunpy.timeseries import TimeSeries

series = TimeSeries(Path(local_file), source="XRS")
if isinstance(series, list):
    raise ValueError("Expected one local source series; inspect the list first")
print(series.__class__.__name__, series.columns, series.time_range)
for name in series.columns:
    print(name, series.units[name], series.quantity(name).shape)
```

Use the source table in `api-reference.md` for EVE, ESP, GBM, LYRA, NoRH,
RHESSI, NOAA, and GOES. For a CDF, first check that the optional CDF reader is
installed; `TimeSeries(path)` may produce several generic objects. Never infer
units from the file name. Validate each unit and resolve unknown CDF units
before calculation.

## 7. Compute solar rotation deterministically

For a model-only calculation, no coordinates, maps, or network are needed:

```python
import astropy.units as u
from sunpy.sun.models import differential_rotation

longitude_change = differential_rotation(
    2 * u.day, 30 * u.deg, model="howard", frame_time="sidereal"
)
print(longitude_change.to(u.deg))
```

Compare models explicitly when the scientific question warrants it:
`howard`, `snodgrass`, `allen`, and `rigid`. A synodic calculation subtracts
the approximate Earth orbital contribution, so record `frame_time` in the
analysis output.

For an existing valid coordinate, use one of these mutually exclusive modes:

```python
from sunpy.physics.differential_rotation import solar_rotate_coordinate

rotated = solar_rotate_coordinate(coord, time="2020-01-02T00:00:00")
# Or: rotated = solar_rotate_coordinate(coord, observer=new_observer)
```

`time=` assumes an Earth observer and warns. `observer=` is required for a
non-Earth observer and must carry an `obstime`. Do not combine both arguments.
Frame creation, observer construction, and transformations belong to the
coordinates route.
