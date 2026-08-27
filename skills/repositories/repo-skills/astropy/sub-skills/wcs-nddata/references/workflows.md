# WCS and NDData Workflows

## Build and Validate a Simple WCS

```python
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

header = fits.Header()
header["NAXIS"] = 2
header["CTYPE1"] = "RA---TAN"
header["CTYPE2"] = "DEC--TAN"
header["CRVAL1"] = 0.0
header["CRVAL2"] = 0.0
header["CRPIX1"] = 1.0
header["CRPIX2"] = 1.0
header["CDELT1"] = -0.1
header["CDELT2"] = 0.1

w = WCS(header)
world = w.all_pix2world([[0, 0]], 0)
pix = w.all_world2pix(world, 0)
assert np.allclose(pix, [[0, 0]], atol=1e-6)
```

State whether coordinates use origin `0` or `1`.

## High-Level WCS Objects

```python
sky = w.pixel_to_world(0, 0)
x, y = w.world_to_pixel(sky)
```

Prefer this when the caller wants `SkyCoord`/`Quantity` objects. Use
`array_index_to_world` for NumPy array indices.

## Create NDData with WCS and Uncertainty

```python
import numpy as np
from astropy import units as u
from astropy.nddata import NDData, StdDevUncertainty

nd = NDData(np.ones((2, 2)), unit=u.ct,
            uncertainty=StdDevUncertainty(np.ones((2, 2)) * 0.1),
            mask=np.array([[False, True], [False, False]]),
            wcs=w, meta={"object": "demo"})
```

Verify data, mask, uncertainty, unit, metadata, and WCS shape alignment.

## CCDData FITS Round-Trip

```python
from astropy import units as u
from astropy.nddata import CCDData

ccd = CCDData([[1, 2], [3, 4]], unit=u.adu, wcs=w)
ccd.write("ccd.fits", overwrite=True)
rt = CCDData.read("ccd.fits")
assert rt.unit == u.adu
```

Use temporary files for smoke checks and inspect warnings for non-standard FITS
headers.

## WCS Validation CLI

```bash
wcslint image.fits
```

Use this as a diagnostic. Follow it with a numeric round-trip relevant to the
user's pixel and world domain.
