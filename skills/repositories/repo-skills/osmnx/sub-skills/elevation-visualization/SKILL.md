---
name: elevation-visualization
description: "Attach node elevations, compute edge grades, and produce static
  OSMnx plots with optional raster and headless guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# elevation-visualization

Use this sub-skill when an OSMnx graph or features GeoDataFrame already exists and the remaining work is to:

- attach node elevations from a local raster file or a Google-compatible elevation endpoint
- calculate edge grades from node elevations and edge lengths
- render static plots, route overlays, figure-ground diagrams, building footprints, or orientation roses
- control image output with `settings.imgs_folder`
- adjust elevation requests with `settings.elevation_url_template`

Do **not** use this sub-skill when the task is really about:

- downloading graphs or features
- choosing origins/destinations or solving routes
- fixing CRS, projection, validation, or graph/GeoDataFrame IO

## Fast routing rules

- Need graph or feature acquisition? Use the `data-acquisition` sub-skill.
- Need route calculation or path selection? Use the `routing-analysis` sub-skill.
- Need projection or IO fixes? Use the `graph-modeling-io` sub-skill.
- Need edge bearings for orientation plots? Generate them in `routing-analysis`, then return here for plotting.

## Primary workflow

1. Confirm the graph already has coordinates and lengths.
2. Choose the elevation source:
   - local raster(s): `ox.elevation.add_node_elevations_raster`
   - web endpoint: `ox.elevation.add_node_elevations_google`
3. After node elevations exist, call `ox.add_edge_grades` or `ox.elevation.add_edge_grades`.
4. Pick the plot helper that matches the output you want.
5. For batch or headless runs, save with `show=False`, `close=True`, and a writable image folder.

## Reference files

- [Elevation reference](references/elevation-reference.md)
- [Plotting reference](references/plotting-reference.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke script](scripts/elevation_plot_smoke.py)

## Validation checklist

- Raster path: graph CRS matches the raster CRS exactly.
- Multi-raster path: all rasters use compatible CRS/resolution; use VRT support when available.
- Web path: the elevation URL template accepts `locations` and optional `key` placeholders.
- Plot path: `matplotlib` is available, `settings.imgs_folder` is writable, and the inputs match the chosen plot helper.
- Orientation path: edge `bearing` attributes already exist before calling `plot_orientation`.

## Intentional scope limits

- This sub-skill does not cover interactive Folium maps.
- This sub-skill does not calculate routes, nearest points, or graph download queries.
- This sub-skill does not repair CRS or graph IO problems; fix those first elsewhere.
