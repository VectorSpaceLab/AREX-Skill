# Time and Coordinates Workflows

## Time Creation and Conversion

```python
from astropy.time import Time

t = Time("2000-01-01T00:00:00", format="isot", scale="utc")
print(t.jd)
print(t.tai.isot)
```

For arrays:

```python
times = Time(["2024-01-01", "2024-01-02"], scale="utc")
```

## Coordinate Transform

```python
from astropy import units as u
from astropy.coordinates import SkyCoord

coord = SkyCoord(ra=10*u.deg, dec=20*u.deg, frame="icrs")
gal = coord.transform_to("galactic")
print(gal.l, gal.b)
```

Check that units are angular and output values are finite.

## Catalog Matching

```python
from astropy import units as u
from astropy.coordinates import SkyCoord

sources = SkyCoord([10.0, 11.0]*u.deg, [20.0, 21.0]*u.deg, frame="icrs")
catalog = SkyCoord([10.1, 30.0]*u.deg, [20.1, -5.0]*u.deg, frame="icrs")
idx, sep2d, dist3d = sources.match_to_catalog_sky(catalog)
```

Keep `idx`, `sep2d`, and `dist3d` together. Use a maximum separation threshold
before accepting a match.

## Offline-Safe AltAz Transform

```python
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time
from astropy.utils import iers

iers.conf.auto_download = False
location = EarthLocation(lat=19.8206*u.deg, lon=-155.4681*u.deg, height=4205*u.m)
time = Time("2024-01-01T10:00:00", scale="utc", location=location)
target = SkyCoord(ra=10*u.deg, dec=20*u.deg, frame="icrs")
altaz = target.transform_to(AltAz(obstime=time, location=location))
```

If high-precision Earth orientation is required, allow an explicit IERS update
instead of silently falling back to bundled data.

## Proper Motion Propagation

```python
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time

star = SkyCoord(ra=10*u.deg, dec=20*u.deg, distance=100*u.pc,
                pm_ra_cosdec=5*u.mas/u.yr, pm_dec=-3*u.mas/u.yr,
                radial_velocity=20*u.km/u.s, obstime=Time("J2000"))
future = star.apply_space_motion(Time("J2025"))
```

Always specify `obstime` for proper-motion coordinates.
