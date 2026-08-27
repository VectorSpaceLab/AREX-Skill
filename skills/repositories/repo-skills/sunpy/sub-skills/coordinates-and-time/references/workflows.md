# Coordinates and time workflows

All examples are local and use fixed dates. Replace values only after deciding
which observer, time scale, solar radius, and physical interpretation apply.
Expected validation signals are included so a caller can distinguish a valid
result from a merely printable object.

## 1. Normalize times and build ranges

**Input:** a timestamp, optional scale/format, or two endpoints/duration.
**Output:** an Astropy `Time` or SunPy `TimeRange`.

```python
import astropy.units as u
from sunpy.time import TimeRange, parse_time

t = parse_time("2012:124:21:08:12", scale="tai")
assert t.scale == "tai"
assert t.isot.startswith("2012-05-03T21:08:12")

interval = TimeRange("2020-01-01T00:00:00", 6*u.hour)
assert interval.start <= interval.center <= interval.end
assert interval.seconds.to_value(u.s) == 21600
assert "2020-01-01T03:00:00" in interval
parts = interval.split(3)
assert len(parts) == 3 and parts[0].start == interval.start
```

Use `format="jd"`, `format="mjd"`, `format="utime"`, or
`format="tai_seconds"` for numeric inputs. Use `TimeRange(start, end)` when
endpoints matter; use a quantity or `TimeDelta` for a duration. Remember that
`TimeRange` sorts reversed endpoints, while `TimeRange.window()` and
`.shift()` are convenient mutable interval utilities rather than immutable
records.

**Recovery:** if parsing fails, inspect the input type and specify `format=`;
if a numeric timestamp was interpreted incorrectly, reconstruct it with the
correct format and record the time scale. Do not compare strings or mix UTC and
TAI without an explicit conversion.

## 2. Construct and validate a coordinate

**Input:** angle, Cartesian, or observer metadata. **Output:** a unit-aware
`SkyCoord` with explicit frame metadata.

```python
import astropy.units as u
from astropy.coordinates import SkyCoord
from sunpy.coordinates import HeliographicStonyhurst, Helioprojective

t0 = "2020-01-01T00:00:00"
hgs = SkyCoord(10*u.deg, 20*u.deg, 695700*u.km,
               frame=HeliographicStonyhurst, obstime=t0)
hpc = SkyCoord(-120*u.arcsec, 80*u.arcsec,
               frame=Helioprojective, observer="earth", obstime=t0)
assert hgs.frame.obstime.isot.startswith("2020-01-01")
assert hpc.Tx.unit.is_equivalent(u.arcsec)
assert hpc.frame.observer is not None
```

Use `frame=Helioprojective(...)` when the destination frame is reused. Use
`observer=SkyCoord(...)` for a spacecraft/ground observer whose HGS location
is already known. Arrays should be vectorized in one `SkyCoord` rather than
constructed in a Python loop.

**Validation:** verify `coord.frame.name`, `coord.shape`, each component's unit,
`coord.frame.obstime`, `coord.frame.observer`, and `np.isfinite(coord.cartesian.xyz.value)`
when the coordinate is 3-D.

**Recovery:** a missing observer or time is not harmless metadata. Add both to
the source and destination frames. A 2-D HPC transform that yields NaNs is
usually off-limb ambiguity; use a known distance or a documented screen rather
than guessing a surface intersection.

## 3. Transform between solar frames

**Input:** a fully described source coordinate and a destination frame.
**Output:** a `SkyCoord` in the destination frame, preserving shape and units.

```python
import astropy.units as u
from astropy.coordinates import SkyCoord
from sunpy.coordinates import HeliographicCarrington, Helioprojective

obstime = "2020-01-01T00:00:00"
hpc = SkyCoord(0*u.arcsec, 0*u.arcsec,
               frame=Helioprojective(observer="earth", obstime=obstime))
hgc_frame = HeliographicCarrington(observer="earth", obstime=obstime)
hgc = hpc.transform_to(hgc_frame)
back = hgc.transform_to(hpc.frame)
assert hgc.frame.name == "heliographic_carrington"
assert back.frame.name == "helioprojective"
assert back.obstime == hpc.obstime
```

For Helioprojective, `Tx`/`Ty` are angular components and the optional
`distance` is required for an unambiguous 3-D conversion. For HGC, specify the
observer because apparent Carrington longitude includes the observer geometry.
For a change of observer, construct a second HPC frame with the new observer
and the intended time; do not mutate `.frame.observer` in place.

Astropy frames are valid destinations too, for example `.transform_to("icrs")`
when the coordinate is fully 3-D. A change in destination `obstime` updates the
axes and origin but does not make the physical object move. Treat that as a
coordinate-frame comparison unless a propagation workflow is selected.

**Recovery:** `ConvertError` or missing-frame-attribute errors mean the graph
cannot infer a unique 3-D position. Check `obstime`, `observer`, `distance`,
`rsun`, and whether a 2-D off-limb coordinate needs a screen. If a round trip
is not close, compare the same `rsun`, observer, and time and inspect whether
light-travel-time/apparent geometry was intentionally enabled.

## 4. Use ephemeris and solar utilities

**Input:** fixed body/time and optional observer. **Output:** deterministic
local geometry or solar orientation quantities.

```python
import astropy.units as u
from sunpy.coordinates import get_body_heliographic_stonyhurst, get_earth
from sunpy.coordinates.sun import B0, L0, P, earth_distance

when = "2020-01-01T00:00:00"
earth = get_earth(when)
venus = get_body_heliographic_stonyhurst("venus", when, observer=earth,
                                         quiet=True)
assert earth.frame.name == "heliographic_stonyhurst"
assert venus.obstime.isot.startswith("2020-01-01")
assert B0(when).unit.is_equivalent(u.deg)
assert L0(when).unit.is_equivalent(u.deg)
assert P(when).unit.is_equivalent(u.deg)
assert earth_distance(when).unit.is_equivalent(u.AU)
```

Set `include_velocity=True` only when velocity differentials are needed; test
`.velocity`/differential components after the call. `observer=` requests an
apparent body location with light-travel-time iteration and is distinct from a
true/instantaneous position. Use `quiet=True` to suppress only the informational
log message, not errors.

Use `carrington_rotation_number(time)` to label an observation and
`carrington_rotation_time(number)` to invert it. Keep `L0`'s
`light_travel_time_correction` and `aberration_correction` settings explicit
when comparing to another convention.

**Recovery:** built-in ephemerides are approximate for planets. If a result
must match a mission kernel or Horizons, stop and route to the optional backend
rather than mixing conventions. `get_horizons_coord()` is a network operation
and is not part of the offline smoke path.

## 5. Interact with WCS without building a map

**Input:** an existing Astropy `WCS` containing solar CTYPE/auxiliary metadata,
or a known SunPy frame. **Output:** a frame or WCS metadata object.

```python
import astropy.units as u
from astropy.wcs import WCS
from astropy.wcs.utils import wcs_to_celestial_frame
from sunpy.coordinates import Helioprojective, solar_frame_to_wcs_mapping

frame = Helioprojective(observer="earth", obstime="2020-01-01")
wcs = solar_frame_to_wcs_mapping(frame)
assert isinstance(wcs, WCS)
assert wcs.wcs.ctype == ["HPLN-TAN", "HPLT-TAN"]
assert wcs_to_celestial_frame(wcs).name == "helioprojective"
```

This helper concerns frame registration and WCS axes only; it does not provide
pixel scale, reference pixel, data shape, image units, or a plotted map. For an
existing `GenericMap`, prefer its `.coordinate_frame` and let the maps route
handle pixel/world conversion.

**Recovery:** if `wcs_to_celestial_frame()` cannot identify the frame, inspect
both CTYPE values and observer/date/solar-radius auxiliary metadata. Do not add
legacy ad-hoc WCS attributes; use public SunPy frame/WCS helpers and the map
route for header repair.

## 6. Propagate a solar-surface feature

Choose the least powerful mechanism that matches the claim:

### Context manager for a time-dependent transform

```python
import astropy.units as u
from astropy.coordinates import SkyCoord
from sunpy.coordinates import HeliographicStonyhurst, propagate_with_solar_surface

start = HeliographicStonyhurst(obstime="2020-01-01")
feature = SkyCoord(0*u.deg, 20*u.deg, 695700*u.km, frame=start)
target = HeliographicStonyhurst(obstime="2020-01-02")
with propagate_with_solar_surface(rotation_model="howard"):
    moved = feature.transform_to(target)
assert moved.frame.obstime == target.obstime
assert moved.lon.to_value(u.deg) != feature.lon.to_value(u.deg)
```

`propagate_with_solar_surface()` also follows the Sun's translational center
and changes only the documented SunPy frame transformations. Supported models
are `howard`, `snodgrass`, `allen`, and `rigid`.

### Explicit metaframe for reusable propagation metadata

```python
from sunpy.coordinates import RotatedSunFrame
rotated = RotatedSunFrame(base=start, rotated_time="2020-01-02",
                          rotation_model="howard")
rotated_feature = SkyCoord(0*u.deg, 20*u.deg, frame=rotated)
result = rotated_feature.transform_to(start)
```

`RotatedSunFrame` requires a base SunPy frame with `obstime`; use exactly one
of `duration` and `rotated_time`. It is useful when the rotation duration is
part of the coordinate object. `as_base()` changes the represented inertial
location and is not the same as a passive frame conversion.

### Coordinate helper for a new observer/time

`sunpy.physics.differential_rotation.solar_rotate_coordinate(coordinate,
observer=...)` or `time=...` applies a solar rotation model and returns the
feature as seen by the new observer. Pass one of `observer` or `time`, never
both. The `time=` form assumes an Earth observer and emits a warning; use a
fully defined observer for spacecraft work.

**Validation:** compare the result at the target time, confirm latitude is
unchanged by the idealized differential-rotation helper, record the model and
duration, and check that a rigid model gives equal longitude offsets across
latitudes while `howard` does not.

**Recovery:** do not use a plain `transform_to()` with a new `obstime` to claim
that a feature rotated. If the result is off-disk/NaN, resolve 2-D geometry
first. If the desired operation is map edge rotation or reprojection, route to
the maps/solar-physics skill rather than applying a coordinate-only helper to
image pixels.
