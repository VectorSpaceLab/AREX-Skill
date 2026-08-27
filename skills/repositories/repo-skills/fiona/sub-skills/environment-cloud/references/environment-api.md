# Environment API

## `fiona.Env`

`Env` is a context manager around GDAL's stateful configuration and driver
registry. The verified constructor accepts `session=None`, `aws_unsigned=False`,
`profile_name=None`, `session_class=...`, and arbitrary GDAL configuration
options such as `CPL_DEBUG` or `CHECK_WITH_INVERT_PROJ`.

```python
import fiona

with fiona.Env(CPL_DEBUG=False, CHECK_WITH_INVERT_PROJ=True):
    with fiona.open("input.geojson") as src:
        print(src.driver)
```

Scope configuration with a `with` block. On exit Fiona restores prior options
and tears down its managed environment. Avoid setting AWS credentials as raw
GDAL options; Fiona handles credentials through session objects.

## Drivers and data paths

`fiona.supported_drivers` maps driver names to supported modes. Query it before
selecting a format or mode. `fio env --formats` is the CLI equivalent. Driver
availability depends on the GDAL runtime used by the installed Fiona build.

GDAL and PROJ data lookup may use `GDAL_DATA`, `PROJ_DATA`, or `PROJ_LIB`, or
package-provided data finders. A valid library with missing data can fail only
when opening a CRS or a specific format, so include a CRS and driver probe in
a smoke check.

## Runtime diagnostic

The bundled `scripts/check_runtime.py` intentionally prints only:

- Fiona and GDAL release versions;
- number and names of supported drivers;
- whether importable optional modules such as boto3, Shapely, and fsspec exist.

It does not print installation paths, credentials, environment variable values,
or machine-specific prefixes.
