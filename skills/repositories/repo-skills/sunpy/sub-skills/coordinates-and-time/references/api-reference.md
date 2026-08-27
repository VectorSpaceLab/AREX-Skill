# Coordinates and time API reference

This reference records the public API shape used by this route. Import
`sunpy.coordinates` before using a string frame name: the import registers the
SunPy frames with Astropy's coordinate graph.

## Time API

| API | Contract and useful behavior |
|---|---|
| `sunpy.time.parse_time(time_string, *, format=None, **kwargs)` | Returns an `astropy.time.Time`. Accepts strings, string lists, Python `date`/`datetime`, tuples, NumPy datetime values/arrays, pandas time objects when pandas is installed, and existing Astropy `Time`. Extra keywords are passed to Astropy `Time`; use `scale=` for UTC/TAI/etc. |
| `format=` | Accepts Astropy formats plus SunPy `utime` (UT seconds since 1979-01-01 UTC) and `tai_seconds` (TAI seconds since 1958-01-01). Bare numeric input needs an explicit format such as `format="jd"` or `format="utime"`. |
| recognized solar strings | Common forms include ISO with `T` or a space, slashes, compact mission timestamps, day-of-year forms such as `2012:124:21:08:12`, month names, `_TAI`/`_UTC` suffixes, and leap seconds. `24:00:00` is normalized to the next day for a scalar input. |
| `sunpy.time.TimeRange(a, b=None, format=None)` | `b` may be a second time, `datetime.timedelta`, `astropy.units.Quantity`, or `astropy.time.TimeDelta`. With one sequence argument, it must contain exactly two values. Start/end are ordered so the range is positive; a negative duration is reversed. |
| `TimeRange` properties | `.start`, `.end`, `.center` are `Time`; `.dt` is a `TimeDelta`; `.days`, `.hours`, `.minutes`, `.seconds` are positive quantities. |
| `TimeRange` methods | `.split(n)` returns `n` equal closed subranges (`n >= 1`); `.window(cadence, window)` creates windows at a cadence; `.next()`/`.previous()` mutate by one duration; `.shift(dt_start, dt_end)` mutates endpoints; `.get_dates()`, `.intersects(other)`, and `time in range` are available. Endpoints are included for membership/intersection. |

For reproducible work, do not use `parse_time("now")` in a saved result.
Record the normalized `.isot` and `.scale` values. A time array can be passed to
`parse_time`, but each frame's `obstime` must be compatible with the coordinate
array shape.

## Public SunPy frame inventory

All frames inherit Astropy's frame/SkyCoord behavior. Canonical registered
string names are shown in parentheses; this version does not promise short
aliases such as `hpc` or `hgs`.

| Class (string name) | Components and frame attributes | Use |
|---|---|---|
| `HeliographicStonyhurst` (`heliographic_stonyhurst`) | `lon`, `lat`, optional `radius`; `obstime`, `rsun` | Sun-centered longitude/latitude with the Sun-Earth direction defining zero longitude. |
| `HeliographicCarrington` (`heliographic_carrington`) | `lon`, `lat`, optional `radius`; `obstime`, `observer`, `rsun` | Carrington longitude/latitude. Observer is needed for apparent transforms; `observer="self"` requires a full 3-D coordinate. |
| `Helioprojective` (`helioprojective`) | `Tx`, `Ty`, optional `distance`; `obstime`, `observer`, `rsun` | Observer-centered solar-image line of sight. `Tx` is positive toward the west limb and `Ty` toward solar north. |
| `HelioprojectiveRadial` (`helioprojectiveradial`) | `psi`, `delta`, optional `distance`; `obstime`, `observer`, `rsun`; `.theta` is impact angle | Radial/position-angle form of observer-centered solar coordinates. |
| `Heliocentric` (`heliocentric`) | Cartesian `x`, `y`, `z` by default, or cylindrical `rho`, `psi`, `z`; `obstime`, `observer` | Sun-centered, observer-oriented Cartesian coordinates (HCC). |
| `HeliocentricEarthEcliptic` (`heliocentricearthecliptic`) | spherical `lon`, `lat`, `distance`; `obstime` | Sun-centered ecliptic frame using the Earth direction. |
| `GeocentricSolarEcliptic` (`geocentricsolarecliptic`) | `lon`, `lat`, `distance`; `obstime` | Earth-centered solar-ecliptic frame. |
| `HeliocentricInertial` (`heliocentricinertial`) | `lon`, `lat`, `distance`; `obstime` | Sun-centered inertial frame aligned with the solar north pole. |
| `GeocentricEarthEquatorial` (`geocentricearthequatorial`) | `lon`, `lat`, `distance`; `obstime`, `equinox` | Earth-centered mean-equatorial frame. |
| `Geomagnetic`, `SolarMagnetic`, `GeocentricSolarMagnetospheric` | `lon`, `lat`, `distance`; `obstime`, `magnetic_model` | Earth-centered magnetic frames. The default IGRF model is `igrf13`; require a valid `obstime`. |

`SkyCoord` is the normal high-level interface:

```python
import astropy.units as u
from astropy.coordinates import SkyCoord
import sunpy.coordinates  # registers string names

hpc = SkyCoord(100*u.arcsec, 200*u.arcsec,
               frame="helioprojective", observer="earth",
               obstime="2020-01-01")
hgs = hpc.transform_to("heliographic_stonyhurst")
```

Frame attributes are available through `.frame`: `.frame.obstime`,
`.frame.observer`, and `.frame.rsun`. Coordinate components preserve their
physical units; use `.Tx`, `.Ty`, `.lon`, `.lat`, `.radius`, `.distance`, or
`.cartesian` rather than parsing `str(coord)`.

## Observer and 3-D rules

- A string observer is resolved through `get_body_heliographic_stonyhurst`
  when `obstime` is defined. Without `obstime`, it remains unresolved and
  observer-dependent operations can fail.
- A precise observer is a 3-D `SkyCoord` or frame, typically in
  `HeliographicStonyhurst`, with `radius` and `obstime` where needed. An
  observer's `obstime` supplies a missing frame time in supported constructors,
  but explicit duplication is safer for reproducible pipelines.
- `Helioprojective.make_3d()` and `HelioprojectiveRadial.make_3d()` infer a
  surface intersection. An off-disk 2-D line of sight has no unique surface
  intersection and may return NaNs or require a screen assumption.
- Heliographic 2-D coordinates can be made 3-D with `.make_3d()`, which uses
  the frame's `rsun`. Keep the same `rsun` across products before comparing
  surface positions.

## Transform and WCS helpers

Use `SkyCoord.transform_to()` or a frame's `.transform_to()`; destination
frames should carry their own `obstime`, `observer`, and `rsun` when those
attributes define the desired geometry. Public WCS registration helpers are:

- `sunpy.coordinates.solar_wcs_frame_mapping(wcs)` maps solar FITS CTYPE and
  auxiliary observer metadata to a frame.
- `sunpy.coordinates.solar_frame_to_wcs_mapping(frame, projection="TAN")`
  creates a 2-D Astropy `WCS` for supported solar frames.
- `astropy.wcs.utils.wcs_to_celestial_frame(wcs)` uses the registration after
  `import sunpy.coordinates`.

These helpers do not load image data. Map header factories, map validation,
pixel plotting, and reprojection are outside this route.

## Ephemeris and solar utilities

| API | Output/behavior |
|---|---|
| `get_body_heliographic_stonyhurst(body, time="now", observer=None, *, include_velocity=False, quiet=False)` | HGS location of a solar-system body using Astropy's built-in ephemeris. If `observer` is supplied, iteratively accounts for light-travel time; `include_velocity=True` adds differentials. |
| `get_earth(time="now", *, include_velocity=False)` | Earth as a `SkyCoord` in HGS with longitude explicitly set to zero. |
| `get_horizons_coord(...)` | JPL Horizons network query; do not assume offline/reproducible behavior. See optional-backends. |
| `sunpy.coordinates.sun.B0(time)`, `L0(time, light_travel_time_correction=True, nearest_point=True, aberration_correction=False)`, `P(time)`, `earth_distance(time)`, `angular_radius(time)` | Solar disk orientation, apparent Carrington latitude/longitude, position angle, Earth distance, and angular radius. |
| `carrington_rotation_number(t)`, `carrington_rotation_time(crot, longitude=None)` | Convert between time and fractional/integer Carrington rotation. If `longitude` is supplied, `crot` must be integral and longitude must be in `(0, 360]` degrees. |
| `sunpy.sun.models.differential_rotation(duration, latitude, *, model="howard", frame_time="sidereal")` | Deterministic longitude offset. Supported models are `howard`, `snodgrass`, `allen`, and `rigid`; pass units for duration and latitude. |

`get_body_heliographic_stonyhurst` uses an Astropy built-in ephemeris by
default. Higher-accuracy JPL ephemerides may require a separately configured
Astropy provider and network/cache access; do not silently claim that accuracy.
