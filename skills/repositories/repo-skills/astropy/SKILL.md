---
name: astropy
description: "Use Astropy core for astronomy units, coordinates, times, tables,
  FITS/WCS files, modeling, statistics, visualization, cosmology, configuration,
  and public CLIs."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Astropy Repo Skill

Use this skill when a task needs the Astropy core Python package for astronomy
or astrophysics analysis. Astropy is a CPU scientific-Python library; selected
workflows do not require GPU or accelerator backends. Use an installed Astropy
package and the bundled references/scripts here rather than reopening the
source repository.

## Fast Start

```python
import astropy
from astropy import units as u
print(astropy.__version__)
print((42 * u.km / u.s).to(u.m / u.s))
```

If plotting, fitting, convolution FFT paths, or common dataframe bridges are
needed, prefer installing the common optional set:

```bash
python -m pip install "astropy[recommended]"
```

Use `astropy[all]` only for broad optional integrations such as HDF5, Parquet,
S3/fsspec, Jupyter, or additional astronomy packages.

## Route by Task

- For units, quantities, equivalencies, custom units, and physical constants,
  read [sub-skills/units-constants/SKILL.md](sub-skills/units-constants/SKILL.md).
- For `Time`, timescales, `SkyCoord`, coordinate frames, transformations,
  separations, matching, and observation geometry, read
  [sub-skills/time-coordinates/SKILL.md](sub-skills/time-coordinates/SKILL.md).
- For `Table`/`QTable`, unified I/O, FITS, ASCII/ECSV, VOTable, HDF5/Parquet
  notes, pandas/dataframe bridges, and table/FITS CLIs, read
  [sub-skills/tables-io/SKILL.md](sub-skills/tables-io/SKILL.md).
- For FITS WCS, pixel/world conversion, WCS validation, `NDData`, `CCDData`,
  masks, uncertainties, and image metadata containers, read
  [sub-skills/wcs-nddata/SKILL.md](sub-skills/wcs-nddata/SKILL.md).
- For image normalization, intervals, stretches, WCSAxes, RGB output,
  `fits2bitmap`, kernels, direct convolution, and FFT convolution, read
  [sub-skills/visualization-convolution/SKILL.md](sub-skills/visualization-convolution/SKILL.md).
- For models, fitters, compound models, constraints, robust statistics,
  histograms, time series, periodograms, and uncertainty distributions, read
  [sub-skills/modeling-stats-timeseries/SKILL.md](sub-skills/modeling-stats-timeseries/SKILL.md).
- For cosmology realizations/classes, distances, ages, redshift inversion,
  cosmology units, and serialization, read
  [sub-skills/cosmology/SKILL.md](sub-skills/cosmology/SKILL.md).
- For install/import checks, optional extras, config/cache, remote data/IERS,
  logging/warnings, SAMP, and the general CLI catalog, read
  [sub-skills/cli-config-data/SKILL.md](sub-skills/cli-config-data/SKILL.md).

## Shared References and Scripts

- Read [references/package-overview.md](references/package-overview.md) for the
  module map, install extras, and general workflow pattern.
- Read [references/troubleshooting.md](references/troubleshooting.md) for
  cross-cutting install/import, optional dependency, remote-data, units, and
  FITS/WCS safety guidance.
- Read [references/repo-provenance.md](references/repo-provenance.md) to check
  the source commit and evidence baseline before refreshing this skill.
- Router import metadata lives in
  [references/repo-routing-metadata.json](references/repo-routing-metadata.json).
- Run [scripts/astropy_smoke.py](scripts/astropy_smoke.py) to verify a small
  installed-package API surface across the main sub-skill routes.
- Run [scripts/astropy_cli_smoke.py](scripts/astropy_cli_smoke.py) to verify
  public Astropy console commands with safe help and optional temporary
  fixtures.

## Operating Rules

1. Keep units attached until a non-Astropy API requires raw arrays; then use
   `.to_value(unit)` and record the unit.
2. Be explicit about `format=`, `scale=`, `frame=`, `unit=`, `origin=`, and
   `format` names for I/O to avoid silent guessing.
3. Use temporary files for smoke checks and never mutate user FITS/table files
   unless the user explicitly requested that exact operation.
4. For offline or reproducible tasks, disable or control remote downloads before
   coordinate/time/IERS/name-resolution operations.
5. Validate scientific transformations numerically: unit round-trips,
   pixel/world round-trips, table read/write round-trips, fit residuals, or
   cosmology unit checks.
6. Route optional dependency errors to the nearest sub-skill first, then to the
   root troubleshooting reference for install-level decisions.

## Do Not Use This Skill For

- General NumPy/Pandas data processing without Astropy APIs, astronomy formats,
  units, times, or coordinates.
- Maintaining the Astropy repository, release engineering, CI, or documentation
  build workflows.
- Running broad Astropy test suites or benchmarks as a substitute for a focused
  user workflow.
- SAMP services, remote data downloads, or file-mutating CLI operations without
  explicit user approval and bounded temporary-file safeguards.
