# Data formats and input contracts

This sub-skill works with four related surfaces:

- `GeoJson` for GeoJSON features or feature collections
- `TopoJson` for TopoJSON objects
- `Choropleth` for binding table data to features
- `GeoJsonTooltip` / `GeoJsonPopup` for feature property display

## Accepted input forms

### GeoJson

`GeoJson` accepts:

- a dict-like GeoJSON object
- a JSON string containing GeoJSON
- a local file path
- a URL string
- any object exposing `__geo_interface__`

If the object also exposes `to_crs`, Folium reprojects it to `EPSG:4326` before rendering.

If `embed=False`, the input must be a URL or file path. Styling and highlighting also require a FeatureCollection so the layer can be assigned stable feature identifiers.

### TopoJson

`TopoJson` accepts a dict, JSON string, file path, or already-open file object together with an `object_path` such as `objects.counties`.

### Choropleth

`Choropleth` accepts `geo_data` plus optional table data:

- `data`: DataFrame, Series, or dict-like values
- `columns`: required for DataFrame input; the first column is the key and the second is the value
- `key_on`: the GeoJSON/TopoJSON lookup path, such as `feature.id` or `feature.properties.name`
- `bins`: integer count or explicit bin edges

## Coordinate order

Folium uses two coordinate conventions:

- map locations and marker inputs: `[lat, lon]`
- GeoJSON coordinates: `[lon, lat]`

GeoPandas geometries already follow the GeoJSON convention when they are serialized through `__geo_interface__`. If a GeoDataFrame exposes `to_crs`, Folium reprojects it to `EPSG:4326` before serialization.

When point features look misplaced, the fastest diagnosis is usually to compare the map click location from `ClickForLatLng` with the geometry coordinates you supplied.

## Feature identifiers and joins

`GeoJson` needs a unique identifier when styling or highlighting.

The runtime logic prefers, in order:

1. a unique `feature.id`
2. a unique string or integer property key
3. a generated `id` field when the data are embedded

If the layer is not embedded and no stable identifier exists, the render should fail fast rather than inventing a join key.

`Choropleth` resolves `key_on` against feature data using dot-path lookups. The usual safe choices are:

- `feature.id`
- `feature.properties.<field>`

For nested data, keep the lookup path simple and stable.

## Styling and callbacks

- `style_function` and `highlight_function` must return dictionaries.
- Loop-generated style functions should capture loop variables early with a default argument to avoid late binding.
- `JsCode` is the correct wrapper for `GeoJson.on_each_feature` JavaScript callbacks.
- For point features, `GeoJson.marker` accepts `Marker`, `Circle`, or `CircleMarker` objects only.

## Color scales

`Choropleth` builds a `StepColormap` and stores it on `color_scale`.

Important behavior:

- `fill_color` should be a valid ColorBrewer palette when values are bound
- `legend_name` becomes the legend caption
- `nan_fill_color` and `nan_fill_opacity` control missing or unmatched values
- `use_jenks=True` requires the optional `jenkspy` package and an integer `bins` value

## Validation checklist

Before handing a layer off, confirm:

- the input surface matches the chosen class
- the key path resolves on at least one feature
- tooltip and popup field names exist in the feature properties
- the coordinates are in the right order
- the bins cover the data range
- missing values have an explicit style decision
