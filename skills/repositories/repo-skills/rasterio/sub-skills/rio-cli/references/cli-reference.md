# CLI Reference

## Read this when

You need to choose a `rio` command, build a safe shell command, or understand the JSON/GeoJSON output patterns.

## Global pattern

```bash
rio [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] ...
```

Useful global options:

- `-v` / `--verbose` and `-q` / `--quiet` adjust logging.
- `--version` prints the Rasterio version.
- `--gdal-version` prints the GDAL runtime version.
- `--show-versions` prints system, Python, GDAL, and dependency versions.
- `--aws-profile`, `--aws-no-sign-requests`, and `--aws-requester-pays` apply to cloud access workflows that have the optional dependencies and credentials configured.

## Command map

| Command | Use when | Common output |
| --- | --- | --- |
| `info` | inspect driver, count, CRS, bounds, dtype, transform, tags, stats | JSON or scalar text |
| `bounds` | print raster bounds as GeoJSON, bbox, projected, geographic, or mercator coordinates | GeoJSON or bbox |
| `transform` | transform coordinate arrays between CRSs or dataset CRS | JSON coordinate arrays |
| `env` | inspect GDAL/Rasterio environment and formats | text |
| `blocks` | inspect internal block windows | GeoJSON |
| `calc` | evaluate short expressions across one or more raster inputs | output raster |
| `clip` | clip to bounds, template, or data window | output raster |
| `create` | create an empty/filled dataset | output raster |
| `convert` | copy/scale/change raster dtype or format | output raster |
| `warp` | reproject, resize, or resample a raster | output raster |
| `mask` | mask pixels using GeoJSON features | output raster |
| `rasterize` | burn GeoJSON features into a raster | output raster |
| `shapes` | extract raster shapes/features | GeoJSON stream or collection |
| `merge` | mosaic multiple raster datasets | output raster |
| `stack` | combine bands/files into a multiband raster | output raster |
| `overview` | build or list overviews | modified raster or text |
| `sample` | sample raster values at input coordinates | JSON arrays |
| `gcps` | print ground control points | GeoJSON |
| `edit-info` | update CRS, transform, nodata, tags, color interpretation | modified raster |
| `insp` | open an interactive inspector | REPL session |
| `rm` | delete a dataset and sidecar files | file deletion |

## Common examples

Metadata:

```bash
rio info input.tif --indent 2
rio info input.tif --count
rio info input.tif --bounds
rio info input.tif --tags
rio info input.tif --stats --bidx 2
```

Bounds and coordinates:

```bash
rio bounds input.tif --bbox --precision 2
rio bounds input.tif --bbox --projected
printf '[-78.0, 23.0]\n' | rio transform --dst-crs EPSG:32618 --precision 2
```

Calculation and clipping:

```bash
rio calc "(+ 2 (* 0.95 (read 1)))" input.tif output.tif
rio clip input.tif output.tif --bounds "[xmin, ymin, xmax, ymax]"
rio clip input.tif output.tif --to-data-window
rio clip input.tif output.tif --geographic --bounds "[-78, 23, -76, 25]"
```

Creation options:

```bash
rio create output.tif -f GTiff -t uint8 -n 3 -h 512 -w 512 --co tiled=true --co blockxsize=256 --co blockysize=256
rio convert input.tif output.tif --dtype uint8 --scale-ratio 0.0625
```

Clip and warp:

```bash
rio clip input.tif output.tif --like template.tif
rio warp input.tif output.tif --dst-crs EPSG:4326
rio warp input.tif output.tif --dst-crs EPSG:4326 --res 0.01
```

Feature commands:

```bash
rio shapes input.tif --bidx 1 --precision 6 --collection > shapes.geojson
rio rasterize features.geojson output.tif --dimensions 1024 1024 --src-crs EPSG:4326
rio mask input.tif output.tif --crop --geojson-mask mask.geojson
```

Multi-raster commands:

```bash
rio merge a.tif b.tif merged.tif
rio stack red.tif green.tif blue.tif rgb.tif
```

## Safe flag patterns

- `rio calc` is for short expressions and band math. Use `--name alias=path.tif` when you need named inputs, and add `--dtype` if the result may overflow the source type.
- `rio clip` uses a single `--bounds` string, for example `--bounds "xmin ymin xmax ymax"` or `--bounds "[xmin, ymin, xmax, ymax]"`. Use `--geographic` when those bounds are lon/lat, `--like` to borrow a template grid, and `--to-data-window` to crop to valid data instead of supplying bounds.
- `rio warp` chooses one grid strategy at a time. `--like` excludes `--dimensions`, `--bounds`, `--dst-crs`, and `--res`; `--dimensions` excludes `--bounds` and `--res`; `--src-bounds` and destination `--bounds` are mutually exclusive; `--target-aligned-pixels` requires `--res`; and `--dst-nodata` needs `--src-nodata` when the source has no nodata.
- `rio rasterize` accepts EPSG-only `--src-crs` strings in this CLI version. Use `--like` when a template raster should define the output grid.
- Bounds flags are not all the same: `clip`, `create`, and `rasterize` accept a single quoted or bracketed string, while `warp --bounds` and `warp --src-bounds` take four separate float values.

## Safety notes

- Confirm output paths before commands that create, edit, overwrite, or remove datasets.
- Use explicit `--overwrite` only when replacing a file is intentional.
- Treat cloud/S3 commands as optional-extra workflows and avoid them without user approval for credentials/network use.
- For complex branching or repeated operations, prefer Python API workflows from the other sub-skills.
