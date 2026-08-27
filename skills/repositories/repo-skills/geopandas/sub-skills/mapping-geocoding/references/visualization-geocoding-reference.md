# Visualization and Geocoding Reference

Read this for GeoPandas plotting, interactive mapping, and geocoding API guidance.

## Static Plotting

| API | Use | Optional dependency |
|---|---|---|
| `GeoSeries.plot` | Plot geometries as a matplotlib layer. | `matplotlib` |
| `GeoDataFrame.plot` | Plot active geometry with optional column-based styling and legends. | `matplotlib` |
| `geopandas.plotting.plot_series` / `plot_dataframe` | Lower-level functions behind the accessors. | `matplotlib` |

Common parameters include `column`, `cmap`, `color`, `legend`, `ax`, `figsize`, `markersize`, `categorical`, `scheme`, and classification/legend kwargs. Classification schemes require `mapclassify`.

## Interactive Maps

| API | Use | Optional dependency |
|---|---|---|
| `GeoDataFrame.explore` / `GeoSeries.explore` | Build folium/Leaflet-style interactive maps. | `folium`, `branca`; classification may require `mapclassify` |
| Tile provider support | Add basemaps or tile layers. | `xyzservices`, sometimes `contextily` depending on workflow |

For interactive maps:

- Keep data small enough for browser rendering; simplify or sample when needed.
- Use a CRS suitable for web display or let the map workflow transform as documented by the API.
- Decide whether output should be an in-memory map object or an HTML file saved by folium.

## Geocoding APIs

| API | Verified signature | Notes |
|---|---|---|
| `geopandas.tools.geocode` | `geocode(strings, provider=None, **kwargs)` | Converts address strings to a GeoDataFrame of point geometries and address strings. Defaults to a Photon provider when provider is omitted. |
| `geopandas.tools.reverse_geocode` | `reverse_geocode(points, provider=None, **kwargs)` | Converts Shapely points to address records. Points use x=longitude, y=latitude. |

Geocoding requires `geopy`. Provider can be a geopy service string or geocoder class. Provider-specific kwargs may include `timeout`, `user_agent`, API keys, country/domain filters, or rate-limit relevant settings.

GeoPandas prepares geocoding results with CRS `EPSG:4326` when CRS support is available. Returned point coordinates are longitude/latitude.

## Optional Dependency Checks

Run:

```bash
python scripts/check_mapping_optional_deps.py --json
```

Use `--require matplotlib folium mapclassify` or `--require geopy` only when the task must run that optional workflow now.

## No-network Geocoding Check

Run:

```bash
python scripts/mock_geocode_smoke.py --json
```

This validates result shape and CRS through monkeypatched provider behavior, not a real external service. It is safe for tests and CI-like checks.
