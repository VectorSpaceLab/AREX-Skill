---
name: time-coordinates
description: "Use Astropy Time and coordinates for timescales, formats, frames,
  transformations, separations, matching, observatory geometry, and solar-system
  helpers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Time and Coordinates Router

Use this sub-skill when a task asks for time scales/formats or astronomy
coordinate objects and transformations.

## Load This When

- The task mentions `Time`, `TimeDelta`, UTC/TAI/TT/TDB, Julian dates, ISO
  formats, precision, leap seconds, or observatory location on a time object.
- The task uses `SkyCoord`, `Angle`, `Longitude`, `Latitude`, `EarthLocation`,
  ICRS/FK5/Galactic/AltAz/Galactocentric, or `transform_to`.
- The user needs angular separation, catalog matching, proper motion, radial
  velocity, or space-motion propagation.
- Observation planning requires AltAz transforms, local sidereal time, Sun/Moon
  positions, or no-network handling for IERS data.

## Route Away When

- Pixel/world transformations from FITS WCS are central; use
  `../wcs-nddata/SKILL.md`.
- Unit conversion itself is the obstacle; use `../units-constants/SKILL.md`.
- Remote-data cache/config policy is the main question; use
  `../cli-config-data/SKILL.md`.
- Table serialization of coordinates is central; use `../tables-io/SKILL.md`.

## First Actions

1. Identify input types: strings, numbers, arrays, `Quantity`, `Time`,
   `SkyCoord`, frame object, or table columns.
2. Make time scale and format explicit: `Time(value, format=..., scale=...)`.
3. Attach location when needed for local or Earth-rotation dependent results.
4. Construct `SkyCoord` with units and a frame; do not assume degrees for raw
   numbers unless the user says so.
5. For transforms, use `coord.transform_to(target_frame_or_name)` and validate
   representative outputs.
6. For matching, keep returned index, separation, and 3D distance together.
7. For offline/reproducible tasks, set IERS/network policy before transforms
   that need Earth orientation data.

## References

- [references/api-reference.md](references/api-reference.md) lists constructors,
  methods, frame and matching APIs.
- [references/workflows.md](references/workflows.md) covers time conversion,
  coordinate transforms, matching, AltAz observation planning, proper motion,
  and offline-safe settings.
- [references/troubleshooting.md](references/troubleshooting.md) covers units,
  frame attributes, IERS warnings, name-resolution/network traps, and array
  shape issues.

## Safety and Validation

- Always state angle units and time scale.
- Avoid name resolution in unattended tasks unless network access is explicit;
  prefer literal coordinates.
- Validate transforms with sanity checks: finite angles, expected frames,
  round-trip where appropriate, and separations in angular units.
- Do not treat WCS pixel coordinates as `SkyCoord` without a verified WCS
  transformation.

## Native-Backed Validation Ideas

- Convert a UTC `Time` to JD and assert the known result for J2000-like inputs.
- Build an ICRS `SkyCoord`, transform to Galactic, and assert finite longitude
  and latitude.
- Match a two-object catalog and assert the returned index and separation units.
