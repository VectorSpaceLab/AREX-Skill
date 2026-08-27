# Astropy Package Overview

Astropy is the core Python package for astronomy and astrophysics workflows. It combines NumPy-style arrays with domain-aware objects for units, times, coordinates, tables, FITS/WCS files, modeling, statistics, visualization, cosmology, and operational utilities.

## Installation and Import Surface

Typical user installation:

```bash
python -m pip install astropy
python - <<'PY'
import astropy
print(astropy.__version__)
PY
```

Useful extras:

- `astropy[recommended]` installs common optional runtime dependencies used by many workflows, including SciPy, Matplotlib, and Narwhals.
- `astropy[all]` installs broad optional integrations such as HDF5, Parquet, S3/fsspec, pandas/dataframe bridges, IPython/Jupyter, and additional astronomy utilities. Use it only when the task needs those integrations.
- Development, docs, typing, and test dependency groups are not required for ordinary runtime use.

Representative public modules:

| Module | Primary purpose | Route |
| --- | --- | --- |
| `astropy.units`, `astropy.constants` | Quantities, units, equivalencies, physical constants | `sub-skills/units-constants/` |
| `astropy.time`, `astropy.coordinates` | Time scales/formats and coordinate frames/transforms | `sub-skills/time-coordinates/` |
| `astropy.table`, `astropy.io` | Tables and file formats including FITS, ASCII/ECSV, VOTable | `sub-skills/tables-io/` |
| `astropy.wcs`, `astropy.nddata` | FITS WCS and image-like data containers | `sub-skills/wcs-nddata/` |
| `astropy.visualization`, `astropy.convolution` | Image normalization, plotting aids, kernels/convolution | `sub-skills/visualization-convolution/` |
| `astropy.modeling`, `astropy.stats`, `astropy.timeseries`, `astropy.uncertainty` | Models/fitting, robust statistics, periodograms and time series | `sub-skills/modeling-stats-timeseries/` |
| `astropy.cosmology` | Cosmology realizations, FLRW classes, distances/ages, redshift inversion | `sub-skills/cosmology/` |
| `astropy.config`, `astropy.utils`, `astropy.samp` | Configuration/cache, remote data, logging, SAMP, package CLIs | `sub-skills/cli-config-data/` |

## Public Console Commands

Astropy exposes command-line tools through console entry points:

- FITS: `fitsinfo`, `fitsheader`, `fitscheck`, `fitsdiff`.
- Visualization: `fits2bitmap`.
- Tables: `showtable-astropy` (`showtable` may exist as a deprecated alias).
- VOTable/WCS: `volint`, `wcslint`.
- SAMP: `samp_hub`.

Use `scripts/astropy_cli_smoke.py` to check that these commands are available and their help parsers work. Use command-specific references in `sub-skills/tables-io/`, `sub-skills/wcs-nddata/`, `sub-skills/visualization-convolution/`, and `sub-skills/cli-config-data/` for safety notes.

## General Workflow Pattern

1. Choose the domain object first (`Quantity`, `SkyCoord`, `Time`, `Table`, `WCS`, `NDData`, `Model`, `Cosmology`, etc.).
2. Keep units attached as long as possible; convert to raw numbers only at external library boundaries.
3. Prefer explicit formats and scales (`format=`, `scale=`, `unit=`, `frame=`, `origin=`) over implicit guessing.
4. Use temporary files for smoke checks and never overwrite user data without explicit confirmation.
5. Disable or control remote data access when the task must run offline or be reproducible.
6. Validate domain transformations numerically: unit conversion round-trips, pixel/world round-trips, table read/write round-trips, fit residuals, or cosmology unit checks.
