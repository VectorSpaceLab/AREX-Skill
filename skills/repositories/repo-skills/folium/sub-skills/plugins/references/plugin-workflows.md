# Plugin workflows

## 1) Cluster many points

Use `MarkerCluster` when you need Python-side marker children, individual popups, or later bounds checks.
Use `FastMarkerCluster` when the point count is large and the browser can build markers directly from rows.

```python
from folium import Map, plugins

m = Map(location=[40, -74], zoom_start=5)
cluster = plugins.MarkerCluster(
    locations=locations,
    popups=popups,
    icon_create_function="function(cluster) { return L.divIcon({html: cluster.getChildCount()}); }",
)
cluster.add_to(m)
```

Rules of thumb:

- Use `MarkerCluster` when the user needs `Marker` children, custom popups, or icon-specific Python control.
- Use `FastMarkerCluster` when the user says “many points” and does not need `get_bounds()` or per-marker Python children.
- For `FastMarkerCluster`, `callback` must return a Leaflet marker for one data row. Treat it as browser-side rendering, not a Python marker collection.
- For `HeatMap`, pass `[lat, lon]` or `[lat, lon, weight]`; clean NaNs first.
- For `HeatMapWithTime`, build `data` as a list of time slices, then attach an `index` list of labels with the same length.

## 2) Draw, edit, and search

Use `Draw` when the user wants ad hoc sketching and client-side export.
Use `GeoMan` when the task needs more advanced edit modes such as cut, rotate, or snapping.

```python
from folium import Map, FeatureGroup, plugins
from folium.utilities import JsCode

m = Map(location=[45, 3], zoom_start=4)
fg = FeatureGroup(name="editable").add_to(m)
plugins.Draw(
    export=True,
    feature_group=fg,
    filename="drawn.geojson",
    on={"click": JsCode("function(e) { console.log(this.toGeoJSON()); }")},
).add_to(m)
```

Search workflow:

- Use `Search(layer=...)` only with `GeoJson`, `TopoJson`, `FeatureGroup`, or `MarkerCluster`.
- For GeoJson and TopoJson, `search_label` must exist in the feature properties.
- For point searches, use `geom_type="Point"`; for polygons or lines, use the matching geometry type so the plugin zooms to bounds rather than a point marker.
- For `FeatureGroup` search, store the searchable label on the marker or feature metadata first.

Control workflow:

- `Fullscreen`, `MiniMap`, `MeasureControl`, `MousePosition`, `LocateControl`, `Geocoder`, and `ScrollZoomToggler` are usually one-line map additions.
- Use `JsCode` only for formatter or event hooks that need custom JavaScript.
- `LocateControl` requires a secure browser context for geolocation.

## 3) Organize or compare layers

Use `DualMap` when the user wants two synchronized maps in one page.
Use `SideBySideLayers` when the user wants a swipe comparison between exactly two layers.
Use `GroupedLayerControl`, `TreeLayerControl`, `FeatureGroupSubGroup`, or `TagFilterButton` when the user wants to manage many overlays.

```python
m = plugins.DualMap(location=[52.1, 5.1], layout="horizontal")
folium.TileLayer("openstreetmap").add_to(m.m1)
folium.TileLayer("cartodbpositron").add_to(m.m2)
```

Guidance:

- Put shared layers on the `DualMap` object itself; put map-specific layers on `m.m1` or `m.m2`.
- For `GroupedLayerControl`, supply `groups={"Group": [layer1, layer2]}` and set `exclusive_groups=False` only when multiple layers in the same group may be active.
- For `TreeLayerControl`, build nested dict/list trees with `children` and `layer` nodes.
- Use `FeatureGroupSubGroup` when you want a subgroup to inherit a parent `FeatureGroup` or `MarkerCluster`.
- Use `TagFilterButton` when the elements already carry `tags=[...]` values and the user wants tag-based filtering.

## 4) Animate past data or live data

Decision order:

1. If the feed is live, use `Realtime`.
2. If each feature has a start/end interval, use `Timeline` plus `TimelineSlider`.
3. If each feature has timestamp arrays for geometry points, use `TimestampedGeoJson`.
4. If the choropleth style is precomputed by feature id and timestamp, use `TimeSliderChoropleth`.
5. If the source is a time-enabled WMS layer, use `TimestampedWmsTileLayers`.

Callbacks and data shapes:

- Wrap complex time callbacks in `JsCode` when the plugin accepts JS hooks.
- `Realtime` can take a URL string, a dict for `fetch`, or a `JsCode` source.
- `TimeSliderChoropleth` expects `styledict[feature_id][timestamp] = {"color": ..., "opacity": ...}` and the ids must match the GeoJSON ids.
- `TimestampedGeoJson` is for historical data only; each feature needs a `times` list, and the list length must match the coordinates shape.
- `Timeline` is the better fit for interval data or when a `get_interval` hook can derive the interval from a feature.

## 5) Style paths, vectors, or a globe

Use the path/style plugins when the geometry already exists but needs visual treatment.

- `AntPath`: animated line motion.
- `PolyLineOffset`: parallel offset lines.
- `PolyLineTextPath`: text along an existing line.
- `SemiCircle`: directional sectors and arcs.
- `StripePattern` / `CirclePattern`: fill patterns for polygon styling.
- `PolyLineFromEncoded` / `PolygonFromEncoded`: build geometry from encoded strings.
- `VectorGridProtobuf`: render vector tiles and style each tile layer key separately.
- `WebGLEarth`: swap the flat map for a 3D globe; add markers, tiles, or realtime updates as children.

When in doubt, choose the simplest plugin that matches the user’s input model rather than reshaping the data aggressively in Python.

## Hard decision cases to remember

- For about 1000 points, choose `FastMarkerCluster` only if the user does not need Python-side child markers, later bounds, or per-point popup logic; otherwise keep `MarkerCluster`.
- For historical movement, choose `TimestampedGeoJson` when the geometry itself changes through time, `Timeline` when features carry intervals, and `Realtime` only when the source is live.
- For comparison tasks, choose `SideBySideLayers` when the user wants a swipe and `DualMap` when they want two fully synchronized map views.
