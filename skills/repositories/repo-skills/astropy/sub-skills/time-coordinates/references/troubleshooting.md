# Time and Coordinates Troubleshooting

## Transform Requires Missing Frame Attributes

Symptoms include errors about `obstime`, `location`, `equinox`, or frame
attributes. Create the target frame with the required attributes, for example
`AltAz(obstime=time, location=site)`.

## IERS or Earth Orientation Warnings

If a transform needs Earth orientation parameters, Astropy may warn about stale
or unavailable IERS data.

- For offline/reproducible tasks: `iers.conf.auto_download = False` and accept
  the documented precision limit.
- For highest precision: explicitly permit a network update and cache the data.

Do not let an unattended task unexpectedly hit the network.

## Name Resolution Fails

`SkyCoord.from_name` and solar-system/name helpers may require external
services. Prefer literal coordinates when reproducibility matters. If name
resolution is required, handle network failures and cache resolved coordinates
in the workflow output.

## Units or Shape Errors

Raw numbers in `SkyCoord` constructors may be ambiguous. Attach units:

```python
SkyCoord(ra=[10, 11] * u.deg, dec=[20, 21] * u.deg, frame="icrs")
```

For vectorized operations, inspect `.shape` and align array lengths before
matching or transforming.

## Catalog Matches Look Wrong

- Verify both catalogs are in comparable frames.
- Apply a maximum angular separation threshold.
- Preserve returned `idx` alignment with the query coordinates.
- Use `nthneighbor=2` when matching a catalog to itself and skipping the source
  itself.

## Time Scale Confusion

UTC, TAI, TT, TDB, and UT1 are different. Make the scale explicit in
construction and output. Avoid interpreting a string timestamp without knowing
whether it represents UTC or another timescale.
