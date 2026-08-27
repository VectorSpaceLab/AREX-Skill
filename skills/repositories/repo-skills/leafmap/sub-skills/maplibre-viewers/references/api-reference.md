# MapLibre Viewers API Reference

## Purpose

This reference captures the verified MapLibre HTML and CLI entry points.

## Verified entry points

| API | Verified signature | Use |
| --- | --- | --- |
| `leafmap.maplibregl.Map` | `center=(0, 20), zoom=1, pitch=0, bearing=0, style='dark-matter', height='600px', controls=..., projection='mercator', use_message_queue=None, add_sidebar=None, add_floating_sidebar=None, sidebar_visible=False, sidebar_width=360, sidebar_args=None, layer_manager_expanded=True, **kwargs` | MapLibre GL map object.
| `Map.add_vector` | `data, layer_type=None, filter=None, paint=None, name=None, fit_bounds=True, visible=True, before_id=None, source_args={}, overwrite=False, **kwargs` | Add a vector source/layer.
| `Map.add_geojson` | verified callable | Add GeoJSON data.
| `Map.add_raster` | `source, indexes=None, colormap=None, vmin=None, vmax=None, nodata=None, name='Raster', before_id=None, fit_bounds=True, visible=True, opacity=1.0, array_args={}, client_args={'cors_all': True}, overwrite=True, **kwargs` | Add a raster source/layer.
| `Map.add_pmtiles` | verified callable | Add a PMTiles layer.
| `Map.add_layer_control` | verified callable | Add MapLibre layer controls.
| `Map.to_html` | `output=None, title='My Awesome Map', width='100%', height='100%', replace_key=False, remove_port=True, preview=False, overwrite=False, **kwargs` | Export standalone HTML.
| `Map.to_streamlit` | verified callable | Embed in Streamlit.
| `Map.set_sidebar_content` | verified callable | Replace sidebar content.
| `Map.add_to_sidebar` | verified callable | Add a widget to the sidebar.
| `Map.remove_from_sidebar` | verified callable | Remove a sidebar widget.
| `Map.set_sidebar_width` | verified callable | Adjust sidebar width.
| `Map.add_to_map_container` | verified callable | Add widgets to the map container.
| `leafmap.cli.view_vector` | `file_path, style='dark-matter', open_browser=True` | View a vector file in the browser.
| `leafmap.cli.view_raster` | `file_path, port=None, indexes=None, colormap=None, vmin=None, vmax=None, nodata=None, open_browser=True` | View a raster file in the browser.
| `leafmap.view_pmtiles` | convenience wrapper | Build a PMTiles map without writing the full MapLibre composition manually.
| `leafmap.cli.view_vector_cli` | CLI parser entry point | `view-vector` command.
| `leafmap.cli.view_raster_cli` | CLI parser entry point | `view-raster` command.

## Notes from inspection

- `python -m leafmap --help` exposes the two subcommands.
- `view-vector` is the safest quick smoke because it does not need a long-running server.
- `view-raster` intentionally keeps the tile server alive until interrupted.

## Validation path

- Use `scripts/check_leafmap_smoke.py --mode maplibre` for the MapLibre HTML smoke.
- Use `scripts/check_leafmap_smoke.py --mode cli` for the CLI help smoke.
