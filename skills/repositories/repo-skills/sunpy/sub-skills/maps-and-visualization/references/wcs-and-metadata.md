# WCS and metadata discipline

## Minimum trustworthy contract

A SunPy map is a 2-D array plus metadata describing how pixel `(x, y)` maps to a solar coordinate. The NumPy data shape is `(y, x)`, while public pixel quantities and `make_fitswcs_header()` use Cartesian `(x, y)`. Keep these orders explicit in code and notes.

For a map intended for spatial operations, validate at least:

- `m.data.ndim == 2` and the expected `m.data.shape`.
- `m.meta`/`m.fits_header` contains usable `CUNIT1`, `CUNIT2`, `CTYPE1`, `CTYPE2`, `CRVAL1`, `CRVAL2`, `CRPIX1`, `CRPIX2`, and `CDELT1`/`CDELT2` or equivalent CD/PC representation.
- `m.spatial_units` are angular or equivalent to arcsec. GenericMap rejects missing/non-angular coordinate units.
- `m.wcs.wcs.ctype`, `m.wcs.wcs.crval`, `m.wcs.wcs.crpix`, `m.wcs.wcs.cunit`, `m.wcs.array_shape`, and `m.coordinate_frame` agree with the intended observation.
- Observer/time/solar-radius metadata are present when converting or reprojecting helioprojective data: inspect `.observer_coordinate`, `.date`, `.reference_date`, `.rsun_meters`, and `.dsun`.
- `m.reference_pixel` and `m.scale` are physically plausible and in the expected Cartesian order.

A missing frame (`m.coordinate_frame is None`) means frame-dependent calls such as `submap` with SkyCoord, `draw_grid`, or `reproject_to` may be untrustworthy. Repair or route to coordinates-and-time rather than silently substituting a frame.

## Authoring a map safely

```python
import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from sunpy.coordinates import frames
from sunpy.map import Map, make_fitswcs_header

data = np.arange(80, dtype=float).reshape(8, 10)  # (y, x)
reference = SkyCoord(
    0*u.arcsec, 0*u.arcsec, frame=frames.Helioprojective,
    obstime="2020-01-01", observer="earth",
)
header = make_fitswcs_header(
    data, reference, scale=(2, 2)*u.arcsec/u.pixel,
    instrument="synthetic", wavelength=171*u.angstrom,
)
m = Map(data, header)
```

`make_fitswcs_header()` requires an observation time and rejects heliocentric coordinates in this release. If a `SkyCoord` carries a frame, the helper uses its frame/observer to populate WCS and observer metadata. Default reference pixel is the array center; default scale is one arcsec/pixel. Pass `unit=` to set `BUNIT` or pass a quantity data array. The header helper converts zero-based reference pixels to FITS one-based `CRPIXn`.

For a custom projection, pass `projection_code='CAR'` or another valid FITS projection code and ensure the coordinate/frame is appropriate. A rotation may be specified with either `rotation_angle` or a 2x2 `rotation_matrix`, never both. Keep `MetaDict`/header and array shape paired.

## Read-only inspection and repair

When a FITS file fails map construction:

1. Read data and header without modifying the file. Keep a pristine copy: `original_header = header.copy()`.
2. Identify the exact failure and compare it to the FITS/WCS contract. Common repairs include correcting `CUNIT1/2`, `CTYPE1/2`, date-key spelling/value, or missing scale keys; do not invent observer, time, or solar-radius values without domain evidence.
3. Edit a copy (`repaired = original_header.copy()`), record each changed key and source of truth, then call `Map(data, repaired)`.
4. Validate `m.wcs`, `m.coordinate_frame`, `.spatial_units`, `.date`, `.observer_coordinate`, and pixel/world round trip. Compare the repaired map's output to expectations.
5. Save a repaired derivative only to an explicit user-approved path. Never overwrite the source file by default.

Header keys are case-insensitive in `MetaDict`/FITS headers, but canonical FITS spelling improves portability. A map can warn about missing `CTYPE` and still construct when enough metadata exists; this is not evidence that frame operations are safe. A `MapMetaValidationError` for coordinate units is a hard stop until repaired.

## Pixel/world checks

```python
world = m.pixel_to_world(4*u.pixel, 3*u.pixel)
pix = m.world_to_pixel(world)
assert np.allclose([pix.x.to_value(u.pixel), pix.y.to_value(u.pixel)], [4, 3])
```

Use the map's own `coordinate_frame` when creating an overlay coordinate. For a two-corner region, use `SkyCoord(..., frame=m.coordinate_frame)` and `m.submap(bottom_left, top_right=top_right)`. For pixel regions, use `[x, y] * u.pixel`, not array indexing order. If coordinates have a different frame or observer, transform them deliberately using the coordinates route before invoking map methods.

## Transform-specific metadata expectations

- `submap` returns a new map with a sliced array and adjusted reference pixel; it preserves dask but does not change the source.
- `resample` changes dimensions, scale, reference pixel, and NAXIS values. Check output shape and scale rather than expecting original CRPIX.
- `rotate` rewrites rotation metadata to a PC matrix and may remove CROTA/CD keywords. Output dimensions can change.
- `reproject_to` returns a new map whose metadata is based on target WCS; arbitrary source metadata is not preserved. Use `return_footprint=True` to quantify coverage. `auto_extent='corners'|'edges'|'all'` trades speed against complete extent; `'all'` can be expensive.
- `preserve_date_obs=True` requires target WCS with `DATE-AVG` or `DATE-OBS`; it preserves the source observation time while using target reference time.
- Reprojection warns on an `rsun` mismatch. Treat that as a physical-consistency issue to resolve, not a cosmetic warning.

## Validation checklist

Record input and output shapes, data dtype/unit, changed metadata keys, coordinate frame names, observer/time, WCS pixel shape, and footprint range. For plots, check the axis WCS is the intended map WCS; if plotting onto another map's axes, use `autoalign=True` only after deciding that reprojection and its cost are acceptable. Use `MPLBACKEND=Agg` and a temporary PNG for a deterministic smoke check.
