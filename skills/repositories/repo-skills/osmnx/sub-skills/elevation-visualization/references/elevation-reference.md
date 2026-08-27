# Elevation reference

## What each function does

| API | Required state | Output | Notes |
| --- | --- | --- | --- |
| `ox.elevation.add_node_elevations_raster(G, filepath, band=1, cpus=None)` | `G` must already have node `x`/`y` coordinates, and the graph CRS must match the raster CRS | Same graph with node `elevation` attributes | Accepts one raster path or an iterable of raster paths. An iterable triggers virtual-raster composition before sampling. `rasterio` is required; `rio-vrt` is required when composing multiple rasters. |
| `ox.elevation.add_node_elevations_google(G, api_key=None, batch_size=512, pause=0)` | `G` must already have node `x`/`y` coordinates | Same graph with node `elevation` attributes | Uses `settings.elevation_url_template`. The endpoint only needs to understand `locations` and, optionally, `key`. `api_key` may be `None` for providers that do not require one. |
| `ox.add_edge_grades(G, add_absolute=True)` or `ox.elevation.add_edge_grades(G, add_absolute=True)` | Nodes already need `elevation`; edges already need `length` | Same graph with edge `grade` and optional `grade_abs` attributes | Grade is rise over run, signed from edge `u` to `v`. |

## Local raster workflow

- Keep the graph and raster in the same CRS.
- Use one raster if you just need a simple sample.
- Use multiple rasters when coverage is split across files; OSMnx builds a VRT from the paths first.
- Use `cpus=1` for the simplest path, or a higher value only when the environment is safe for multiprocessing.
- After the call, inspect `dict(G.nodes(data="elevation"))` or a node GeoDataFrame to confirm the elevations landed.

## Web elevation workflow

- `settings.elevation_url_template` is the request template used by `add_node_elevations_google`.
- The template must include a `{locations}` placeholder.
- Include `{key}` if the endpoint expects an API key.
- Use `batch_size` to stay within provider limits.
- Use `pause` to slow requests when you hit rate limits or want gentler pacing.
- Empty or malformed responses raise `InsufficientResponseError`.

## Edge-grade workflow

- Call grade calculation only after elevations are present.
- Keep `length` on the edges; if it is missing, fix the graph elsewhere before coming back here.
- `add_absolute=True` gives both signed `grade` and `grade_abs`.
- If you simplify or consolidate the graph after elevation work, recompute elevations and grades on the new graph.

## Validation steps

1. Confirm every node has an `elevation` value or an expected `NaN` when coverage is intentionally incomplete.
2. Confirm every edge has `length` before calling grade calculation.
3. Confirm the returned graph still has the same topology you expected.
4. For web requests, confirm the template, key, and provider batch limits before retrying.
