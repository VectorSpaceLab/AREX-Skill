# Interactive Maps Workflows

## Purpose

Use these recipes when you already know you want a notebook map and need the shortest safe path.

## Minimal map

```python
import leafmap

m = leafmap.Map(center=(40, -100), zoom=4)
m
```

If the environment should use folium instead:

```python
import leafmap.foliumap as leafmap

m = leafmap.Map(center=(40, -100), zoom=4)
m
```

## Change the basemap

```python
m = leafmap.Map()
m.add_basemap("Satellite")
```

## Add a vector layer

Use the layer type that matches the data you already have:

```python
m.add_geojson(data_or_path, layer_name="My layer")
m.add_gdf(gdf, layer_name="My layer")
m.add_vector(data_or_path, layer_name="My layer")
```

## Add a WMS or tile layer

```python
m.add_tile_layer(
    url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    name="Google Satellite",
    attribution="Google",
)
```

```python
m.add_wms_layer(
    url=wms_url,
    layers="0",
    name="Raster service",
    format="image/png",
    shown=True,
)
```

## Legends, colorbars, and widgets

- Use `m.add_legend(...)` when the map already has a thematic layer.
- Use `m.add_colorbar(...)` or `leafmap.colormaps.create_colormap(...)` for numeric color scales.
- Use `leafmap.toolbar.main_toolbar(m)` when you need the full ipyleaflet toolset.
- Use `leafmap.toolbar.save_map(m)` when the user wants save/export controls.

## Split and linked maps

- Use `leafmap.split_map(...)` for one comparison.
- Use `leafmap.linked_maps(...)` for synchronized multiple-map views.

## Export and sharing

- Use `m.to_html(...)` when the user needs a portable HTML artifact.
- Keep folium in mind when the output must render without notebook widgets.

## Validation steps

- Start with `scripts/check_leafmap_smoke.py --mode core`.
- If the request depends on local data conversion, follow up with `--mode data`.
- If the user only needs a quick example, prefer the root smoke helper before a large notebook or service workflow.
