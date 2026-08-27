# Map, image, and visualization API reference

Read this reference before relying on a signature or return type. The signatures below are from the inspected SunPy 0.1.dev1+gd2ae0740e package and should be treated as version-specific.

## Factory and containers

| API | Signature / behavior | Use and output |
|---|---|---|
| `sunpy.map.Map` | `Map(*args, composite=False, sequence=False, allow_errors=False, **kwargs)` | Factory for local paths, pathlib paths, directories/globs, existing maps, `(data, header)` or `(data, WCS)`, and data followed immediately by metadata/WCS. One map returns a `GenericMap`/registered subclass; multiple inputs return a list unless `sequence` or `composite` is set. URLs are supported by the package but are outside safe runtime use here. |
| `sunpy.map.GenericMap` | `GenericMap(data, header, plot_settings=None, **kwargs)` | 2-D data plus FITS-like metadata. Inspect `.data`, `.meta`, `.fits_header`, `.plot_settings`; do not assume source-specific subclass behavior. |
| `sunpy.map.MapSequence` | `MapSequence(*args, sortby='date')` | Ordered list of already-constructed maps. `sortby=None` preserves supplied ordering; default sorts by `.date`. `maps`, `data`, `meta`, `all_same_shape`, `plot`, `peek`, and templated `save` are available. It does not coalign frames. |
| `sunpy.map.CompositeMap` | `CompositeMap(*args, **kwargs)` | Layered maps. Use `add_map`, `remove_map`, `get_map`, `set_alpha`, `set_levels`, `set_zorder`, `set_plot_settings`, `plot`, `peek`, `draw_limb`, and `draw_grid`. Alpha must be in `[0, 1]`; levels make a layer contour-like. |

### Factory input rules

- A NumPy array is not a filename list. It must be followed immediately by a dict/`MetaDict`/FITS `Header` or an `astropy.wcs.WCS`; otherwise `Map` raises `ValueError`.
- A tuple `(data, header)` or `(data, WCS)` is accepted. A WCS is converted to a relaxed FITS header for map construction.
- A local file can contain multiple 2-D HDUs; a directory/glob/list can produce multiple maps. `allow_errors=True` warns and skips failing inputs, but still raises if no maps remain; use this only when skipped inputs are acceptable and recorded.
- `Map(..., sequence=True)` passes remaining keyword arguments to `MapSequence`; `sortby='date'` is the default. `Map(..., composite=True)` creates a `CompositeMap`.

## Header construction and WCS

`sunpy.map.make_fitswcs_header(data, coordinate, reference_pixel=None, scale=None, rotation_angle=None, rotation_matrix=None, instrument=None, telescope=None, observatory=None, detector=None, wavelength=None, exposure=None, projection_code='TAN', unit=None)` returns a `MetaDict`. `data` can be an array/quantity or shape tuple in NumPy order `(y, x)`. `coordinate` is an `astropy.coordinates.SkyCoord` or SunPy frame with `obstime`; heliocentric coordinates are rejected. `reference_pixel` and `scale` are Cartesian `(x, y)` quantities. Do not pass both `rotation_angle` and `rotation_matrix`.

A constructed map exposes:

- `.wcs`: an `astropy.wcs.WCS` synthesized from map metadata; `.wcs.array_shape` follows the data.
- `.coordinate_frame`: a frame inferred from WCS, or `None` with a warning if inference fails.
- `.observer_coordinate`, `.date`, `.reference_date`, `.reference_pixel`, `.scale`, `.spatial_units`, `.coordinate_system`, `.dimensions`, `.unit`, `.wavelength`, `.instrument`, `.observatory`, `.detector`, `.exposure_time`.
- `.world_to_pixel(coordinate)`: returns a `PixelPair` with pixel quantities.
- `.pixel_to_world(x, y)`: quantity-input pixels, returns a world `SkyCoord`.

`GenericMap` validates that both spatial units exist and are angular/equivalent to arcsec. `ctype`, `crval`, `crpix`, scale, observer/time, and solar radius metadata must be physically coherent for reliable transformations.

## Transform and I/O methods

| API | Signature | Important behavior |
|---|---|---|
| `submap` | `m.submap(bottom_left, *, top_right=None, width=None, height=None)` | Returns a new map. Coordinates can be `SkyCoord`/frame or pixel quantities. Pixel pairs use Cartesian `(x, y)`, not NumPy `(row, column)`. Supply `top_right` or both `width` and `height`, not both modes. Preserves dask arrays. |
| `resample` | `m.resample(dimensions: u.pixel, method='linear')` | New map with dimensions in `(x, y)` order. Methods are `nearest`, `linear`, `spline`; updates scale and reference-pixel metadata. Does not preserve dask. |
| `superpixel` | `m.superpixel(dimensions: u.pixel, offset=(0, 0)*u.pixel, func=np.sum, conservative_mask=False)` | Aggregates non-overlapping pixel blocks; dimensions/offset are Cartesian quantities at the public API. Inspect output shape/scale and mask semantics. |
| `rotate` | `m.rotate(angle=None, rmatrix=None, order=3, scale=1.0, recenter=False, missing=np.nan, *, method='scipy', clip=True)` | Returns new rotated/rescaled map. Supply angle or matrix, not both; neither means derotate according to metadata. Methods include `scipy`, and optional `scikit-image`/`opencv` when installed. Does not preserve dask. |
| `reproject_to` | `m.reproject_to(target_wcs, *, algorithm='interpolation', return_footprint=False, auto_extent=None, preserve_date_obs=False, **reproject_args)` | `target_wcs` is a dict/header or WCS. Algorithms: `interpolation`, `adaptive`, `exact`. `auto_extent`: `None`, `corners`, `edges`, `all`. Returns map, or `(map, footprint)` when requested. Requires the `reproject` extra. Output retains WCS-associated metadata, not arbitrary metadata. Does not preserve dask. |
| `save` | `m.save(filepath, filetype='auto', **kwargs)` | Infers from extension. FITS, ASDF, and JP2 are supported where dependencies/codecs exist. ASDF stores the map under `sunpymap`; JP2 casts to uint8 and is not a lossless metadata/data interchange choice. |
| `plot` | `m.plot(*, annotate=True, axes=None, title=True, autoalign=True, clip_interval=None, **imshow_kwargs)` | Plots on WCSAxes; use `projection=m`. `clip_interval` is a two-value percentage quantity. `autoalign=True` can invoke reprojection for different WCS. |
| `peek` | `m.peek(draw_limb=False, draw_grid=False, colorbar=True, **matplot_args)` | Convenience display, often GUI-oriented. Use only interactively; use `plot` plus `savefig` for headless checks. |

## Overlays and utility functions

- `m.draw_grid(axes=None, grid_spacing=15*u.deg, annotate=True, system='stonyhurst', **kwargs)` draws a heliographic grid. `system` can be selected explicitly, such as `carrington`; kwargs pass to plotting infrastructure.
- `m.draw_limb(axes=None, resolution=1000, **kwargs)` draws the apparent solar limb.
- `m.draw_contours(levels, axes=None, fill=False, **contour_args)` draws contours in the map WCS.
- `m.draw_quadrangle(bottom_left, width=None, height=None, axes=None, top_right=None, **kwargs)` draws a rectangle in world or pixel coordinates.
- `m.draw_extent(axes=None, **kwargs)` outlines a map's footprint on WCSAxes.
- `sunpy.map.maputils.sample_at_coords(m, coordinates)`, `all_coordinates_from_map(m)`, `contains_full_disk(m)`, `contains_solar_center(m)`, and `contains_coordinate(m, coordinates)` are useful for data-coordinate validation. Use only when their preconditions (usually a helioprojective map) are satisfied.
- `sunpy.image.resample.resample(array, dimensions, method='linear', center=False, minusone=False)` returns a NumPy array and requires the same number of dimensions; methods are `nearest`, `linear`, `spline`.
- `sunpy.image.resample.reshape_image_to_4d_superpixel(img, dimensions, offset)` returns a 4-D view useful for block aggregation; dimensions and offset are NumPy `(y, x)` order here.
- `sunpy.image.transform.affine_transform(image, rmatrix, order=3, scale=1.0, image_center=None, recenter=False, missing=np.nan, *, method='scipy', clip=True)` transforms a 2-D NumPy array without map metadata. Available transform methods depend on installed optional libraries.
- `sunpy.visualization.drawing.limb`, `equator`, `prime_meridian`, and `extent` draw lower-level overlays on supplied axes/WCS. `sunpy.visualization.colormaps.cmlist` is the registered colormap mapping; `show_colormaps(search=None)` displays a catalog and is not a headless validation API.

## Dependency map

- Core map import: `sunpy[map]` (package-specific map source readers plus WCS plotting dependencies).
- Image routines: `sunpy[image]` (SciPy and image helpers).
- WCS-aware plotting: `sunpy[visualization]`/Matplotlib plus Astropy WCSAxes.
- Reprojection: `sunpy[map]` includes `reproject>=0.14.0` in this version; verify `import reproject` before claiming it is available.
- ASDF serialization: `sunpy[asdf]`; JP2: `sunpy[jpeg2000]`; OpenCV and scikit-image rotation choices: their respective optional extras. Missing optional packages should produce a bounded fallback or an explicit limitation, not a source checkout dependency.
