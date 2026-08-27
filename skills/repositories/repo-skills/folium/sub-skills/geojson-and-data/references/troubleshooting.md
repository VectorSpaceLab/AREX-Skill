# Troubleshooting

## Identifier and `key_on`

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `key_on` not found | The join path is wrong or the feature ids do not match the table keys | Use `feature.id` or a real property path such as `feature.properties.name`; keep the table key column unique and stable |
| GeoJson styling fails when `embed=False` | There is no stable feature identifier and the layer cannot be mutated in place | Embed the data, add explicit feature ids, or use a property that is already unique |
| Choropleth colors every feature with the missing-value color | The key column and `key_on` do not match | Compare a few feature ids against the table keys and make the join column explicit |

## Columns, bins, and colors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| DataFrame binding raises a column error | `columns` is missing or points at the wrong fields | For DataFrame input, pass `[key_column, value_column]` in the correct order |
| `bins` error or empty legend | The bin edges do not cover the data range | Expand the bin list or use an integer bin count that spans the values |
| `use_jenks=True` fails | `jenkspy` is not installed or `bins` is not an integer | Install the optional dependency or switch back to explicit bins |
| All missing values share the same color | That is the configured `nan_fill_color` behavior | Pick a deliberate `nan_fill_color` / `nan_fill_opacity` combination that matches the story |
| Legend looks wrong | `fill_color` is not a valid ColorBrewer palette for bound data | Use a palette such as `YlGn`, `BuPu`, or `RdYlBu` |

## CRS and coordinate order

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Shapes appear on the wrong continent | GeoJSON coordinates were supplied as `[lat, lon]` instead of `[lon, lat]` | Swap the order and re-check with `ClickForLatLng` |
| GeoDataFrame looks offset after rendering | The GeoDataFrame CRS is not EPSG:4326 | Reproject upstream or rely on the `to_crs` path when available |
| Map center and feature geometry disagree | Folium map locations use `[lat, lon]` but GeoJSON uses `[lon, lat]` | Treat the map center and geometry data as different coordinate conventions |
| TopoJSON renders incorrectly | The `object_path` does not point at the intended object | Confirm the object path before rendering; it must match the topology structure |

## Tooltip and popup fields

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Tooltip or popup fails to render | The field is absent from the feature properties | Use exact property names and keep the property set consistent across features |
| `fields` and `aliases` mismatch | The label lists are different lengths | Give them the same length and order |
| GeometryCollection warnings appear | The layer contains geometry types that the standard tooltip/popup path does not handle well | Convert to MultiPolygon where possible or switch to `on_each_feature` for custom handling |
| Labels look cluttered | `labels=True` with long aliases | Turn labels off or shorten aliases |

## Style callbacks

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `style_function` raises a type error | The callback did not return a dictionary | Return a plain style dict with Leaflet-compatible keys |
| Every layer gets the same style in a loop | Late-binding closure captured the last loop value | Bind the loop variable early with `lambda feature, style=style: style` |
| Marker styling does nothing | The point layer is not using a supported marker class | Use `Marker`, `Circle`, or `CircleMarker` for `GeoJson.marker` |
| `popup_keep_highlighted` errors | A popup is required for that feature | Provide a popup and a highlight function together |

## Network and embed issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Remote GeoJSON does not load | The URL is unavailable or the environment is offline | Use a local file or embedded GeoJSON for the final skill |
| Styling remote data fails with `embed=False` | The layer is not a FeatureCollection that can be mutated locally | Keep styling on embedded FeatureCollections or pre-structure the data appropriately |
| Rendering is slow | The data are large and over-detailed | Simplify upstream or use a lighter geometry source before rendering |

## Quick recovery checks

1. Verify the coordinate order on one known point.
2. Print or inspect a sample feature id and a sample table key.
3. Confirm the tooltip and popup field names exist in the first feature's properties.
4. Check the color scale and missing-value styling on a tiny embedded example before trying the full dataset.
