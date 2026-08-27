# Installation and configuration

## Choose the smallest variant

The package distribution is `sunpy`, imported as `sunpy`, and requires Python
3.12 or newer in this source baseline. Use an isolated virtual environment or
Conda prefix; do not install into a system interpreter with `sudo`.

| Need | Extra | Main surfaces |
|---|---|---|
| Base package, time, coordinates, solar constants, basic I/O | none | `sunpy`, `sunpy.time`, `sunpy.coordinates`, `sunpy.sun`, `sunpy.physics` |
| Array/image operations | `image` | SciPy-backed image helpers |
| Map/WCS plotting, reprojection, map source classes | `map` | Matplotlib, reproject, SciPy, mpl-animators |
| Fido and provider clients | `net` | BeautifulSoup, DRMS, date utilities, tqdm, Zeep |
| TimeSeries formats and plotting | `timeseries` | CDF, HDF5/NetCDF, pandas, Matplotlib |
| Visualization without the full map stack | `visualization` | Matplotlib and animation helpers |
| ASDF map/coordinate serialization | `asdf` | ASDF and ASDF-Astropy |
| JPEG2000 map files | `jpeg2000` | Glymur and lxml; a native JPEG2000 library may still be needed |
| SPICE coordinate support | `spice` | SpiceyPy plus mission kernels supplied separately |
| OpenCV or scikit-image helpers | `opencv` / `scikit-image` | Optional image processing |
| All core user extras | `all` | `core` plus ASDF, JPEG2000, OpenCV, SPICE, and scikit-image |
| S3 remote files | `s3` | fsspec S3 stack and cloud clients; credentials/network required |
| Notebook widgets/tables | `jupyter` | Jupyter presentation helpers |

For pip, select only what the route needs, for example:

```bash
python -m pip install 'sunpy[map,net,timeseries]'
```

`sunpy[all]` is convenient for broad local inspection but is larger than a
single workflow needs. `s3` and `jupyter` are not included in `all`.

## Verify without network

```python
import numpy as np
import pandas as pd
import astropy.units as u
from sunpy.time import parse_time, TimeRange
from sunpy.coordinates import Helioprojective
from sunpy.map import Map, make_fitswcs_header
from sunpy.timeseries import GenericTimeSeries

frame = Helioprojective(observer="earth", obstime="2020-01-01")
assert parse_time("2020-01-01").scale == "utc"
assert TimeRange("2020-01-01", "2020-01-02").dt.sec == 86400
```

For a Map, create a header with `make_fitswcs_header()` and construct
`Map(array, header)`; for a local generic series use a pandas DataFrame with a
time-like index and `GenericTimeSeries(dataframe, units=...)`. A bare dict passed
to the `TimeSeries` factory is not a generic series constructor.

## Configuration and diagnostics

SunPy reads a user configuration file from its platform-specific config
location. Use `sunpy.print_config()` to locate it and `sunpy.config` to inspect
loaded values. Set `SUNPY_CONFIGDIR` before importing SunPy when a separate
configuration directory is required. Keep configuration changes local to the
project or session when reproducing a problem.

Use `sunpy.__version__`, `sunpy.__file__`, and `sunpy.system_info()` when
reporting an issue. `sunpy.log` is the package logger; set its level in the
calling application rather than modifying source defaults. Record Python,
SunPy, Astropy, NumPy, optional-extra versions, operating system, and the
smallest standalone reproducer.

## Environment boundaries

The optional extras are ordinary Python/scientific dependencies; SunPy core has
no required CUDA/ROCm/MPS backend. A visible GPU does not change the install
plan. Network providers, S3, SPICE kernels, and native codecs need separate
runtime checks. Do not claim those capabilities from a successful base import.
