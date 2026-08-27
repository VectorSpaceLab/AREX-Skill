# Operations Reference

## Install and Verify

```bash
python -m pip install astropy
python - <<'PY'
import astropy
print(astropy.__version__)
PY
```

Use `astropy[recommended]` for common SciPy/Matplotlib/Narwhals runtime needs.
Use `astropy[all]` only when broad optional integrations are required.

## Configuration and Cache

```python
from astropy.config import paths

print(paths.get_config_dir())
print(paths.get_cache_dir())
```

For isolated checks, use temporary config/cache contexts when available:

```python
from astropy.config.paths import set_temp_config, set_temp_cache

with set_temp_config(), set_temp_cache():
    ...
```

## Remote Data and IERS

For offline/reproducible coordinate/time workflows:

```python
from astropy.utils import iers
iers.conf.auto_download = False
```

If the user needs up-to-date Earth orientation parameters, explicitly allow
network access and record cache behavior. Name resolution and remote URLs also
need explicit network expectations.

## Logging and Warnings

Astropy exposes a package logger and uses structured warnings. Prefer targeted
handling:

```python
import warnings
from astropy.utils.exceptions import AstropyWarning

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always", AstropyWarning)
    ...
```

Inspect warning messages before suppressing them.

## SAMP

SAMP supports astronomy application messaging through hub/client workflows.
Use `samp_hub --help` for command options. Starting a hub creates a local
service/socket and should be explicit, bounded, and cleaned up.
