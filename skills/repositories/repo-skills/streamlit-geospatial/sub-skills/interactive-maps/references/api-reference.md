# Inspected API reference

These signatures were inspected from the installed Leafmap package with the
Folium backend selected. They are the contract for this leaf; do not invent
alternate keyword names.

## Module locations matter

Use separate aliases for the package-level discovery helpers and the Folium
map module:

```python
import leafmap                       # discovery helpers
import leafmap.foliumap as folium_map  # Folium map class

xyz_names = leafmap.search_xyz_services("OpenStreetMap")
qms_names = leafmap.search_qms("topography", limit=10)
m = folium_map.Map(center=[40, -100], zoom=4)
```

The inspected package exposes `get_wms_layers`, `search_xyz_services`,
`search_qms`, and `cog_bands` on `leafmap`. The `leafmap.foliumap` module
exposes the search helpers and `cog_bands`, but not `get_wms_layers`. Therefore
use `leafmap.get_wms_layers(url)` for WMS capability discovery rather than
calling it through the `folium_map` alias. `add_cog_layer` and `add_wms_layer`
are instance methods, not module-level functions.

## Folium map and rendering

```text
leafmap.foliumap.Map(**kwargs)
Map.to_streamlit(self, width: Optional[int] = None,
                 height: Optional[int] = 600,
                 scrolling: Optional[bool] = False,
                 add_layer_control: Optional[bool] = True,
                 bidirectional: Optional[bool] = False, **kwargs)
```

The repository examples construct the map with keyword options such as
`center`, `zoom`, `locate_control`, `draw_control`, and
`measure_control`; the constructor itself accepts `**kwargs`. A minimal render
is:

```python
m = folium_map.Map(center=[40, -100], zoom=4)
# add validated layers here
m.to_streamlit(height=600)
```

The relevant inspected instance methods are:

```text
Map.split_map(self, left_layer: Optional[str] = 'TERRAIN',
              right_layer: Optional[str] = 'OpenTopoMap',
              left_args: Optional[dict] = {}, right_args: Optional[dict] = {},
              left_array_args={}, right_array_args={},
              left_label: Optional[str] = None,
              right_label: Optional[str] = None,
              left_position: Optional[str] = 'bottomleft',
              right_position: Optional[str] = 'bottomright', **kwargs)

Map.add_heatmap(self, data: Union[str, List[List[float]], pandas.DataFrame],
                latitude: Optional[str] = 'latitude',
                longitude: Optional[str] = 'longitude',
                value: Optional[str] = 'value',
                name: Optional[str] = 'Heat map',
                radius: Optional[int] = 25, **kwargs)

Map.add_points_from_xy(self, data: Union[str, pandas.DataFrame],
                       x: Optional[str] = 'longitude',
                       y: Optional[str] = 'latitude',
                       popup: Optional[List] = None,
                       min_width: Optional[int] = 100,
                       max_width: Optional[int] = 200,
                       layer_name: Optional[str] = 'Marker Cluster',
                       color_column: Optional[str] = None,
                       marker_colors: Optional[List] = None,
                       icon_colors: Optional[List] = ['white'],
                       icon_names: Optional[List] = ['info'],
                       angle: Optional[int] = 0,
                       prefix: Optional[str] = 'fa',
                       add_legend: Optional[bool] = True,
                       max_cluster_radius: Optional[int] = 80, **kwargs)

Map.add_geojson(self, in_geojson: str,
                layer_name: Optional[str] = 'Untitled',
                encoding: Optional[str] = 'utf-8',
                info_mode: Optional[str] = 'on_hover',
                opacity: Optional[float] = 1.0,
                zoom_to_layer: Optional[bool] = True, **kwargs)

Map.add_gdf(self, gdf,
            layer_name: Optional[str] = 'Untitled',
            zoom_to_layer: Optional[bool] = True,
            info_mode: Optional[str] = 'on_hover',
            opacity: Optional[float] = 1.0, **kwargs)

Map.zoom_to_gdf(self, gdf)
Map.add_xyz_service(self, provider: str, **kwargs)
Map.add_tile_layer(self, url: str, name: str, attribution: str,
                   overlay: Optional[bool] = True,
                   control: Optional[bool] = True,
                   shown: Optional[bool] = True,
                   opacity: Optional[float] = 1.0,
                   API_key: Optional[str] = None, **kwargs)
Map.add_legend(self, title: Optional[str] = 'Legend',
               labels: Optional[List] = None,
               colors: Optional[List] = None,
               legend_dict: Optional[Dict] = None,
               builtin_legend: Optional[str] = None,
               opacity: Optional[float] = 1.0,
               position: Optional[str] = 'bottomright',
               draggable: Optional[bool] = True,
               style: Optional[Dict] = {},
               shape_type: Optional[str] = 'rectangle')
```

`split_map` is used by the examples with named basemap strings and with
prepared Folium tile-layer objects. For a split comparison, pass two already
validated layer specifications and smoke-test the visual order. Do not assume
that a WMS URL and a COG URL have identical split behavior; see the difficult
case in [workflows](workflows.md).

## Discovery helpers and service layers

```text
leafmap.search_xyz_services(keyword, name=None, list_only=True, add_prefix=True)
leafmap.search_qms(keyword, limit=10, list_only=True, add_prefix=True)
leafmap.get_wms_layers(url)
leafmap.cog_bands(url: str, titiler_endpoint: Optional[str] = None) -> List

Map.add_wms_layer(self, url: str, layers: str,
                  name: Optional[str] = None,
                  attribution: Optional[str] = '',
                  overlay: Optional[bool] = True,
                  control: Optional[bool] = True,
                  shown: Optional[bool] = True,
                  format: Optional[str] = 'image/png',
                  transparent: Optional[bool] = True,
                  version: Optional[str] = '1.1.1',
                  styles: Optional[str] = '', **kwargs)

Map.add_cog_layer(self, url: str,
                  name: Optional[str] = 'Untitled',
                  attribution: Optional[str] = '.',
                  opacity: Optional[float] = 1.0,
                  shown: Optional[bool] = True,
                  bands: Optional[List] = None,
                  titiler_endpoint: Optional[str] = None,
                  zoom_to_layer=True, **kwargs)
```

Use `search_xyz_services(keyword=...)` for the selectable provider names, then
pass a selected provider name to `m.add_xyz_service(provider)`. QMS is a
separate search and may add network latency; keep its result list bounded.
`get_wms_layers(url)` is capability discovery and can fail before any map is
created. Call it only after an exact allowlist check and catch its exception.
`cog_bands` discovers band labels and may contact the configured COG service;
call it only for an approved URL. Select exactly one or three bands before
`add_cog_layer` when following the application workflow.

`add_cog_layer` forwards extra visualization keywords through `**kwargs` to
the configured raster service. Validate that visualization input is a JSON
object and use only parameters supported by that endpoint (for example,
`rescale`, `colormap_name`, `color_formula`, `nodata`, or `return_mask` may be
endpoint-dependent). A valid Python dictionary alone does not prove that the
remote service accepts every key.

## Kepler and PyDeck backends

The installed optional backends have these signatures:

```text
leafmap.kepler.Map.__init__(self, **kwargs)
leafmap.kepler.Map.add_gdf(self, gdf,
                           layer_name: Optional[str] = 'Untitled',
                           config: Optional[str] = None, **kwargs)
leafmap.kepler.Map.add_geojson(self, in_geojson: Union[str, dict],
                               layer_name: Optional[str] = 'Untitled',
                               config: Optional[str] = None, **kwargs)
leafmap.kepler.Map.to_streamlit(self, width: Optional[int] = 800,
                                height: Optional[int] = 600,
                                responsive: Optional[bool] = True,
                                scrolling: Optional[bool] = False, **kwargs)
leafmap.kepler.Map.to_html(self, outfile: Optional[str] = None,
                           read_only: Optional[bool] = False, **kwargs)

leafmap.deck.Map.__init__(self, center=(20, 0), zoom=1.2, **kwargs) -> None
leafmap.deck.Map.add_gdf(self, gdf, layer_type='GeoJsonLayer',
                         layer_name: Optional[str] = None,
                         random_color_column: Optional[str] = None, **kwargs)
leafmap.deck.Map.add_geojson(self, filename: str,
                             layer_name: Optional[str] = None,
                             random_color_column: Optional[str] = None, **kwargs)
leafmap.deck.Map.to_html(self, filename=None, open_browser=False,
                         notebook_display=None, iframe_width='100%',
                         iframe_height=500, as_string=False, offline=False,
                         **kwargs)
```

`leafmap.kepler.Map` has no inspected `add_points_from_xy` method. The
PyDeck map has no inspected `to_streamlit` method; render it with
`st.pydeck_chart(map_object)`. If an optional backend import fails, report the
selected backend as unavailable instead of silently switching to Folium.

The package helper is at `leafmap.gdf_centroid(gdf, return_geom=False)` in the
inspected environment. It is not exposed as
`leafmap.foliumap.gdf_centroid`, `leafmap.kepler.gdf_centroid`, or
`leafmap.deck.gdf_centroid`.
