# Time and Coordinates API Reference

## Time APIs

- `Time(val, val2=None, format=None, scale=None, precision=None, in_subfmt=None, out_subfmt=None, location=None, copy=False)` creates scalar or array times.
- `TimeDelta(val, val2=None, format=None, scale=None, precision=None, in_subfmt=None, out_subfmt=None, location=None, copy=False)` represents elapsed durations.
- Common properties: `.iso`, `.isot`, `.jd`, `.mjd`, `.datetime`, `.unix`, `.scale`, `.format`, `.location`.
- Common operations: `t.to_value(format)`, `t.light_travel_time(...)`, `t.sidereal_time(...)`, arithmetic with `TimeDelta` or quantities.

## Coordinate APIs

- `SkyCoord(*args, copy=True, **kwargs)` accepts components, strings, quantities,
  frame names/objects, and many array shapes.
- `EarthLocation(*args, **kwargs)` represents observatory location; create from
  geocentric coordinates, geodetic longitude/latitude/height, or registered site
  names when available.
- Matching helpers include `match_coordinates_sky(matchcoord, catalogcoord, nthneighbor=1, storekdtree='kdtree_sky')`, `SkyCoord.match_to_catalog_sky`, and `SkyCoord.search_around_sky`.
- Solar-system helpers include `get_sun`, `get_body`, `get_body_barycentric`,
  and the `solar_system_ephemeris` context manager.

## Frame and Transform Notes

- Common frames: `icrs`, `fk5`, `galactic`, `galactocentric`, `altaz`, `gcrs`,
  `itrs`, `barycentrictrueecliptic`.
- Frame attributes matter: `AltAz` needs `obstime` and `location`; FK frames may
  need equinox; Galactocentric has configurable solar parameters.
- Use `coord.transform_to('galactic')` or `coord.transform_to(frame_object)`.
- Separation APIs: `coord1.separation(coord2)`, `coord1.separation_3d(coord2)`,
  and position-angle helpers.

## Array Semantics

`Time` and `SkyCoord` objects can be scalar or array-like. Use `.isscalar`,
`.shape`, slicing, and vectorized operations instead of looping when possible.
Keep returned catalog matching indices aligned with the original catalog.
