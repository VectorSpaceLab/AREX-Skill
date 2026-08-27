# Coordinates and time troubleshooting

## Install and import

| Symptom | Likely cause | Recovery and validation |
|---|---|---|
| `ModuleNotFoundError: sunpy` or `astropy` | Core package is absent or the wrong interpreter is active | Install the supported SunPy package in the active environment; run `python -c 'import sunpy, astropy; print(sunpy.__version__)'`. Do not diagnose from a different Python. |
| `SkyCoord(..., frame="helioprojective")` says unknown frame | `sunpy.coordinates` was not imported, so frame registration did not occur | `import sunpy.coordinates` before constructing string frames, or pass the imported class directly. Verify `SkyCoord(...).frame.name`. |
| `sunpy.coordinates.spice` import fails | `spiceypy` is optional | Install/verify the optional dependency only for a kernel-backed workflow. Core SunPy coordinate transforms do not require it. |
| a magnetic frame fails with a time-related error | `obstime` is missing or invalid | Supply a valid observation time and verify `.frame.obstime`; do not substitute a fixed year for a historical observation. |

## Optional dependencies and external data

- A core time/frame failure must not be “fixed” by downloading SPICE kernels or
  querying Horizons. First reproduce with `get_earth()` and the built-in body
  ephemeris.
- `get_horizons_coord()` and JPL ephemeris providers can fail from network or
  service availability. Record the query/provider and retry only under an
  approved external-data budget.
- SPICE frame names and kernel coverage are data-dependent. Inspect the loaded
  kernel set and epoch coverage before interpreting a transform; no kernel
  means no valid spacecraft geometry.

## Data, configuration, and WCS

| Symptom | Likely cause | Recovery |
|---|---|---|
| WCS cannot map to a solar frame | Missing/invalid solar CTYPE pair or observer/date/`rsun` auxiliary metadata | Inspect `wcs.wcs.ctype`, `dateobs`/`dateavg`, and solar observer fields. Use `solar_frame_to_wcs_mapping()` for a minimal frame-derived WCS. For header repair or pixel coordinates, route to maps. |
| frame comparison differs by tens of arcseconds | Different light-travel-time, aberration, observer, or Carrington conventions | Make `observer`, `obstime`, `rsun`, `L0(..., light_travel_time_correction=..., aberration_correction=...)`, and provider explicit before comparing. |
| time is off by hours or a numeric epoch is implausible | Wrong scale or missing numeric `format=` | Reparse with an explicit `format` and `scale`; compare `.isot`, `.jd`, and `.scale`, not the input string. |

## API misuse and metadata errors

| Error/symptom | Diagnosis | Recovery |
|---|---|---|
| `ConvertError` or “observer must be defined” | HPC/HCC/HPR transform lacks a resolvable observer | Add `observer="earth"` plus `obstime`, or supply a fully defined 3-D HGS observer coordinate. Check both source and destination frames. |
| observer string remains a string or body lookup fails | `obstime` is absent/invalid, or the body name is unsupported by Astropy | Supply a fixed `obstime`; use a supported solar-system body or an explicit observer coordinate. |
| `observer="self"` raises a full-3-D error | HGC self-observer geometry cannot be derived from a 2-D coordinate | Supply `radius`/Cartesian 3-D data and `obstime`; use a normal observer for a surface direction. |
| unexpected NaN from `make_3d()` | The 2-D HPC/HPR line of sight is off the solar disk or has insufficient observer metadata | Supply an actual distance, use `SphericalScreen`/`PlanarScreen` for the intended off-limb assumption, or keep the coordinate 2-D and do not claim a surface location. |
| components have surprising names/units | Frame representation differs from the chosen frame | Use `Tx`/`Ty` for HPC, `psi`/`delta` for HPR, `lon`/`lat`/`radius` for heliographic, and `x`/`y`/`z` for HCC; inspect `.representation_type` and convert units explicitly. |
| `TimeRange` rejects a one-item tuple or has reversed endpoints | Constructor requires two values and always stores a positive range | Pass exactly two values or a duration; use the original input separately if order has scientific meaning. |
| `TimeRange.split(0)` fails | `n` must be at least one | Use `n >= 1`; validate the number of returned intervals. |

## Workflow-specific failures

### Transforming HPC/HGS/HGC

First print a compact metadata record:

```python
print(coord.frame.name, coord.frame.obstime, coord.frame.observer,
      getattr(coord.frame, "rsun", None), coord.shape)
```

If any required observer/time is `None`, repair the source/destination frame.
For round trips, keep the same observer, time, and `rsun`; otherwise the
numerical difference can be physical rather than an implementation failure.

### Propagating a feature

A plain transform to a frame with a different time moves only the coordinate
representation with the evolving frame. It does not advance the feature. Use
`propagate_with_solar_surface`, `RotatedSunFrame`, or
`solar_rotate_coordinate` and record the selected model (`howard`, `snodgrass`,
`allen`, or `rigid`). The context manager also follows the translational solar
center; `transform_with_sun_center()` handles only that translation.

If a coordinate includes velocity differentials, remember that frame
transforms can rotate the velocity representation but do not use velocity to
move the position across time. Propagation and velocity integration are
separate claims.

### WCS interaction

`solar_frame_to_wcs_mapping()` creates axes and frame metadata, not a complete
image WCS. If `world_to_pixel()` or plotting fails, the missing reference
pixel/scale/data shape is a map/WCS construction issue. Do not patch private
WCS or SunPy attributes from this route.

### Reproducibility

Replace `"now"` with a recorded time, pin the ephemeris/provider choice, state
whether positions are true or light-time corrected, and print units. For
external SPICE/Horizons results, preserve kernel/query provenance outside the
runtime skill.
