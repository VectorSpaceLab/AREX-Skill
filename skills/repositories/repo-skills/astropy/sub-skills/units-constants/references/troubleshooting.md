# Units and Constants Troubleshooting

## `UnitConversionError`

Likely causes:

- Units are not dimensionally equivalent.
- A required equivalency was omitted.
- The input value lost its unit before conversion.

Recovery:

```python
q.unit, q.unit.physical_type
q.to(target, equivalencies=u.spectral())  # only when scientifically valid
```

Do not silence the error by using `.value`; that hides a physical mismatch.

## Constants Are Ambiguous in CGS

Some electromagnetic constants have different SI/CGS meanings. If arithmetic
raises an ambiguity error, choose the appropriate system:

```python
from astropy import constants as const
const.e.si
const.e.esu
```

Record the system because it affects reproducibility.

## Units Disappear in NumPy or External Libraries

Many NumPy functions support `Quantity`, but not all external packages do. Use
`.to_value(unit)` at the boundary and immediately record or reattach the unit.
If a function returns raw arrays, wrap them back with `result * unit` only when
the output unit is known.

## Unit String Parsing Fails

Use an explicit format when parsing data-file units:

```python
u.Unit(text, format="fits", parse_strict="warn")
```

Use `parse_strict="raise"` for validation and `warn` only when ingesting legacy
files where downstream inspection is planned.

## Dimensionless Angles Surprise

Radians are units in Astropy. For some math expressions a radian should be
considered dimensionless:

```python
angle.to(u.dimensionless_unscaled, equivalencies=u.dimensionless_angles())
```

Use this deliberately; it can hide mistakes if applied globally.
