# Plotting reference

## Optional dependency and output defaults

- Static plotting uses the `visualization` extra, which provides `matplotlib`.
- In scripts or CI, set the backend to `Agg` before importing OSMnx plotting helpers if a display is unavailable.
- When `save=True` and `filepath=None`, graph and footprint plots save to `settings.imgs_folder/image.png`.
- `settings.imgs_folder` should point at a writable directory.

## Color helpers

| API | Use | Notes |
| --- | --- | --- |
| `ox.plot.get_colors(n, cmap="viridis", start=0, stop=1, alpha=None)` | Sample evenly spaced colors from a colormap | Returns hex strings. Use `alpha` to get RGBA hex strings. |
| `ox.plot.get_node_colors_by_attr(G, attr, num_bins=None, cmap="viridis", start=0, stop=1, na_color="none", equal_size=False)` | Color nodes by a numeric attribute | `num_bins=None` maps continuously; a positive `num_bins` bins values with `cut` or `qcut`. |
| `ox.plot.get_edge_colors_by_attr(G, attr, num_bins=None, cmap="viridis", start=0, stop=1, na_color="none", equal_size=False)` | Color edges by a numeric attribute | Same binning behavior as the node helper. |

## Graph and route plots

| API | Expected input | Key parameters | Output notes |
| --- | --- | --- | --- |
| `ox.plot_graph(G, ax=None, figsize=(8, 8), bgcolor="#111111", node_color="w", node_size=15, node_alpha=None, node_edgecolor="none", node_zorder=1, edge_color="#999999", edge_linewidth=1, edge_alpha=None, bbox=None, show=True, close=False, save=False, filepath=None, dpi=300)` | `MultiGraph` or `MultiDiGraph` with node coordinates and a graph CRS | `bbox` is `(left, bottom, right, top)`. `save=True` uses `settings.imgs_folder` when `filepath` is omitted. | Great general-purpose static graph plot. If both node size and edge width are zero, it raises a `ValueError`. |
| `ox.plot_graph_route(G, route, route_color="r", route_linewidth=4, route_alpha=0.5, orig_dest_size=100, ax=None, **pg_kwargs)` | A route as a list of node IDs | `pg_kwargs` passes through to `plot_graph` and `_save_and_show` | Draws the path on top of the graph. For parallel edges, it chooses the shortest edge by `length`. |
| `ox.plot_graph_routes(G, routes, route_colors="r", route_linewidths=4, **pgr_kwargs)` | An iterable of route lists | Route colors and line widths must match route count when passed as iterables | Overlays multiple routes on one graph. |

## Specialized plot helpers

| API | Expected input | Important assumptions | Notes |
| --- | --- | --- | --- |
| `ox.plot_figure_ground(G, dist=805, street_widths=None, default_width=4, color="w", **pg_kwargs)` | An unprojected street graph | Uses `highway` edge tags to choose widths | Good for figure-ground diagrams. Pass custom `street_widths` when you want to emphasize different street classes. |
| `ox.plot_footprints(gdf, ax=None, figsize=(8, 8), color="orange", edge_color="none", edge_linewidth=0, alpha=None, bgcolor="#111111", bbox=None, show=True, close=False, save=False, filepath=None, dpi=600)` | A GeoDataFrame of polygons or multipolygons | Non-polygon geometries are filtered out before plotting | Useful for building footprints or other polygon features. |
| `ox.plot_orientation(G, num_bins=36, min_length=0, weight=None, ax=None, figsize=(5, 5), area=True, color="#003366", edgecolor="k", linewidth=0.5, alpha=0.7, title=None, title_y=1.05, title_font=None, xtick_font=None)` | An unprojected graph with `bearing` edge attributes | Bearings must already be attached elsewhere | Returns a figure and polar axes. Save it manually with `fig.savefig(...)` if needed; this helper does not expose `save=True`. |

## Headless recipe

1. Select the `visualization` extra or install `matplotlib` directly.
2. Set the backend to `Agg` before importing OSMnx in scripts.
3. Pass `show=False` and `close=True` for batch runs.
4. Set `save=True` and either rely on `settings.imgs_folder` or pass an explicit `filepath`.

## Validation steps

- Verify that your graph has the expected coordinate system before choosing a plot helper.
- Verify that routes are lists of node IDs, not edge tuples.
- Verify that polygon plots receive polygonal geometries only.
- Verify that `bearing` attributes exist before using `plot_orientation`.
