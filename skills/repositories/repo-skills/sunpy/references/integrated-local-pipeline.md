# Integrated local Map and TimeSeries pipeline

Use this recipe when a local 2-D solar array, an observation time, and a small
set of time-indexed measurements need to be kept consistent. It deliberately
uses no sample data, Fido, provider, or network call. For frame theory read the
coordinates route; for detailed Map/WCS operations read the maps route; for
TimeSeries source readers read the TimeSeries route.

```python
from pathlib import Path
import tempfile

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord

from sunpy.coordinates import Helioprojective
from sunpy.map import Map, make_fitswcs_header
from sunpy.time import parse_time
from sunpy.timeseries import GenericTimeSeries

# Use one explicit instant in both the image metadata and measurement index.
t0 = parse_time("2020-01-01T00:00:00")
frame = Helioprojective(observer="earth", obstime=t0, rsun=695700 * u.km)
reference = SkyCoord(0 * u.arcsec, 0 * u.arcsec, frame=frame)
data = np.arange(64, dtype=float).reshape(8, 8)  # (y, x)
header = make_fitswcs_header(
    data,
    reference,
    scale=u.Quantity([2, 2], u.arcsec / u.pixel),
    unit=u.ct,
)
solar_map = Map(data, header)

# Snapshot before deriving a new map; submap() should not mutate this object.
original_data = solar_map.data.copy()
original_shape = solar_map.data.shape
original_date = solar_map.date
original_ctype = list(solar_map.wcs.wcs.ctype)
original_crpix = tuple(solar_map.wcs.wcs.crpix)
bottom_left = SkyCoord(-4 * u.arcsec, -4 * u.arcsec, frame=solar_map.coordinate_frame)
top_right = SkyCoord(4 * u.arcsec, 4 * u.arcsec, frame=solar_map.coordinate_frame)
cropped = solar_map.submap(bottom_left, top_right=top_right)
assert cropped is not solar_map
assert np.array_equal(solar_map.data, original_data)
assert solar_map.data.shape == original_shape
assert np.isclose((solar_map.date - original_date).to_value(u.s), 0)
assert list(solar_map.wcs.wcs.ctype) == original_ctype
assert np.allclose(solar_map.wcs.wcs.crpix, original_crpix)

# Save and reload only to an explicit temporary or user-approved path.
with tempfile.TemporaryDirectory(prefix="sunpy-local-pipeline-") as directory:
    fits_path = Path(directory) / "solar-map.fits"
    solar_map.save(fits_path, filetype="fits")
    reloaded = Map(fits_path)
    assert reloaded.data.shape == (8, 8)
    assert reloaded.unit.is_equivalent(u.ct)
    assert reloaded.wcs.array_shape == (8, 8)
    assert reloaded.coordinate_frame.name == "helioprojective"
    assert list(reloaded.wcs.wcs.ctype) == ["HPLN-TAN", "HPLT-TAN"]
    assert np.isclose((reloaded.date - t0).to_value(u.s), 0)

# A generic local series uses a time-indexed DataFrame, not a bare dict.
index = pd.DatetimeIndex([t0.datetime, (t0 + 1 * u.hour).datetime])
series = GenericTimeSeries(
    pd.DataFrame({"flux": [1.0, 2.0]}, index=index),
    meta={"instrument": "synthetic"},
    units={"flux": u.W / u.m**2},
)
assert np.isclose((series.time_range.start - t0).to_value(u.s), 0)
assert np.isclose((series.time_range.end - (t0 + 1 * u.hour)).to_value(u.s), 0)
assert series.quantity("flux").unit.is_equivalent(u.W / u.m**2)
assert series.to_dataframe().shape == (2, 1)
```

The array unit is declared in the WCS header (`BUNIT=ct`), while the series
unit is declared in its `units` mapping. If the input file is remote, first use
the data-access route to obtain it under an explicit network/destination policy;
this local recipe is not a substitute for provider or calibration validation.
For a headless plot, prefix the command with `MPLBACKEND=Agg` and save/close the
figure rather than calling `peek()` or `quicklook()`.
