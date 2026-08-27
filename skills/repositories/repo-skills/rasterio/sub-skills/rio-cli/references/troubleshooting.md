# Troubleshooting

## `rio` command is missing

Symptoms:
- `rio: command not found`
- the package imports but no CLI is on PATH

Likely causes:
- The environment that has Rasterio installed is not active.
- The console script entry point was not created.

Recovery:
- Run `python -I -c "import rasterio; print(rasterio.__version__)"` in the intended environment.
- Reinstall Rasterio in that environment if the import succeeds but the entry point is missing.
- Run the bundled `scripts/rio_smoke.py` once PATH is fixed.

## Click parse errors

Symptoms:
- `Error: Invalid value for ...`
- `Error: Missing option ...`
- exit code 2 with usage text

Likely causes:
- A required argument or output path is missing.
- CRS, bounds, or dimensions were malformed.
- Incompatible options were combined.
- A positional path beginning with `-` was parsed as an option.

Recovery:
- Run `rio COMMAND --help` for the exact command.
- Keep numeric bounds in the syntax that the command expects: `rio clip` and `rio rasterize` use one quoted or bracketed string, while `rio warp --bounds` uses four separate values.
- Use canonical CRS strings such as `EPSG:4326`.
- Put `--` before any positional path that starts with `-`.

## Output already exists

Symptoms:
- command exits with an overwrite-protection message.

Likely causes:
- A destination path already exists and the command requires explicit overwrite approval.

Recovery:
- Confirm the destination should be replaced.
- Add `--overwrite` only after the user approves replacing that exact file.

## Invalid CRS, bounds, or grid choices in `rio warp`/`rio clip`

Symptoms:
- `Invalid value for dst_crs`
- `src-nodata must be provided because dst-nodata is not None`
- `--dimensions cannot be used with ...`
- `--bounds`, `--like`, or `--to-data-window` errors
- `Non-rectilinear rasters ... cannot be clipped`

Likely causes:
- Source and destination bounds were confused.
- `--dimensions`, `--res`, and `--bounds` were combined incorrectly.
- Destination nodata was supplied without a source nodata override when the source lacks one.
- A clipped raster was rotated or sheared instead of rectilinear.

Recovery:
- Use `rio info input.tif` to inspect source CRS and bounds first.
- For `rio clip`, use `--geographic` only for lon/lat bounds; otherwise keep bounds in the input CRS or use `--like`.
- Choose one grid-sizing strategy at a time: `--like`, `--dimensions`, `--bounds` + `--res`, or `--to-data-window`.
- Route rotated or sheared rasters to `rio warp` or Python instead of `rio clip`.

## Invalid expression or band selection in `rio calc`

Symptoms:
- `Expression Error:`
- a caret points at the bad part of the expression
- `shape mismatch` or `operands could not be broadcast together`
- exit code 1 from the expression evaluator

Likely causes:
- The snuggs expression is malformed.
- A named input was not declared with `--name`.
- The input datasets have incompatible shapes or band counts.

Recovery:
- Run `rio calc --help` and test one input at a time.
- Add `--name alias=path.tif` when you need stable symbolic names.
- Add `--dtype` or explicit casts if the math can overflow the source type.
- Move branching or multi-step workflows to Python if the expression gets hard to read.

## Invalid GeoJSON or source CRS in `rio rasterize`

Symptoms:
- `invalid CRS.  Must be an EPSG code.`
- `Invalid GeoJSON`
- `GeoJSON does not match crs of existing output raster`

Likely causes:
- The GeoJSON is malformed.
- `--src-crs` was not given as an EPSG code.
- An existing output grid does not match the incoming source features.

Recovery:
- Validate the GeoJSON before invoking `rio rasterize`.
- Use a canonical `EPSG:NNNN` string for `--src-crs`.
- Use `--like` when a template raster should define the output grid.

## Cloud and credential flags

Symptoms:
- S3 or HTTPS paths fail while local paths work.
- Errors mention credentials, requester pays, range requests, or HTTP status codes.

Likely causes:
- Optional `s3` dependencies are not installed.
- Credentials or anonymous access flags are missing.
- The remote object requires network access or payment configuration.

Recovery:
- Install the optional cloud extra only when the user wants cloud access.
- Use `--aws-no-sign-requests` only for public anonymous buckets.
- Use `--aws-requester-pays` only when the user accepts requester-pays charges.
- Prefer local fixture checks during skill verification.
