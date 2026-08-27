# Units and Constants API Reference

## Core Constructors

- `astropy.units.Quantity(value, unit=None, dtype=numpy.inexact, copy=True, order=None, subok=False, ndmin=0)` creates unit-aware scalars or arrays.
- `astropy.units.Unit(s='', represents=None, format=None, namespace=None, doc=None, parse_strict='raise')` parses or defines unit objects.
- Prefer `value * u.m` or `u.Quantity(value, u.m)` for construction; prefer `u.Unit("km / s")` for validated user-supplied unit strings.

## Quantity Operations

| Need | API |
| --- | --- |
| Convert units | `q.to(target_unit, equivalencies=None)` |
| Raw value in a unit | `q.to_value(target_unit)` |
| Unit decomposition | `q.decompose()`, `q.si`, `q.cgs` |
| Validate dimension | `q.unit.is_equivalent(unit)` or `q.unit.physical_type` |
| Attach unit to array | `array * u.Unit(...)` |
| Preserve subclass behavior | pass `subok=True` when subclass semantics matter |

## Equivalencies

Common equivalency factories live in `astropy.units`:

- `u.spectral()` for wavelength, frequency, energy, and wavenumber.
- `u.doppler_radio(rest)`, `u.doppler_optical(rest)`, `u.doppler_relativistic(rest)` for velocity/frequency conventions.
- `u.temperature()` and `u.temperature_energy()` for temperature conversions.
- `u.parallax()` for angle-to-distance parallax conversions.
- `u.dimensionless_angles()` when radians should be treated as dimensionless.
- Domain-specific brightness and beam equivalencies exist for radio/photometry workflows.

Pass equivalencies explicitly to `.to()` so the scientific assumption is visible.

## Custom Units and Formatting

- Define simple units with `u.def_unit("name", represents=...)`.
- Temporarily enable custom units with `with u.add_enabled_units([...]):`.
- Parse strings with `u.Unit(text, format="generic"|"fits"|"vounit"|"cds", parse_strict="raise"|"warn"|"silent")`.
- Format units with `unit.to_string(format="latex"|"fits"|"vounit"|"unicode")`.

## Constants

Use `astropy.constants` objects as quantities. They carry value, unit,
uncertainty, reference, and system-specific behavior.

Examples:

```python
from astropy import constants as const, units as u
energy = (const.h * const.c / (500 * u.nm)).to(u.eV)
```

Some electromagnetic constants are ambiguous between SI and CGS systems. If a
constant cannot be used directly in a CGS expression, select the appropriate
system-specific version (`.si`, `.cgs`, or versioned constants modules) and
explain the choice.
