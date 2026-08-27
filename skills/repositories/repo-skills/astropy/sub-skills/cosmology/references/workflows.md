# Cosmology Workflows

## Built-In Realization Calculations

```python
from astropy import units as u
from astropy.cosmology import Planck18

age0 = Planck18.age(0)
dc = Planck18.comoving_distance(1.0)
assert age0.unit.is_equivalent(u.Gyr)
assert dc.unit.is_equivalent(u.Mpc)
```

State `Planck18` (or another realization) in the result.

## Custom Flat Lambda-CDM Cosmology

```python
from astropy import units as u
from astropy.cosmology import FlatLambdaCDM

cosmo = FlatLambdaCDM(H0=70 * u.km / (u.Mpc * u.s), Om0=0.3, Tcmb0=2.725 * u.K,
                      name="example")
print(cosmo.luminosity_distance([0.5, 1.0]))
```

Use units for dimensional parameters and include `name`/`meta` when results
must be traceable.

## Clone a Realization

```python
updated = Planck18.clone(name="Planck18-lowH0", H0=65 * u.km / (u.Mpc * u.s))
```

Use `clone` for small changes so inherited parameters remain explicit.

## Redshift Inversion

```python
from astropy import units as u
from astropy.cosmology import Planck18, z_at_value

z = z_at_value(Planck18.age, 5 * u.Gyr, zmin=0.01, zmax=10)
```

Choose bounds that bracket the expected solution and record the target function.
For non-monotonic functions, multiple redshifts may satisfy the same value.

## Serialization Round-Trip

```python
mapping = Planck18.to_format("mapping")
restored = Planck18.from_format(mapping, format="mapping")
assert restored.is_equivalent(Planck18)
```

For table/YAML/ECSV formats, verify optional dependencies and metadata after
round-trip.
