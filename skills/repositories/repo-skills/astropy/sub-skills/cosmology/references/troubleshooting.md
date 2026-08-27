# Cosmology Troubleshooting

## Output Is a Quantity, Not a Number

Cosmology methods return unit-aware quantities. Convert deliberately:

```python
Planck18.comoving_distance(1).to_value(u.Mpc)
```

Keep units attached for intermediate calculations.

## Wrong or Hidden Default Cosmology

Do not rely on implicit defaults for reproducible tasks. Pass or state the
cosmology explicitly. If using `default_cosmology`, document the active value.

## `z_at_value` Fails or Finds the Wrong Solution

- Check that `fval` has units compatible with the target function.
- Set `zmin` and `zmax` to bracket the expected solution.
- Some functions are not one-to-one over wide redshift ranges; split ranges or
  choose a bracket.
- Increase `maxfun` only after confirming the bounds and function behavior.

## Metadata Lost in Serialization

Use registered formats that preserve metadata, and verify with `is_equivalent`
and explicit metadata checks. Table/YAML/ECSV routes can involve optional
dependencies or format-specific limitations.

## Parameter Units Are Invalid

Dimensional parameters such as `H0`, `Tcmb0`, and neutrino masses need units.
Density parameters such as `Om0` are dimensionless. Validate class constructor
errors rather than stripping units.
