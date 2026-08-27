---
name: cosmology
description: "Use Astropy cosmology realizations, FLRW classes, distances, ages,
  redshift inversion, cosmology units, equivalencies, and serialization."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Cosmology Router

Use this sub-skill when a task centers on `astropy.cosmology` models,
realizations, cosmological calculations, redshift inversion, or cosmology I/O.

## Load This When

- The task mentions `Planck18`, `default_cosmology`, `FlatLambdaCDM`,
  `LambdaCDM`, `w0waCDM`, cosmology parameters, or cloning a cosmology.
- The user needs age, lookback time, comoving/luminosity/angular-diameter
  distance, distance modulus, Hubble parameter, density parameters, critical
  density, or absorption distance.
- The task uses `z_at_value`, vectorized redshifts, cosmology units, little-h
  equivalencies, or cosmology serialization.
- A workflow must preserve cosmology metadata in mappings, tables, YAML, ECSV,
  or another registered format.

## Route Away When

- General units/equivalencies are the main question; use
  `../units-constants/SKILL.md`.
- Table format mechanics are central; use `../tables-io/SKILL.md`.
- Model fitting or time-series analysis is central; use
  `../modeling-stats-timeseries/SKILL.md`.

## First Actions

1. Identify whether the user wants a built-in realization, current default, or
   custom class.
2. Keep redshift inputs scalar/vectorized and unitless unless an API expects a
   `Quantity`.
3. Preserve output quantities with units; do not strip `.value` until necessary.
4. For custom cosmologies, state all required parameters and units.
5. For inverse calculations, bound `z_at_value` and validate the solution.
6. For serialization, choose the target format and verify round-trip metadata.

## References

- [references/api-reference.md](references/api-reference.md) lists classes,
  functions, realizations, and I/O APIs.
- [references/workflows.md](references/workflows.md) covers common calculations,
  custom cosmologies, redshift inversion, and serialization.
- [references/troubleshooting.md](references/troubleshooting.md) covers unit
  issues, solver bounds, default cosmology surprises, optional dependencies, and
  metadata round-trips.

## Safety and Validation

- Always state which cosmology was used.
- Validate units on every output.
- Use bounded redshift grids/solvers for automated tasks.
- Do not assume built-in realization names are unchanged across major versions;
  check availability in the installed package.

## Native-Backed Validation Ideas

- Evaluate `Planck18.age(0)` and assert it is a positive Gyr quantity.
- Compute `Planck18.comoving_distance(1)` and assert Mpc-equivalent units.
- Clone a realization with a new name and verify parameters/metadata.
