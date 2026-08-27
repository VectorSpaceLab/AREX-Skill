# Map and visualization workflows

All examples are local and deterministic unless noted. Use `MPLBACKEND=Agg` on headless systems. The coordinate-frame construction in these recipes is deliberately minimal; use the coordinates-and-time route for frame transformations or observer theory.

## 1. Construct and inspect a tiny map

```python
import numpy as np
import astropy.units as u
from astropy.coordinates import SkyCoord
from sunpy.coordinates import frames
from sunpy.map import Map, make_fitswcs_header

data = np.arange(80, dtype=float).reshape(8, 10)
coord = SkyCoord(0*u.arcsec, 0*u.arcsec, frame=frames.Helioprojective,
                 obstime='2020-01-01', observer='earth')
header = make_fitswcs_header(data, coord, scale=(2, 2)*u.arcsec/u.pixel,
                             instrument='synthetic', wavelength=171*u.angstrom)
m = Map(data, header)
print(m.data.shape, m.coordinate_frame, m.observer_coordinate)
print(m.wcs, m.reference_pixel, m.scale, m.date)
```

Expected signals: `GenericMap`, shape `(8, 10)`, angular spatial units, an inferred helioprojective frame, and `m.wcs.array_shape == (8, 10)`. A map made from a shape tuple uses `(y, x)` for the shape but still exposes Cartesian `(x, y)` reference pixels.

## 2. Load local input or make a sequence/composite

```python
from sunpy.map import Map
single = Map('/approved/local/file.fits')
items = Map(['/approved/local/a.fits', '/approved/local/b.fits'])
seq = Map(items, sequence=True, sortby='date')
comp = Map(items, composite=True)
```

In a reusable script, replace paths with command-line inputs and reject URLs by default. `Map(path)` can read FITS and optional ASDF/JP2 files when their readers/dependencies are installed. `Map(directory_or_glob)` may return a list. `Map(..., allow_errors=True)` warns and skips failed members; record the skipped paths and require at least one valid map. `MapSequence` requires already constructed map objects, sorts by date by default, and does not coalign them. `CompositeMap` is a layer stack: set `alpha`, `zorder`, or contour `levels` before plotting.

## 3. Repair a header without damaging source data

```python
from astropy.io import fits
from sunpy.map import Map

with fits.open(input_path) as hdul:
    data = hdul[0].data.copy()
    original = hdul[0].header.copy()
repaired = original.copy()
repaired['CUNIT1'] = 'arcsec'
repaired['CUNIT2'] = 'arcsec'
fixed = Map(data, repaired)
```

Only make changes justified by an instrument specification or another trusted record. Save a repair log containing changed keys, old/new values, and rationale. Validate `fixed.coordinate_frame`, `fixed.wcs`, `fixed.spatial_units`, and a pixel/world round trip. If required observer/time or coordinate units remain unknown, stop. See [wcs-and-metadata.md](wcs-and-metadata.md).

## 4. Crop, rotate, resample, and superpixel

```python
import astropy.units as u

cut = m.submap([2, 2]*u.pixel, top_right=[7, 6]*u.pixel)
small = cut.resample((3, 4)*u.pixel, method='linear')
rotated = small.rotate(angle=10*u.deg, order=1, method='scipy')
block = rotated.superpixel((2, 2)*u.pixel, func=np.mean)
```

Validate every output independently. `submap` pixel bounds are Cartesian and include pixels intersecting the rectangle; `resample` dimensions are `(x, y)` and update WCS scale; `rotate` may change shape and uses interpolation; `superpixel` aggregates blocks and may trim incomplete blocks. Keep source and derived maps separate. `spline` resampling with non-finite input can turn much/all of the output into NaN; use `linear`/`nearest` or clean data deliberately.

For array-only processing, `sunpy.image.resample.resample(array, (new_y, new_x), method=...)` keeps NumPy `(y, x)` order and returns an array without WCS. `sunpy.image.transform.affine_transform()` also returns only an array; use a Map method when metadata must follow the operation.

## 5. Reproject to a target WCS

```python
from sunpy.map import make_fitswcs_header

target_header = make_fitswcs_header(
    (6, 7), coord, reference_pixel=(3, 2)*u.pixel,
    scale=(3, 3)*u.arcsec/u.pixel,
)
out, footprint = m.reproject_to(
    target_header, algorithm='interpolation', return_footprint=True,
)
assert out.data.shape == (6, 7)
assert footprint.shape == (6, 7)
```

The target can be a dict/header or `astropy.wcs.WCS`. Algorithms are `interpolation`, `adaptive`, and `exact`; exact/adaptive may be more expensive. `auto_extent='corners'`, `'edges'`, or `'all'` expands/shifts output to cover source geometry, with increasing work and coverage. Check `footprint` values: `0` means no valid source coverage, `1` full coverage, intermediate values partial. Verify observer, dates, solar radius, and WCS compatibility before interpreting physical results. `preserve_date_obs=True` needs target `DATE-AVG` or `DATE-OBS`.

If `import reproject` fails, install/enable the map/reproject extra in an isolated environment or report reprojection unavailable; do not replace it with a pixel resize and call that alignment.

## 6. Headless WCS plot and overlays

```python
import matplotlib.pyplot as plt

fig = plt.figure(figsize=(5, 4))
ax = fig.add_subplot(projection=m)
m.plot(axes=ax, clip_interval=(1, 99)*u.percent, cmap='gray')
m.draw_grid(axes=ax, grid_spacing=15*u.deg, system='stonyhurst')
m.draw_limb(axes=ax, color='yellow')
m.draw_contours([20, 50], axes=ax, colors='cyan')
m.draw_quadrangle([2, 2]*u.pixel, top_right=[7, 6]*u.pixel,
                  axes=ax, edgecolor='red')
fig.savefig(output_png, dpi=120)
plt.close(fig)
```

Use `fig.add_subplot(projection=m)` so the axis is WCS-aware. To customize native WCSAxes grids, use `ax.coords[0].grid(...)` and `ax.coords[1].grid(...)`; ordinary Matplotlib grid calls may not affect the coordinate overlays. `draw_grid` is a heliographic overlay and has different semantics from the default helioprojective coordinate grid. `draw_contours` levels are data values unless passing appropriate contour arguments. For a second map on the same WCSAxes, explicitly reproject it or accept `autoalign=True` and validate the result.

`peek()` and `quicklook()` are convenience display/browser methods, not deterministic server-side output. Use `plot` + `savefig` in tests and batch pipelines. Interactive point selection is intentionally excluded.

## 7. Save and reload

```python
from pathlib import Path
out = Path(temp_dir) / 'tiny.fits'
m.save(out)
reloaded = Map(out)
assert reloaded.data.shape == m.data.shape
assert reloaded.wcs.wcs.ctype == m.wcs.wcs.ctype
```

Use `.asdf` only when ASDF is installed and the consumer needs richer SunPy object serialization; ASDF reload commonly returns a `GenericMap` unless a registered source class is available. FITS is the safer interchange format. JP2 support is optional and saving casts data to uint8, so do not use it when preserving scientific numeric values matters. Never overwrite a source file by default.
