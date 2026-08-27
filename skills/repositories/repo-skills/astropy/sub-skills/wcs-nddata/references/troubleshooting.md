# WCS and NDData Troubleshooting

## Pixel/World Results Are Offset by One

Likely origin mismatch. Use `origin=0` for NumPy/Python coordinates and
`origin=1` for FITS/DS9-style coordinates with `all_pix2world` and
`all_world2pix`. High-level `pixel_to_world` uses zero-based pixel coordinates.

## Axis Order Is Reversed

NumPy array indices are `(row, column)` while WCS pixel coordinates are often
`(x, y)`. Prefer `array_index_to_world` and `world_to_array_index` when starting
from array indices. Inspect `pixel_axis_names` and `world_axis_physical_types`
for higher-dimensional data.

## WCS Warnings from FITS Headers

`FITSFixedWarning` or WCS warnings may mean Astropy normalized non-standard
header cards. Capture the warning, inspect affected keywords, and document why
accepting the fix is safe. Use `relax`, `fix`, `translate_units`, and
`preserve_units` intentionally.

## Distortion Pipeline Confusion

`all_pix2world` includes more distortion corrections than `wcs_pix2world`.
Do not demand equality between those methods when SIP or lookup-table
distortions are present; choose the method matching the science requirement.

## WCS Iterative Inversion Fails

For `all_world2pix` convergence errors, check that world coordinates are inside
or near the image footprint, the header is valid, and distortion terms are
reasonable. Try a smaller domain or inspect the exception diagnostics before
changing tolerance.

## NDData Shapes Do Not Align

Data, mask, uncertainty, and WCS must describe the same array shape. Boolean
masks use `True` for invalid pixels. When slicing or making cutouts, verify that
WCS metadata updates with the data.

## CCDData Unit Problems

`CCDData` expects a unit. For FITS input, check `BUNIT`; for generated data,
pass `unit=` explicitly. Avoid stripping units before arithmetic that should
propagate physical meaning.
