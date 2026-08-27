---
name: units-constants
description: "Use Astropy units, quantities, equivalencies, custom units,
  physical types, and physical constants safely in astronomy calculations."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Units and Constants Router

Use this sub-skill when a task centers on Astropy physical units, unit-aware
arrays, conversions, equivalencies, constants, or unit validation.

## Load This When

- The user asks for `Quantity`, `Unit`, `u.Quantity`, `.to()`, `.to_value()`,
  `.decompose()`, `.si`, `.cgs`, or unit arithmetic.
- A value must carry units through NumPy operations or an astronomy formula.
- A conversion needs an equivalency: spectral wavelength/frequency/energy,
  Doppler velocity, temperature, parallax, brightness temperature, or
  dimensionless angles.
- The task defines custom units, parses unit strings, validates physical types,
  or needs VOUnit/FITS/CDS formatting.
- Constants such as `c`, `G`, `h`, `M_sun`, or versioned CODATA/IAU constants
  are involved.

## Route Away When

- Coordinate frames, `SkyCoord`, `Time`, or observation locations dominate; use
  `../time-coordinates/SKILL.md`.
- Unit-bearing table serialization is the main issue; use
  `../tables-io/SKILL.md`.
- Cosmological units or built-in cosmology realizations dominate; use
  `../cosmology/SKILL.md`.
- The problem is installation or optional dependency setup; use
  `../cli-config-data/SKILL.md` or the root troubleshooting reference.

## First Actions

1. Identify whether each input is a scalar, NumPy array, `Quantity`, `Unit`,
   string unit, or constant.
2. Convert to a `Quantity` early: `value * u.unit` or `u.Quantity(value, unit)`.
3. Keep quantities unit-aware until an external package requires raw values.
4. Use `.to(target_unit, equivalencies=...)` for conversion and `.to_value(...)`
   only at boundaries.
5. If `.to()` fails, decide whether an equivalency is scientifically justified.
6. For constants, inspect the attached unit and whether SI/CGS ambiguity exists
   before using a raw `.value`.
7. Validate output with a dimensional check: `quantity.unit.is_equivalent(...)`
   or `quantity.physical_type`.

## References

- [references/api-reference.md](references/api-reference.md) lists the verified
  constructors and key APIs for units, quantities, equivalencies, and constants.
- [references/workflows.md](references/workflows.md) gives self-contained
  recipes for unit-aware calculations, equivalencies, custom units, NumPy
  interop, and constants.
- [references/troubleshooting.md](references/troubleshooting.md) covers
  conversion errors, cgs electromagnetic ambiguity, lost units, parser strictness,
  and formatting pitfalls.

## Safety and Validation

- Never silently strip units for convenience. If a raw number is required,
  state the target unit used for `.to_value()`.
- Do not apply an equivalency unless the science context warrants it; record
  which equivalency was used.
- Avoid comparing raw `.value` across quantities with different but compatible
  units.
- Use constants as quantities (`const.c`, `const.G`) rather than copying numeric
  values into code.
- For publication or reproducibility, mention the constants version if a result
  depends sensitively on CODATA/IAU revisions.

## Native-Backed Validation Ideas

- Convert `42 * u.km / u.s` to `u.m / u.s` and assert `42000`.
- Convert wavelength to frequency with `u.spectral()` and assert the output unit
  is equivalent to Hz.
- Use a constant in an expression and assert the resulting unit is physically
  expected.
