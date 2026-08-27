# Troubleshooting

## Install or import problems

- If `rtree` fails to import because `libspatialindex_c` is missing, install the system `libspatialindex` package or use the supported container image.
- If `rasterize` fails with CRS or PROJ database lookup errors, use a `pyproj` build with a complete CRS database and keep the install within the project's compatibility range.
- If `rasterio` or `pyproj` wheels fail to install, start from a fresh Python 3.6 environment or the supported container instead of mixing system libraries.

## Network and token problems

- `rs download` needs a reachable Slippy Map endpoint.
- If the endpoint requires a token, keep it in the shell environment or request URL template outside the skill tree.
- If downloads fail, check the `{z}`, `{x}`, and `{y}` placeholders, the file extension, and the request rate limit.

## Empty tiles or empty masks

- Make sure the CSV contains the expected tile ids and is not empty.
- Confirm that the OSM handler matches the feature type you want.
- Empty masks can come from a zoom mismatch, an empty feature collection, invalid geometry, or a tile list that points at the wrong area.
- If imagery is empty, check that the source endpoint actually serves the requested zoom and that the tile ids line up with the masks.

## Zoom mismatch

- `rs rasterize` requires every tile in the CSV to share one zoom level.
- The `--zoom` argument must match that zoom exactly.
- If the zoom does not match, regenerate the tile CSV before rasterization.

## Binary-class limits

- `rs rasterize` only accepts two classes and two colors in this release.
- Masks must be single-channel PNGs with a palette and class indices starting at zero.
- If you need more than background/foreground, split the task or route to a different skill.

## Missing or stale weights

- Run `rs weights --dataset <dataset.toml>` after the training labels exist.
- Paste the printed list into `[weights].values`.
- Recompute weights whenever the mask distribution changes materially.

## Tile sync errors

- Images, labels, and any derived Slippy Map trees must share the same `z/x/y` ids.
- Use `scripts/validate_slippy_map.py <root> --tiles-csv <tiles.csv>` to catch missing tiles, extra tiles, duplicate tiles, and unreadable images.
- If a dataset is intentionally partial, keep the companion CSV and every tree in sync by design.

## Rasterize corner cases

- `rs rasterize` warns and skips invalid features.
- `feature_to_mercator` accepts Polygon and MultiPolygon geometries.
- Existing mask files are combined with pixel-wise maximum, so reruns can preserve earlier foreground pixels.
