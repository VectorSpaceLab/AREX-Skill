# Cross-Cutting Astropy Troubleshooting

## Import or Installation Fails

Symptoms:

- `ModuleNotFoundError: No module named 'astropy'`.
- Import succeeds in one shell but fails in another.
- Optional submodules fail with missing `scipy`, `matplotlib`, `h5py`, `pyarrow`, `pandas`, `dask`, or `fsspec`.

Actions:

1. Check the interpreter that will run the task:
   ```bash
   python - <<'PY'
   import sys, astropy
   print(sys.executable)
   print(astropy.__version__)
   PY
   ```
2. Install the base package for core workflows: `python -m pip install astropy`.
3. Install `astropy[recommended]` when the task uses SciPy fitters, Matplotlib plotting, or common dataframe bridges.
4. Install `astropy[all]` only when the task explicitly needs broad optional integrations such as HDF5, Parquet, S3/fsspec, Jupyter widgets, or additional astronomy packages.
5. If a compiled extension import fails, reinstall with a Python version and platform supported by the current Astropy release and avoid mixing packages from incompatible environments.

## Optional Dependency Errors

Common examples:

- HDF5 table I/O needs `h5py`.
- Parquet I/O needs `pyarrow`.
- HTTP/S3 file access through fsspec needs `fsspec[http,s3]` and often `s3fs`.
- Many fitters, FFT-related paths, and statistics routines use SciPy for best coverage.
- Plotting and image export workflows use Matplotlib and sometimes Pillow.

Prefer the smallest extra or dependency that matches the task. Do not install `all` just to solve a single missing backend unless a broad notebook environment is desired.

## Remote Data, IERS, and Offline Runs

Astropy can use bundled astronomy data and can also download updated files for IERS tables, ephemerides, name resolving, or remote URLs. For deterministic/offline tasks:

```python
from astropy.utils import iers
iers.conf.auto_download = False
```

If a coordinate/time workflow warns about stale IERS data, decide whether approximate bundled values are acceptable. If the user needs the newest Earth orientation parameters, explicitly allow network access and cache the downloaded data.

## Units and Raw NumPy Interoperability

Many NumPy functions preserve `Quantity`, but external libraries may not. When passing data outside Astropy:

- Use `.to(target_unit)` to convert with units attached.
- Use `.to_value(target_unit)` only when the target library needs raw numbers.
- Record the unit next to any raw array so it can be restored.

If conversion fails with `UnitConversionError`, check whether an equivalency is required, such as spectral wavelength/frequency/energy, temperature, Doppler velocity, or dimensionless angles.

## FITS/WCS/CLI Safety

- Use temporary copies for CLI experiments.
- `fitscheck` can update checksums or rewrite verification state depending on flags; run help first and avoid mutating flags unless requested.
- FITS warnings may indicate non-standard but recoverable files. Inspect the warning class and the affected header cards before suppressing.
- WCS coordinate conversions must state origin convention: NumPy/Python coordinates are normally origin `0`; FITS/DS9 style often uses origin `1`.

## Validation Shortcuts

Use bundled scripts for quick environment checks:

```bash
python path/to/astropy/scripts/astropy_smoke.py
python path/to/astropy/scripts/astropy_cli_smoke.py --with-fixtures
```

When adapting the scripts, keep checks small and temporary-file based; they are smoke tests, not replacements for the full Astropy test suite.
