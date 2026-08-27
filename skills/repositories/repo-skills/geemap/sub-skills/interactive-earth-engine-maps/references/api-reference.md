# Interactive Map API Reference

This reference records verified geemap map surfaces for future agents. Use it to choose imports, call signatures, aliases, and backend-specific alternatives without reopening the source repository.

## Backend imports

| Backend | Import | Main class | Use when |
|---|---|---|---|
| ipyleaflet | `import geemap.geemap as geemap` | `geemap.Map` | Rich Jupyter interaction, draw controls, Inspector, Layer Manager, split maps, layer editing. |
| ipyleaflet core | `from geemap import core` | `core.Map` | Lower-level map object and shared widget infrastructure. |
| folium | `import geemap.foliumap as geemap` | `geemap.Map` | Portable Leaflet HTML, simple maps, static Streamlit embedding. |
| top-level | `import geemap` | environment-dependent `geemap.Map` | Defaults to ipyleaflet unless `USE_FOLIUM` is set. Prefer explicit imports in reusable answers. |

## Constructor behavior

### ipyleaflet `geemap.Map` / `geemap.geemap.Map`

Common parameters:

```python
geemap.Map(
    center=(20, 0),
    zoom=2,
    height="600px",
    width="100%",
    basemap="ROADMAP",
    ee_initialize=True,
    draw_ctrl=True,
    search_ctrl=True,
    toolbar_ctrl=True,
    layer_ctrl=False,
    **ipyleaflet_kwargs,
)
```

The class inherits `geemap.core.Map`, which inherits `ipyleaflet.Map`. Use `ee_initialize=False` for offline smoke checks.

### folium `geemap.foliumap.Map`

Common parameters:

```python
geemap.Map(
    center=(20, 0),
    zoom=2,
    ee_initialize=True,
    add_google_map=True,
    basemap="ROADMAP",
    **folium_kwargs,
)
```

Folium accepts `center` and `zoom` as geemap-compatible aliases and maps them to folium location and zoom-start behavior.

## Core map positioning

| Method | Verified signature | Backends | Notes |
|---|---|---|---|
| `set_center` | `(lon: float, lat: float, zoom: int | None = None) -> None` | ipyleaflet, folium | Longitude first, latitude second. Folium defaults zoom to `10` if omitted. |
| `setCenter` | alias of `set_center` | ipyleaflet, folium | JavaScript-style alias. |
| `center_object` | `(ee_object, zoom: int | None = None, max_error: float = 0.001) -> None` | ipyleaflet, folium | Requires an EE geometry, feature, collection, image, or image collection. With no zoom, fits bounds; with zoom, centers on centroid. |
| `centerObject` | alias of `center_object` | ipyleaflet, folium | JavaScript-style alias. |

`center_object()` may call Earth Engine methods such as `geometry()`, `bounds()`, `centroid()`, and `getInfo()`, so it needs initialized credentials and network access for real EE objects.

## Earth Engine layers

| Method | Verified signature | Backends | Notes |
|---|---|---|---|
| `add_layer` | `(ee_object, vis_params=None, name=None, shown=True, opacity=1.0) -> None` | ipyleaflet/core, folium | Adds an EE object as a tile layer. Core delegates non-EE layers to ipyleaflet. |
| `addLayer` | same conceptual signature | ipyleaflet, folium | JavaScript-style alias. |
| `add_ee_layer` | `(ee_object, vis_params=None, name=None, shown=True, opacity=1.0) -> None` | ipyleaflet high-level map | High-level alias that records raster layer state and ArcGIS integration hooks when available. |

Supported EE object families include `ee.Image`, `ee.ImageCollection`, `ee.Geometry`, `ee.Feature`, and `ee.FeatureCollection`. `ee.ImageCollection` inputs are mosaicked for display. Visualization parameters accept dictionaries; palette validation belongs to `geemap.ee_tile_layers`.

## Basemaps and external tile layers

| Method or helper | Verified signature | Backends | Notes |
|---|---|---|---|
| `add_basemap` | `ipyleaflet: (basemap="ROADMAP", show=True, **kwargs)` | ipyleaflet | Accepts provider names, compatibility aliases, provider objects, and URL strings. |
| `add_basemap` | `folium: (basemap="HYBRID", show=True, **kwargs)` | folium | Adds folium tile or WMS basemaps from the folium provider registry. |
| `add_tile_layer` | `ipyleaflet: (url, name="Untitled", attribution="", opacity=1.0, shown=True, **kwargs)` | ipyleaflet | Uses `url=`. Defaults high max zoom values when omitted. |
| `add_tile_layer` | `folium: (tiles="OpenStreetMap", name="Untitled", attribution=".", overlay=True, control=True, shown=True, opacity=1.0, API_key=None, **kwargs)` | folium | Uses `tiles=`. |
| `add_wms_layer` | `ipyleaflet: (url, layers, name=None, attribution="", format="image/png", transparent=True, opacity=1.0, shown=True, **kwargs)` | ipyleaflet | Adds an ipyleaflet WMS layer. |
| `add_wms_layer` | `folium: (url, layers, name=None, attribution="", overlay=True, control=True, shown=True, format="image/png", transparent=True, version="1.1.1", styles="", **kwargs)` | folium | Adds a folium WMS tile layer. |
| `geemap.basemaps.get_xyz_dict` | `(free_only=True, france=False) -> dict` | helper submodule | Returns provider metadata; can filter paid-token and France-specific layers. |
| `geemap.basemaps.xyz_to_leaflet` | `() -> dict` | helper submodule | Converts providers to ipyleaflet tile layers. |
| `geemap.basemaps.xyz_to_folium` | `() -> dict` | helper submodule | Converts providers to folium tile layers. |

Important nuance: backend modules also expose a variable named `basemaps`, which can shadow the helper submodule name. If helper functions are needed, import the submodule explicitly, for example `import geemap.basemaps as basemap_helpers`.

## Split maps

| Method | Verified signature | Backends | Notes |
|---|---|---|---|
| `split_map` | `ipyleaflet: (left_layer="OpenTopoMap", right_layer="Esri.WorldTopoMap", zoom_control=True, fullscreen_control=True, layer_control=True, add_close_button=False, close_button_position="topright", left_label=None, right_label=None, left_position="bottomleft", right_position="bottomright", widget_layout=None, **kwargs)` | ipyleaflet | Creates an ipyleaflet side-by-side split control. |
| `split_map` | `folium: (left_layer="TERRAIN", right_layer="OpenTopoMap", left_args=None, right_args=None, left_label=None, right_label=None, left_position="bottomleft", right_position="bottomright", **kwargs)` | folium | Creates Leaflet side-by-side behavior using folium layers. |

## Local raster, COG, and STAC layers

| Method | Verified signature | Backends | Notes |
|---|---|---|---|
| `add_raster` | `ipyleaflet: (source, indexes=None, colormap=None, vmin=None, vmax=None, nodata=None, attribution=None, layer_name="Raster", zoom_to_layer=True, visible=True, array_args=None, **kwargs)` | ipyleaflet | Uses local tile serving; accepts local raster path, NumPy array, or xarray data array. |
| `add_raster` | `folium: (source, indexes=None, colormap=None, vmin=None, vmax=None, nodata=None, attribution=None, layer_name="Raster", array_args=None, **kwargs)` | folium | Uses local tile serving and adds a folium tile layer. |
| `add_cog_layer` | `(url, name="Untitled", attribution="", opacity=1.0, shown=True, bands=None, titiler_endpoint=None, **kwargs)` | ipyleaflet | Contacts a titiler-compatible endpoint to obtain tiles and bounds. |
| `add_cog_layer` | `(url, name="Untitled", attribution=".", opacity=1.0, shown=True, bands=None, titiler_endpoint=None, **kwargs)` | folium | Same concept with folium tile output. |
| `add_stac_layer` | `(url=None, collection=None, item=None, assets=None, bands=None, titiler_endpoint=None, name="STAC Layer", attribution="", opacity=1.0, shown=True, **kwargs)` | ipyleaflet | Uses STAC metadata and a titiler endpoint. |
| `add_stac_layer` | `(url=None, collection=None, item=None, assets=None, bands=None, titiler_endpoint=None, name="STAC Layer", attribution=".", opacity=1.0, shown=True, **kwargs)` | folium | Same concept with folium tile output. |

These methods are not Earth Engine export methods. Route data export, URL-only helper calls, or format conversion to [conversion-and-io](../../conversion-and-io/SKILL.md).

## Widgets and presentation

| Method | Verified signature | Backends | Notes |
|---|---|---|---|
| `add_draw_control` | `(position="topleft") -> None` | ipyleaflet high-level map | Adds drawing controls and synchronizes drawn geometries/features. |
| `add_layer_manager` | `(position="topright", opened=True, show_close_button=True) -> None` | ipyleaflet high-level map | Adds the Layer Manager widget. |
| `add_inspector` | `(names=None, visible=True, decimals=2, position="topright", opened=True, show_close_button=True) -> None` | ipyleaflet high-level map | Adds the Inspector widget for click-based point/pixel/object inspection. |
| `add_layer_control` / `addLayerControl` | `ipyleaflet: (position="topright") -> None`; `folium: () -> None` | ipyleaflet, folium | Adds a layer control. |
| `add_legend` | `ipyleaflet: (title="Legend", legend_dict=None, keys=None, colors=None, position="bottomright", builtin_legend=None, layer_name=None, add_header=True, widget_args={}, **kwargs)` | ipyleaflet | Uses map widget validation. |
| `add_legend` | `folium: (title="Legend", labels=None, colors=None, legend_dict=None, builtin_legend=None, opacity=1.0, position="bottomright", draggable=True, style=None)` | folium | Produces HTML legend content. |
| `add_colorbar` | `ipyleaflet: (vis_params=None, cmap="gray", discrete=False, label=None, orientation="horizontal", position="bottomright", transparent_bg=False, layer_name=None, font_size=9, axis_off=False, max_width=None, **kwargs)` | ipyleaflet | Validates orientation, min/max, opacity, palette/color inputs through widgets. |
| `add_colorbar` | `folium: (vis_params, index=None, label="", categorical=False, step=None, background_color=None, **kwargs)` | folium | Builds a folium/branca colorbar. |

## Output methods

| Method | Verified signature | Backends | Notes |
|---|---|---|---|
| `to_html` | `ipyleaflet: (filename=None, title="My Map", width="100%", height="880px", add_layer_control=True, **kwargs)` | ipyleaflet | Filename must end with `.html`. Width must end in `px` or `%`; height must end in `px`. Without filename, returns an HTML string. |
| `to_html` | `folium: (filename=None, **kwargs) -> str | None` | folium | Filename must end with `.html`. Without filename, returns an HTML string. |
| `to_streamlit` | `ipyleaflet: (width=None, height=600, scrolling=False, **kwargs)` | ipyleaflet | Embeds `to_html()` through Streamlit components. |
| `to_streamlit` | `folium: (width=None, height=600, scrolling=False, add_layer_control=True, bidirectional=False, **kwargs)` | folium | Static by default; bidirectional mode requires an optional bridge package. |

## Validation signals from native behavior

- `core.Map(ee_initialize=False)` initializes with center `[0, 0]`, zoom `2`, height `600px`, width `100%`, default controls, draw control, toolbar, inspector, and layer manager behavior.
- `set_center(1, 2, 3)` stores center as `[2, 1]` and zoom `3`.
- `center_object()` fits bounds when zoom is omitted, calls `set_center()` on the centroid when zoom is an integer, and raises a zoom type error for non-integer zoom.
- EE tile-layer validation accepts `None` visualization parameters as `{}`, normalizes string palettes to hex color strings, extracts `Box({"default": ...})` palettes, and raises errors for invalid palette types or invalid EE object types.
- Legend validation requires keys and colors to be lists of the same length, validates positions, accepts CSS colors, hex colors, RGB tuples, and known built-in legends.
- Colorbar validation rejects invalid orientation, non-dictionary visualization parameters, and non-scalar min/max/opacity values.
