# Troubleshooting

## Purpose

Read this when Rasterio fails to import, build, or open a file, or when the `rio` CLI reports an error that is not specific to a single workflow.

## Install and import problems

### `ImportError` or `ModuleNotFoundError: rasterio`

Likely causes:
- Rasterio is not installed in the target environment.
- Python is older than 3.12.
- GDAL/PROJ libraries are missing or the wheel/build is incompatible.
- A different checkout or local path is shadowing the installed package.

Recovery:
- Re-run `python -m pip check`.
- Verify `python -I -c "import rasterio; print(rasterio.__version__)"` from outside the checkout.
- Confirm `rio --help` works.
- If building from source, ensure GDAL 3.8+ and PROJ are available.

### Build or editable-install failures

Common symptoms:
- `gdal-config not found`
- `ERROR: A GDAL API version must be specified`
- `Cython is required to build rasterio`
- `RasterioIOError` during import because the compiled extension cannot find GDAL

Recovery:
- Use a wheel or a conda-style environment with GDAL installed.
- Confirm the environment has Python 3.12+, Numpy 2, and a working `gdal-config`/`gdalinfo` pair.
- Re-run `scripts/check_install.py` after fixing the environment.

## File and driver problems

### `RasterioIOError: No such file or directory`

Likely causes:
- The path is wrong.
- The current working directory is not what you expected.
- A `zip://`, `file://`, or `/vsizip/` URI is malformed.

Recovery:
- Use an absolute path or a bundled smoke script that accepts explicit input paths.
- For archive paths, verify the `archive!member` form and the `zip://` scheme.

### Unsupported driver or write mode

Likely causes:
- The requested output driver is not available in the current GDAL build.
- The write profile is missing required keys such as `dtype`, `count`, `width`, or `height`.
- The data type or nodata value is incompatible with the driver.

Recovery:
- Read the dataset profile first and clone it for writes.
- Use `dataset.profile.copy()` and then update only the fields you need.
- For GeoTIFF, use the dataset-specific creation options documented in the dataset-IO sub-skill.

## CLI problems

### `rio` not found or command help fails

Likely causes:
- The package is installed, but the environment's bin directory is not on PATH.
- The install is broken or the entry point was not created.

Recovery:
- Re-run `rio --help` in the target environment.
- If the command is missing, reinstall the package in that environment.
- Use the `rio-cli` sub-skill for command-specific flags and failure messages.

### Invalid option combinations

`rio` uses Click, so parse failures usually point to the exact option pair.
Common examples include:
- `--bounds` with `--like` or `--dimensions`
- malformed CRS strings
- overwrite-protection errors when the output file already exists

Recovery:
- Read the relevant command section in `sub-skills/rio-cli/references/cli-reference.md`.
- Prefer the bundled `scripts/rio_smoke.py` for a safe local check.

## Optional extras

- `rasterio[s3]` is required for S3/cloud-object access helpers.
- `rasterio[plot]` is required for `rasterio.plot` and plotting examples.
- `rasterio[ipython]` helps with `rio insp --ipython`.

If those extras are missing, the core package can still work, but the relevant commands or examples should be treated as unverified.
