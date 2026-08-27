# Troubleshooting

## Missing import or broken install

Symptoms:
- `ImportError: No module named rasterio`
- `ModuleNotFoundError` for `rasterio._base` or similar compiled modules
- `rio --help` is missing

Likely causes:
- Rasterio is installed in the wrong environment.
- GDAL/PROJ libraries are missing or mismatched.
- The editable install did not build against a usable GDAL runtime.

Recovery:
- Run `python -m pip check`.
- Re-run `scripts/check_install.py`.
- Confirm the environment has Python 3.12+ and a working GDAL/PROJ stack.

## `rasterio.open` write-mode errors

Symptoms:
- `TypeError` for missing `dtype` or `count`
- `ValueError` about invalid `nodata`
- `RasterioIOError` while creating or writing a dataset

Likely causes:
- The destination profile is incomplete.
- The nodata value does not fit the dtype.
- The requested driver is unavailable in the installed GDAL build.

Recovery:
- Start from `src.profile.copy()` or `default_gtiff_profile`.
- Update only the fields that actually change.
- Check the output driver and dtype before writing.

## Bad output shape or metadata

Symptoms:
- The output raster opens, but dimensions or georeferencing are wrong.
- The written file has the wrong count or a shape mismatch.

Likely causes:
- The profile was copied but not updated after changing the array shape.
- `width` and `height` were not changed to match the output array.

Recovery:
- Recompute the dimensions before opening the destination.
- Keep the source transform only when the pixel grid is genuinely unchanged.

## Driver-specific confusion

Symptoms:
- GeoTIFF creation options appear to be ignored.
- The output format does not match the file extension you expected.

Likely causes:
- The output driver was copied from the source profile.
- The driver was explicitly set, overriding extension-based detection.

Recovery:
- Decide whether you want the driver from the source profile or the destination extension.
- If needed, override `driver` explicitly in the destination profile.
