---
name: maps-and-visualization
description: "Create, inspect, transform, serialize, and safely visualize SunPy
  Maps with FITS/WCS metadata, image operations, overlays, sequences, and
  composites."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 2-Clause
---

# SunPy maps and visualization

Use this route when the task involves a 2-D solar image and its metadata: constructing a `Map` from an array/header or local file, validating or repairing FITS/WCS metadata, converting pixels and world coordinates, cropping or transforming an image, saving a map, plotting a WCS-aware quicklook, adding grids/limbs/contours/rectangles, or organizing maps into a sequence/composite. Keep coordinate-frame transformations and detailed frame theory in the sibling [coordinates-and-time](../coordinates-and-time/SKILL.md) route; use [data-access-and-io](../data-access-and-io/SKILL.md) for remote search/fetch or provider-specific file retrieval.

## Route quickly

- **Array plus solar coordinate/header:** read [workflows.md](references/workflows.md) and [wcs-and-metadata.md](references/wcs-and-metadata.md); start with `sunpy.map.make_fitswcs_header()` then `sunpy.map.Map(data, header)`.
- **Local FITS/ASDF/JP2 or an existing map:** read the factory and I/O entries in [api-reference.md](references/api-reference.md). Do not use URLs or implicit downloads in a safe/headless workflow.
- **Crop, rotate, resize, superpixel, or align WCS:** read the transformation workflow and optional dependency notes in [workflows.md](references/workflows.md); preserve the original map and validate output shape/WCS.
- **Plot/overlay/quicklook:** set `MPLBACKEND=Agg` for non-interactive checks, create `subplot(projection=map)`, call `map.plot()`, then use `draw_grid`, `draw_limb`, `draw_contours`, or `draw_quadrangle`.
- **Multiple observations:** use `Map(..., sequence=True)`/`MapSequence` for ordered frames and `Map(..., composite=True)`/`CompositeMap` for layers. A sequence does not coalign maps automatically.
- **Bad metadata:** never overwrite the source header in place before preserving it. Copy the header, repair only evidence-backed keys, construct a new map, and check `map.wcs`, `coordinate_frame`, units, shape, and round-trip behavior. See [troubleshooting.md](references/troubleshooting.md).

## Core operating procedure

1. Identify the data shape/order (`numpy` is `(y, x)`), provenance, intended coordinate frame, observation time, observer, pixel scale, and desired output format. For a remote or credentialed source, route acquisition away from this skill.
2. Make or inspect the header. Use `make_fitswcs_header(data_or_shape, reference_coordinate, reference_pixel=..., scale=..., rotation_angle=..., projection_code=..., unit=...)` when metadata is being authored. The reference pixel is Cartesian `(x, y)` and zero-indexed; the generated FITS `CRPIXn` is one-indexed.
3. Construct with `sunpy.map.Map(data, header)` or `sunpy.map.Map(local_path)`. For arrays, the array must be immediately followed by a dict/FITS Header/MetaDict or `astropy.wcs.WCS`. A directory/glob can produce a list; request `sequence=True` or `composite=True` when that collection type is intended.
4. Inspect `m.data`, `m.meta`, `m.fits_header`, `m.wcs`, `m.coordinate_frame`, `m.observer_coordinate`, `m.date`, `m.reference_pixel`, `m.scale`, `m.dimensions`, and `m.unit`. Treat a missing `coordinate_frame` or metadata validation error as a stop, not as permission to guess.
5. Apply a non-mutating operation (`submap`, `rotate`, `resample`, `superpixel`, or `reproject_to`) and validate both the returned data shape and its metadata. Reprojection requires the `reproject` extra and a compatible target `WCS`/header; request `return_footprint=True` when coverage matters.
6. Save explicitly to a temporary or user-approved path with `m.save(path, filetype='auto'|'fits'|'asdf'|'jp2')`. FITS is the conservative interchange choice; ASDF preserves SunPy map structure but needs ASDF; JP2 has format-specific limits. Reload and compare shape, key WCS values, and data semantics.
7. For plots, use a WCSAxes projection (`fig.add_subplot(projection=m)`), then `m.plot(axes=ax, ...)`. Set `MPLBACKEND=Agg` and save a figure for headless validation. `peek()`/`quicklook()` are convenience display actions and may open a browser/window; do not use them in automated or server contexts.

## Validation signals

A successful map workflow has a 2-D output, angular spatial units equivalent to arcsec, a valid `m.wcs` with the expected `array_shape`, a non-`None` frame when world-coordinate operations are required, and expected shape/data/footprint changes. A successful plot has a WCSAxes axis, no GUI requirement under `MPLBACKEND=Agg`, and a saved image. A successful round trip reloads as a `GenericMap` or appropriate registered source subclass and retains the intended WCS metadata.

## Choose the representation deliberately

- Use a **single `GenericMap`** for one observation or a synthetic image with one WCS.
- Use a **`MapSequence`** when time-ordered frames should remain separately inspectable. Check dates and shape consistency; it is a container, not a coalignment algorithm.
- Use a **`CompositeMap`** when several layers should share one plot. Reproject layers to a common WCS before scientific comparison, then set alpha/z-order/levels explicitly.
- Use **array-only `sunpy.image` functions** only when WCS metadata is intentionally not needed. Otherwise prefer a `GenericMap` method so scale, reference pixel, and WCS changes are carried forward.
- Use a **static plot** for reports/tests and reserve `peek`, `quicklook`, animations, and point-selection tools for an explicitly interactive user session.

## Output contract

When handing off a derived map, report the input provenance, source and output shapes, operation/method, changed WCS/header keys, coordinate frame and observer/time, units, reprojection algorithm/footprint if applicable, and output path. For a figure report the backend, WCS projection, normalization/clip interval, overlays, and saved image path. If an optional dependency or physical metadata is unavailable, state the blocked capability and the safe fallback rather than silently changing the operation.

## Limits and boundaries

Map supports 2-D image data; higher-dimensional inputs are truncated by `GenericMap` to the first two dimensions with a warning. `resample`, `rotate`, and `reproject_to` do not preserve dask arrays. `MapSequence.plot` creates a Matplotlib animation and `quicklook`/interactive point selection are not safe defaults. Reprojection can be expensive and changes metadata to WCS-associated values; remote data, large mission downloads, credentials, and interactive GUI work are deliberately excluded.

## Recovery order

If a workflow fails, first reduce it to a tiny in-memory map and print the data shape, header keys, coordinate frame, WCS shape, and optional-import status. Next isolate metadata errors from plotting errors by constructing the map and checking `m.wcs` before importing pyplot. Then validate a crop or static plot before adding reprojection, overlays, or a sequence. Restore complexity one operation at a time and keep the original map/header available for comparison. Read [troubleshooting.md](references/troubleshooting.md) before installing extras or suppressing warnings.

## Bundled checks

Run `python scripts/map_smoke.py --help` to inspect the safe command. Run `MPLBACKEND=Agg python scripts/map_smoke.py --check` for an in-memory constructor, metadata/WCS checks, crop/resample, tiny FITS round-trip, reprojection when available, and a headless PNG plot. Run `python scripts/validate_map_metadata.py --help` or pass a local FITS/ASDF path to validate without modifying it. These scripts use only temporary files and tiny arrays.

## References

- [api-reference.md](references/api-reference.md) — exact public classes/functions, signatures, return types, and optional extras; read before selecting an API.
- [workflows.md](references/workflows.md) — end-to-end construction, repair, transformation, overlay, sequence/composite, I/O, and headless plot recipes.
- [wcs-and-metadata.md](references/wcs-and-metadata.md) — metadata contract, frame/observer access, repair discipline, and validation checklist.
- [troubleshooting.md](references/troubleshooting.md) — installation/import, optional dependency, data/config, API misuse, plotting, WCS, and operation-specific recovery.
- [scripts/map_smoke.py](scripts/map_smoke.py) — safe in-memory and headless smoke check; use for a quick local signal.
- [scripts/validate_map_metadata.py](scripts/validate_map_metadata.py) — read-only metadata/WCS validator for a local map file.
