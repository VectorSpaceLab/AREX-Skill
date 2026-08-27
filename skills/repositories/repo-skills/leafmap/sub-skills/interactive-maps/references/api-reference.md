# Interactive Maps API Reference

## Purpose

This reference captures the verified high-frequency map entry points for the interactive notebook workflow.

## Verified entry points

| API | Verified signature | Use |
| --- | --- | --- |
| `leafmap.leafmap.Map` | `__init__(self, **kwargs)` | Default ipyleaflet map.
| `leafmap.foliumap.Map` | `__init__(self, **kwargs)` | Folium backend map.
| `leafmap.Map` | backend-selected alias | Top-level convenience import.
| `leafmap.split_map` | public helper | Two-layer split comparison.
| `leafmap.linked_maps` | public helper | Multiple synchronized maps.
| `leafmap.basemaps` | boxed basemap registry | Basemap lookup by name.
| `leafmap.colormaps.create_colormap` | verified callable | Standalone colormap rendering.
| `leafmap.toolbar.main_toolbar` | `main_toolbar(m) -> Widget` | Attach the ipyleaflet toolbar.
| `leafmap.toolbar.save_map` | verified callable | Save/export map artifacts.
| `leafmap.toolbar.open_data_widget` | verified callable | Open the data-loading widget.
| `leafmap.toolbar.change_basemap` | verified callable | Switch basemaps from the toolbar.
| `leafmap.toolbar.tool_template` | verified callable | Build a custom widget palette.

## High-frequency map methods

These methods are the ones future agents are most likely to need first:

- `add_basemap(...)`
- `add_tile_layer(...)`
- `add_wms_layer(...)`
- `add_gdf(...)`
- `add_geojson(...)`
- `add_vector(...)`
- `add_xy_data(...)`
- `add_circle_markers_from_xy(...)`
- `add_point_layer(...)`
- `add_heatmap(...)`
- `add_legend(...)`
- `add_colorbar(...)`
- `add_time_slider(...)`
- `add_minimap(...)`
- `layer_opacity(...)`
- `zoom_to_bounds(...)`
- `zoom_to_gdf(...)`
- `to_html(...)`
- `to_image(...)` where available

## Backend guidance

- `leafmap.leafmap` is the richer notebook backend.
- `leafmap.foliumap` is the static/HTML-friendly backend and is also the fallback in Colab and marimo.
- `leafmap.Map` is the natural starting point when you do not yet know which backend the user needs.

## Notes from inspection

- `leafmap.leafmap.Map.__init__` accepts arbitrary keyword arguments and wraps `ipyleaflet.Map`.
- `leafmap.foliumap.Map.__init__` also accepts arbitrary keyword arguments and wraps `folium.Map`.
- Both backends share a large user-facing API surface, but not every method behaves the same way.
- If a helper raises `NotImplementedError` in the folium backend, switch to the ipyleaflet backend or explain the difference explicitly.
