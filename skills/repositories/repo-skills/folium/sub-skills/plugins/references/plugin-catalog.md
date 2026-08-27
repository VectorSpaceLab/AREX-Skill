# Plugin catalog

This catalog is grouped by user task so you can choose a plugin family without starting from a raw import dump.

## Cluster or smooth point density

| User goal | Best fit | Input shape | Why this fit |
| --- | --- | --- | --- |
| Cluster a moderate number of markers with popups or custom icons | `MarkerCluster` | `locations=[(lat, lon), ...]`, optional `popups` and `icons` lists of the same length | Keeps Python-side marker children, so each point can still have its own popup or icon. |
| Render a large point cloud quickly in the browser | `FastMarkerCluster` | `data=[[lat, lon, ...], ...]` plus a JS `callback(row)` | Faster for thousands of points, but no retained child markers and no `get_bounds()`. |
| Show density from weighted points | `HeatMap` | `[[lat, lon], ...]` or `[[lat, lon, weight], ...]` | Lightweight point-density overlay; weights are converted to floats and NaNs are rejected. |
| Animate density across time slices | `HeatMapWithTime` | outer list by time step; each inner point row is `[lat, lon]` or `[lat, lon, weight]`; optional `index` labels | Good when the same point cloud changes over time and you want a time slider. |

Preferred imports:

```python
from folium import plugins
from folium.plugins import MarkerCluster, FastMarkerCluster, HeatMap, HeatMapWithTime
```

## Add controls or browser interaction

| User goal | Best fit | Input shape | Notes |
| --- | --- | --- | --- |
| Let the user draw and export shapes | `Draw` | optional `feature_group`, `draw_options`, `edit_options`, and `on` event map | Export is client-side; the button writes a browser download. |
| Use advanced edit/cut/rotate/snap tools | `GeoMan` | optional `feature_group` and `on` event map | Better for richer editing than `Draw`. |
| Search markers or features | `Search` | a `GeoJson`, `TopoJson`, `FeatureGroup`, or `MarkerCluster` layer | `search_label` must match a property key for GeoJson/TopoJson. |
| Add fullscreen, minimap, measure, coordinates, locate, geocoder, or scroll toggle UI | `Fullscreen`, `MiniMap`, `MeasureControl`, `MousePosition`, `LocateControl`, `Geocoder`, `ScrollZoomToggler` | usually no extra data | These are map controls rather than data layers. `LocateControl` needs HTTPS in real browsers. |

## Compare or organize layers

| User goal | Best fit | Input shape | Notes |
| --- | --- | --- | --- |
| Show two synchronized maps | `DualMap` | same `Map` kwargs, plus `layout="horizontal"` or `"vertical"` | Add shared layers to `m`, map-specific layers to `m.m1` or `m.m2`. |
| Compare two overlays with a swipe | `SideBySideLayers` | `layer_left`, `layer_right` | Both layers must already exist on the map. |
| Group overlay toggles | `GroupedLayerControl` | `groups={group_name: [layer, ...]}` | Use `exclusive_groups=False` for checkboxes instead of radio buttons. |
| Build a nested layer tree | `TreeLayerControl` | nested `base_tree` / `overlay_tree` dicts and lists | Good for large layer sets with hierarchy. |
| Nest sublayers under a parent cluster or feature group | `FeatureGroupSubGroup` | parent `group` plus subgroup layers | Useful for clustered overlays or nested organization. |
| Filter layers by tags | `TagFilterButton` | `data=["tag1", "tag2", ...]` and tagged markers/features | Works well when elements already carry tag lists. |

## Show time or live dynamics

| User goal | Best fit | Input shape | Notes |
| --- | --- | --- | --- |
| Show past time-stamped geometries | `TimestampedGeoJson` | GeoJSON features with `properties.times` arrays | Works with LineString, MultiPoint, MultiLineString, Polygon, MultiPolygon, and single-point features. |
| Show interval-based features with a slider | `Timeline` + `TimelineSlider` | GeoJSON features with `start` / `end`, or a `get_interval` JS hook | Use `TimelineSlider` when you need playback controls. |
| Show a precomputed choropleth by timestamp | `TimeSliderChoropleth` | serialized GeoJSON + `styledict[feature_id][timestamp] = {color, opacity}` | Feature ids must match the GeoJSON ids. |
| Refresh live data from an API | `Realtime` | `source` as URL, dict, or JS code | Best for live tracking and sensor feeds; supports feature-id and update hooks. |
| Time-enable WMS layers | `TimestampedWmsTileLayers` | one or more `WmsTileLayer` objects | Good for server-side raster time dimensions. |

## Style paths, encoded geometry, or advanced rendering

| User goal | Best fit | Input shape | Notes |
| --- | --- | --- | --- |
| Animate a line with a moving dash effect | `AntPath` | line coordinates | Uses a path overlay with animated motion. |
| Offset a polyline without changing its coordinates | `PolyLineOffset` | line coordinates and `offset` | Good for parallel routes or lane-like overlays. |
| Put text along a line | `PolyLineTextPath` | existing `PolyLine` plus text | Attach after the line exists. |
| Draw semicircle sectors | `SemiCircle` | location, radius, and either `direction`/`arc` or `start_angle`/`stop_angle` | Use one angle style or the other, not both. |
| Fill polygons with stripes or circles | `StripePattern`, `CirclePattern` | style parameters only | Often referenced from GeoJson style functions through `fillPattern`. |
| Build geometries from encoded polylines/polygons | `PolyLineFromEncoded`, `PolygonFromEncoded` | encoded polyline string | Useful when the upstream service already provides encoded geometry. |
| Render vector tiles | `VectorGridProtobuf` | tile URL plus `options` | `options` may be a dict or a JS string; `vectorTileLayerStyles` styles each tile layer key separately. |
| Replace the flat map with a 3D globe | `WebGLEarth`, `WebGLEarthMarker`, `WebGLEarthTileLayer`, `WebGLEarthRealtime` | globe center/zoom plus markers, tiles, or live hooks | Use when the user explicitly wants a browser-side globe instead of a Leaflet map. |
