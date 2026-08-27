# Units and Constants Workflows

## Unit-Aware Calculation

```python
from astropy import units as u

velocity = 42 * u.km / u.s
time = 120 * u.s
distance = (velocity * time).to(u.km)
assert distance.unit == u.km
```

Keep quantities through the calculation. Convert to raw arrays only at the
external boundary:

```python
km_values = distance.to_value(u.km)
```

## Spectral Conversion

```python
from astropy import units as u

wavelength = 656.28 * u.nm
frequency = wavelength.to(u.Hz, equivalencies=u.spectral())
energy = wavelength.to(u.eV, equivalencies=u.spectral())
```

State the equivalency because wavelength and frequency are not dimensionally
identical without the physical relationship.

## Doppler Velocity Convention

```python
from astropy import units as u

rest = 115.27120 * u.GHz
observed = 115.0 * u.GHz
v_radio = observed.to(u.km / u.s, equivalencies=u.doppler_radio(rest))
```

Radio, optical, and relativistic conventions differ; choose the one the user or
instrument documentation expects.

## Custom Unit Scope

```python
from astropy import units as u

adu = u.def_unit("adu")
with u.add_enabled_units([adu]):
    counts = u.Quantity([1, 2, 3], "adu")
```

Use a context manager so custom parsing does not leak into unrelated code.

## Constants in Formulae

```python
from astropy import constants as const, units as u

mass = 1 * const.M_sun
radius = 1 * const.R_sun
escape_velocity = (2 * const.G * mass / radius) ** 0.5
print(escape_velocity.to(u.km / u.s))
```

When a task compares values across Astropy versions or papers, record whether
SI, CGS, IAU, or a versioned constants module was used.

## Validation Checklist

- Inputs converted to `Quantity` objects.
- Target units are explicit.
- Equivalencies are named and justified.
- Constants remain unit-aware.
- Final raw values, if any, have the unit recorded next to them.
