# Cosmology API Reference

## Realizations and Defaults

- Common built-in realizations include `Planck18` and other named cosmologies available in the installed version.
- `default_cosmology` controls the default used by APIs that consult a global default.
- Always state the realization or custom parameters used in results.

## Classes and Functions

- `FlatLambdaCDM(H0, Om0, Tcmb0=0 K, Neff=3.04, m_nu=0 eV, Ob0=0.0, *, name=None, meta=None)` creates a flat Lambda-CDM cosmology.
- Related classes include `LambdaCDM`, `wCDM`, `w0waCDM`, `w0wzCDM`, and other FLRW variants.
- `z_at_value(func, fval, zmin=1e-08, zmax=1000, ztol=1e-08, maxfun=500, method='Brent', bracket=None, *, verbose=False)` inverts monotonic-like cosmological functions.

## Common Methods

| Calculation | Example |
| --- | --- |
| Age at redshift | `cosmo.age(z)` |
| Lookback time | `cosmo.lookback_time(z)` |
| Comoving distance | `cosmo.comoving_distance(z)` |
| Luminosity distance | `cosmo.luminosity_distance(z)` |
| Angular diameter distance | `cosmo.angular_diameter_distance(z)` |
| Distance modulus | `cosmo.distmod(z)` |
| Hubble parameter | `cosmo.H(z)` |
| Critical density | `cosmo.critical_density(z)` |
| Clone/update | `cosmo.clone(name="...", Om0=...)` |
| Equivalence | `cosmo.is_equivalent(other)` |

## Serialization

Cosmology objects support registered formats such as mappings, tables, YAML,
and ECSV depending on installed optional dependencies. Use `to_format` and
`from_format` where available, and verify units/metadata after round-trip.
