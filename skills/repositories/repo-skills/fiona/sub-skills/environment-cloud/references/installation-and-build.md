# Installation and build

## Preferred install paths

For ordinary users, install the public wheel with:

```console
python -m pip install fiona
```

Wheels bundle a GDAL runtime for simple applications but may omit optional
format drivers and are not guaranteed to be compatible with every other binary
GIS package. Conda-forge is often preferable when Fiona must share GDAL, PROJ,
QGIS, or many format drivers.

## Source builds

A source build needs a compatible GDAL development installation and Cython.
The build probes `gdal-config` for include/library flags and API version, or
accepts an explicit `GDAL_CONFIG` or `GDAL_VERSION`. The checked source build
rejects GDAL versions below 3.1. A typical explicit build is:

```console
GDAL_CONFIG=/path/to/gdal-config python -m pip install --no-binary fiona fiona
```

The path above is a placeholder for the user's installation; do not copy a
machine-specific path into a shared skill. On systems without `gdal-config`,
configure include directories, libraries, and library directories through the
build system or use a package-manager distribution that supplies them.

## Extras

- Base runtime: `attrs`, `certifi`, `click`, `click-plugins`, and `cligj`.
- `fiona[calc]`: `pyparsing` and Shapely for expression/pipeline commands.
- `fiona[s3]`: boto3 for authenticated or unsigned S3 session setup.
- `fiona[test]`: focused test and optional remote-filesystem dependencies.
- Avoid `all` unless every selected surface is required; it expands the test,
  S3, and calc groups together.

After installing, run `python -m pip check`, import Fiona, print its GDAL
release, and inspect `fiona.supported_drivers`. An install that succeeds but
cannot import compiled extensions is not usable.
