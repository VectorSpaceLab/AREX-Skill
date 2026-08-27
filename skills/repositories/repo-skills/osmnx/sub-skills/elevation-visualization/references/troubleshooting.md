# Troubleshooting

## Missing optional dependencies

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError` from any `plot_*` helper or color helper | `matplotlib` is not installed | Install the `visualization` extra or install `matplotlib`, then rerun with a headless backend if needed. |
| `ImportError` from `add_node_elevations_raster` | `rasterio` is not installed | Install the `raster` extra. |
| `ImportError` mentioning `rio-vrt` when you pass multiple raster paths | Multi-raster VRT support is missing | Install `rio-vrt`, or pass a single raster path instead. |

## Raster elevation problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Many `NaN` elevations | The graph CRS does not match the raster CRS, or the nodes fall outside the raster extent | Reproject the graph or raster so they match exactly, then rerun the raster lookup. |
| Unexpectedly slow or fragile raster lookup | Too many CPUs or a multiprocessing-safe entry point is missing | Use `cpus=1` for a quick smoke test, or protect the call with `if __name__ == "__main__":`. |
| Multi-raster lookup fails | The raster files are incompatible or VRT support is unavailable | Make the rasters share CRS and compatible grid assumptions, or build a single merged raster first. |

## Web elevation problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `InsufficientResponseError` | The API returned an empty or malformed response | Check `settings.elevation_url_template`, the API key, and the provider's response format. |
| Rate-limit or quota issues | Requests are too large or too fast | Lower `batch_size` and increase `pause`. |
| All requests hit the wrong endpoint | The template is misconfigured | Make sure `settings.elevation_url_template` includes the right `locations` placeholder and, when needed, `key`. |

## Plotting problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Plot helper fails in headless CI | Matplotlib is using a GUI backend | Set `matplotlib.use("Agg")` before importing OSMnx plotting helpers, then pass `show=False` and `close=True`. |
| Saved file lands in an unexpected location | `filepath` was omitted | Set `settings.imgs_folder` or pass an explicit `filepath`. |
| `plot_graph_route` fails on the route | The route is not a list of node IDs, or the graph is missing node coordinates or edge lengths | Build the route in `routing-analysis`, then return here with a graph that already has `x`, `y`, and `length`. |
| `plot_graph_routes` complains about lengths or types | `routes`, `route_colors`, or `route_linewidths` do not align | Make each iterable the same length, or pass a single scalar color/linewidth. |
| `plot_figure_ground` looks distorted | The graph was projected | Use an unprojected graph for this helper. |
| `plot_orientation` complains about missing bearings | `bearing` edge attributes were never attached | Generate bearings in `routing-analysis` before plotting here. |
| `plot_footprints` ignores some geometries | The input includes points or lines | Pass only Polygon or MultiPolygon geometries. |
| Color helpers raise or return odd bins | The chosen attribute is empty, non-numeric, or has too few unique values for the chosen bin count | Use a numeric attribute, reduce `num_bins`, or switch `equal_size` off. |

## Extra reminders

- `plot_orientation` does not offer `save=True`; save its figure manually if you need a file.
- `plot_graph_route` selects the shortest parallel edge by `length` when multiple edges connect the same nodes.
- If you need to repair projection or graph-model issues, stop and fix those in `graph-modeling-io` first.
