---
name: coordinates-and-time
description: "Parse solar times, build SunPy coordinate frames, transform
  observer-aware coordinates, and propagate solar features safely."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 2-Clause
---

# Coordinates and time

Use this route when a user needs to normalize solar observation times, describe a
solar or observer-centered position, convert between SunPy/Astropy frames, query
deterministic solar-system geometry, or move a solar-surface feature with a
specified rotation model. The deliverable is normally an `astropy.time.Time`, a
`sunpy.time.TimeRange`, an `astropy.coordinates.SkyCoord`, or a reproducible
array of those objects.

Start with the [SunPy router](../../SKILL.md) when the request also needs map
construction/plotting, Fido search/fetch, or TimeSeries analysis. Those are
separate routes; this skill can consume a map's already-built
`coordinate_frame` but does not create or plot maps.

## Route by intent

| User intent | Start here | Primary result |
|---|---|---|
| Parse a FITS/solar timestamp or compare intervals | [time workflow](references/workflows.md#1-normalize-times-and-build-ranges) | `Time` or `TimeRange` |
| Make a coordinate from angles, pixels-as-angles, or Cartesian data | [frame construction](references/workflows.md#2-construct-and-validate-a-coordinate) | unit-aware `SkyCoord` |
| Convert HPC/HGS/HGC/HCC or an Astropy frame | [transformation workflow](references/workflows.md#3-transform-between-solar-frames) | transformed `SkyCoord` |
| Obtain Earth/planet geometry or solar orientation | [ephemeris workflow](references/workflows.md#4-use-ephemeris-and-solar-utilities) | observer coordinate or solar quantity |
| Use a map WCS as a coordinate frame | [WCS boundary](references/workflows.md#5-interact-with-wcs-without-building-a-map) | frame/WCS conversion only |
| Track a feature over time or apply differential rotation | [propagation workflow](references/workflows.md#6-propagate-a-solar-surface-feature) | rotated coordinate(s) |
| Use mission SPICE kernels | Read [optional backends](references/optional-backends.md) first | explicitly optional, kernel-dependent |

## Operating rules

1. Normalize every user-supplied time with `sunpy.time.parse_time` before
   comparing, adding durations, or putting it in a frame. Preserve the intended
   scale (`utc`, `tai`, etc.) and use an explicit `format=` for numeric epochs.
2. Attach `obstime` to every observer-dependent frame. Attach `observer` as a
   known body string (for example, `"earth"`) only when the time is known, or as
   a fully defined Heliographic Stonyhurst coordinate for a spacecraft or
   precise location.
3. Use physical units on every coordinate component. Never pass bare numbers to
   `SkyCoord` or a frame. Keep `rsun` explicit when comparing data products that
   use different solar radii.
4. Treat a two-dimensional Helioprojective coordinate as a line of sight, not a
   unique 3-D point. On-disk `make_3d()` assumes the solar surface; off-limb
   geometry needs a documented `PlanarScreen` or `SphericalScreen` assumption.
5. Transform with `.transform_to(destination_frame)`. For observer changes,
   make both source and destination observers/times explicit. Do not call the
   low-level functions in `sunpy.coordinates._transformations` directly.
6. Validate outputs by checking frame name, `obstime`, observer, component units,
   shape, finiteness, and (when meaningful) a round trip. A changed longitude
   after changing `obstime` is normally frame evolution, not motion of the
   object; use a propagation context or `RotatedSunFrame` when physical solar
   rotation is intended.

## Progressive disclosure

- Read [API reference](references/api-reference.md) for component names,
  frame attributes, signatures, time formats, and deterministic solar helpers.
- Read [workflows](references/workflows.md) for copyable input/output patterns,
  validation signals, and recovery steps.
- Read [troubleshooting](references/troubleshooting.md) when imports, optional
  packages, incomplete metadata, invalid dimensions, or off-limb transforms
  fail.
- Read [optional backends](references/optional-backends.md) before SPICE,
  Horizons, JPL ephemerides, or any network/kernel-dependent geometry.
- Run the bundled [coordinate/time smoke helper](scripts/coordinate_time_smoke.py)
  when a small local transform and differential-rotation check is useful. It
  uses fixed in-memory inputs, prints machine-checkable summary lines, and does
  not fetch data.

## Scope boundaries and limitations

Map header creation, pixel/WCS plotting, and reprojection belong to the maps
route; Fido and remote data acquisition belong to data access; TimeSeries
index/data operations belong to the TimeSeries route. SPICE kernels and
`get_horizons_coord()` are documentation-only here because they require
external kernels or a network service. Magnetic frames may require a valid
observation time and use the packaged IGRF data; they are not a substitute for
mission-specific magnetic-field models.
