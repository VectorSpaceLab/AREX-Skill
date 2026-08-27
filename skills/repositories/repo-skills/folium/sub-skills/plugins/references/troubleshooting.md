# Troubleshooting

## Start with the browser, not Python

Folium plugin rendering is browser-side.
A successful `render()` or `_repr_html_()` only proves that Folium serialized the plugin markup.
It does **not** prove that the browser fetched the JS/CSS assets, accepted the callback code, or drew the final control correctly.

If the map looks wrong, open the browser console and network panel first.
Check for:

- CDN fetch failures or blocked mixed-content requests
- CSP or ad-blocking issues
- JavaScript syntax errors inside custom callbacks
- browser features that are unavailable in the current context

## Data-shape problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Clustered markers do not appear | `MarkerCluster` locations are not pairs of `[lat, lon]` | Normalize the input to two numeric coordinates per marker. |
| `FastMarkerCluster` renders but later Python-side layer logic fails | It does not keep real Python marker children | Use `MarkerCluster` if you need child markers, later bounds, or per-point Python control. |
| Heat map throws NaN or serialization errors | A row contains NaNs or a non-numeric weight | Clean the data first; weights must be numeric and finite. |
| Time heat map has mismatched frames | Outer time-step list length does not match the index labels | Keep `data` and `index` the same length. |
| `TimeSliderChoropleth` shows wrong colors or no update | Feature ids do not match the GeoJSON ids, or the timestamp keys are inconsistent | Build `styledict` from the ids actually emitted in the GeoJSON and use consistent timestamp strings. |
| `TimestampedGeoJson` does not animate | Feature `times` arrays do not match the coordinate shape | Ensure each feature carries the correct `times` list for its geometry type. |
| `Timeline` renders but has no features | The features lack `start` / `end`, or `get_interval` returned nothing | Supply interval fields or a valid `JsCode` interval extractor. |
| `Search` does nothing | Wrong layer type or missing property name | Restrict search to supported layer classes and make sure `search_label` exists. |

## Callback and JavaScript issues

Use raw JavaScript strings when the plugin expects a function body directly.
Use `JsCode` when the API is designed to accept injected JavaScript objects or when the callback should stay clearly marked as JS.

Common mistakes:

- passing a Python lambda where the plugin expects browser JavaScript
- wrapping a function twice so the output becomes invalid JS
- forgetting to return a Leaflet marker from `FastMarkerCluster.callback`
- forgetting that `Realtime` / `WebGLEarthRealtime` callbacks run in the browser, not in Python

Typical hook names to review carefully:

- `MarkerCluster.icon_create_function`
- `FastMarkerCluster.callback`
- `Draw.on`
- `GeoMan.on`
- `Timeline.get_interval`
- `Realtime.get_feature_id` and `Realtime.update_feature`
- `WebGLEarthRealtime.on_update`

## Browser-only or CDN-limited behavior

| Plugin family | What to check |
| --- | --- |
| Controls like `Fullscreen`, `MiniMap`, `MeasureControl`, `MousePosition`, `LocateControl`, `Geocoder`, `ScrollZoomToggler` | The JS/CSS assets loaded successfully and the browser did not block the control. |
| `LocateControl` | The page must be served over HTTPS or another secure context for geolocation. |
| `Geocoder` | Provider-specific options may require an API key or a custom provider object. |
| `Draw` | The export link is a client-side download; it will not create a server file automatically. |
| `Realtime` and `WebGLEarthRealtime` | The browser fetches remote data, so CORS, HTTPS, and mixed-content rules apply. |
| `WebGLEarth` | The browser must support WebGL, and the globe is not a normal Leaflet map. |

## Export, network, and client-side behavior

- `Draw(export=True)` creates a browser download link. If you need a server file, capture the exported GeoJSON in a separate workflow.
- `MiniMap`, `Geocoder`, `LocateControl`, and other controls may still depend on tile or API requests that happen in the browser after the HTML file opens.
- `VectorGridProtobuf` can fail quietly if the vector-tile URL template or token placeholders are wrong. Check the rendered JS and the browser network log.
- `TimestampedWmsTileLayers` depends on time-capable WMS responses; a valid layer without time metadata will not animate as expected.

## Fast fallback strategy

1. Strip the example down to one plugin.
2. Replace custom callbacks with a minimal JS function.
3. Confirm the generated HTML contains the expected CDN asset tags.
4. Open the file in a browser and inspect the console/network panel.
5. Add the extra styling or controls back only after the minimal case works.

## High-value checks for this family

- `MarkerCluster` vs `FastMarkerCluster`: choose the latter only when speed matters more than Python-side marker ownership.
- `TimestampedGeoJson` vs `Timeline` vs `Realtime`: historical geometry changes, interval data, and live feeds are three different input models.
- `DualMap` vs `SideBySideLayers`: synchronized maps versus a single swipe comparison.
