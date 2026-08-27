# Tables and I/O Workflows

## QTable with Units and ECSV Round-Trip

```python
from astropy import units as u
from astropy.table import QTable

t = QTable({"wave": [500, 600] * u.nm, "flux": [1.2, 2.3] * u.Jy})
t.meta["instrument"] = "demo"
t.write("out.ecsv", format="ascii.ecsv", overwrite=True)
rt = QTable.read("out.ecsv", format="ascii.ecsv")
assert rt["wave"].unit == u.nm
```

Use ECSV when metadata, units, and mixin columns must survive text-file
round-trips.

## Table Joins and Grouping

```python
from astropy.table import Table, join

left = Table({"id": [1, 2], "mag": [15.1, 16.2]})
right = Table({"id": [1, 2], "color": [0.4, 0.7]})
merged = join(left, right, keys="id")
```

Check join keys and duplicate behavior before trusting row order.

## FITS Image Write/Read

```python
import numpy as np
from astropy.io import fits

hdu = fits.PrimaryHDU(np.arange(4, dtype=np.float32).reshape(2, 2))
hdu.header["BUNIT"] = "ct"
hdu.writeto("image.fits", overwrite=True, output_verify="exception")
with fits.open("image.fits", memmap=True) as hdul:
    data = hdul[0].data
    header = hdul[0].header
```

Use `output_verify="exception"` when generating files that should be strict.
Inspect warnings for legacy files rather than ignoring them globally.

## FITS Table HDU

```python
from astropy.io import fits
from astropy.table import Table

t = Table({"id": [1, 2], "flux": [3.4, 5.6]})
hdu = fits.BinTableHDU(t, name="CATALOG")
hdu.writeto("catalog.fits", overwrite=True)
```

When reading multi-HDU files, specify extension name or index.

## Optional Format Integrations

- HDF5 uses `format="hdf5"` and generally needs `h5py`.
- Parquet uses `format="parquet"` and needs `pyarrow`.
- Remote URLs/S3 may need `fsspec`/`s3fs` and explicit credentials or anonymous settings.
- Pandas/dataframe conversion may need optional packages and can lose Astropy
  mixin semantics; validate units and times after conversion.

Install only the integration needed for the user's requested format.
