# CLI, Config, and Data Troubleshooting

## Console Command Not Found

Check that the command is installed in the same environment as `python`:

```bash
python - <<'PY'
import sys, astropy
print(sys.executable)
print(astropy.__version__)
PY
python -m pip show astropy
```

Reinstall Astropy in the active environment if command wrappers are missing.

## Optional Extra Missing

Install only what is needed: `astropy[recommended]` for common SciPy/Matplotlib
needs, specific packages for HDF5/Parquet/S3/Jupyter/dataframe workflows, and
`astropy[all]` only when broad integration coverage is desired.

## Unexpected Network Access

Disable auto-download before coordinate/time code that may consult IERS data:

```python
from astropy.utils import iers
iers.conf.auto_download = False
```

Avoid `SkyCoord.from_name` and remote URLs unless network access is explicit.

## Stale IERS Data Warning

Decide between reproducibility and precision. Bundled data may be sufficient for
many tasks; high-precision current Earth orientation requires an update and
cache management.

## Too Many Warnings Suppressed

Capture warnings by class and inspect messages. Suppressing all Astropy warnings
can hide FITS, WCS, unit, or remote-data problems.

## SAMP Hub Hangs or Leaves State

Use `samp_hub --help` first. Start a hub only for a bounded task, record host/
port/profile choices, and clean up the process. Do not start SAMP as a generic
smoke test.

## CLI Writes Unexpected Output

Use temporary directories and explicit output filenames. For `fitscheck`, avoid
modifying flags unless requested; for `fits2bitmap`, avoid reusing an existing
output path without approval.
