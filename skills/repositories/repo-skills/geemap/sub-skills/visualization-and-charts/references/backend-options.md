# Visualization backend options

Pick a backend by output target, dependency footprint, and credential needs. The minimum verified geemap skill environment covers CPU Python imports and safe local checks; remote Earth Engine, service tokens, and optional visualization extras remain runtime choices.

## Backend selection matrix

| Target | Prefer | Dependencies | Credentials/network | Fallback |
|---|---|---|---|---|
| Local dataframe chart in notebook or script | `geemap.plot` | base geemap includes pandas and Plotly | none for local DataFrame/CSV; network for URL CSV | plain pandas/matplotlib or `geemap.chart.Chart` |
| bqplot chart from arrays or small tables | `geemap.chart.Chart`, `array_values` | base geemap includes bqplot, pandas, matplotlib | none for local lists/DataFrames | `geemap.plot` Plotly Express wrappers |
| Chart from Earth Engine features/images | `geemap.chart.feature_*`, `image_*` | base geemap and Earth Engine API | Earth Engine auth, project, network; large `getInfo()` transfers can be slow | export/reduce data with [conversion and I/O](../../conversion-and-io/SKILL.md), then chart locally |
| Publication static map | `geemap.cartoee` | `cartopy`, matplotlib, pillow, requests, Earth Engine API | EE auth/network for image thumbnails; cartopy data may need network if coastlines/features are requested | use local colorbar/legend only, or an interactive map screenshot outside this sub-skill |
| Compact palette/colorbar/legend asset | `geemap.colormaps`, `geemap.create_colorbar`, `geemap.legends` | base geemap + matplotlib | none | manually build CSS/HTML legend from `builtin_legends` |
| Plotly map and heatmap | `geemap.plotlymap.Map` | base geemap includes Plotly; FigureWidget renderer may need notebook widget support | EE auth only for `add_ee_layer`; Mapbox token only for Mapbox styles | `geemap.plot` for non-map charts; [interactive maps](../../interactive-earth-engine-maps/SKILL.md) for ipyleaflet/folium |
| deck.gl map | `geemap.deck` | `pydeck`; install via geemap `backends` extra or `pip install pydeck` | EE auth only for EE layers; remote tile URLs need network | Plotly map or MapLibre map depending output target |
| kepler.gl dashboard | `geemap.kepler` | `keplergl`; vector methods may need GeoPandas | network for remote files; Streamlit for `to_streamlit` | Plotly map for simple heat/scatter; MapLibre for widget map |
| MapLibre GL widget/HTML | `geemap.maplibregl` | geemap `maplibre` extra: maplibre, ipyvuetify, geopandas, localtileserver, rioxarray, pmtiles, etc. | MapTiler key for MapTiler and 3D terrain styles; EE auth for EE layers | Carto styles (`dark-matter`, `positron`, `voyager`) or `demotiles`; Plotly/pydeck for simpler tile maps |

## Optional dependency recovery

Install only the backend needed for the task:

```bash
# Publication-quality static maps
pip install cartopy

# pydeck and kepler.gl backends
pip install "geemap[backends]"

# MapLibre backend and local raster/vector helpers
pip install "geemap[maplibre]"

# Individual packages when extras are not desired
pip install pydeck keplergl geopandas maplibre ipyvuetify
```

After installing notebook widget backends, restart the Python kernel before retesting if imports succeed but display is blank.

## Credential and token rules

- Earth Engine charts and EE tile/static map layers require an initialized EE session. Set project/auth at the root setup layer; this sub-skill only consumes initialized `ee` objects.
- `plotlymap.Map(..., ee_initialize=False)` and `deck.Map(..., ee_initialize=False)` are safe for local-only constructor checks.
- Mapbox styles in Plotly read `MAPBOX_TOKEN` when `access_token` is omitted.
- MapLibre MapTiler styles read `MAPTILER_KEY`; exported HTML can replace private keys with `MAPTILER_KEY_PUBLIC` when configured. 3D terrain styles (`style="3d-terrain"`, `maptiler_3d_style`) require a MapTiler key.
- Planet mosaic helpers in Plotly/pydeck map classes read `PLANET_API_KEY`; route data/API acquisition troubleshooting to [conversion and I/O](../../conversion-and-io/SKILL.md) unless the issue is only visual styling.

## Coordinate and constructor differences

| Class | Center order | No-auth constructor |
|---|---|---|
| `geemap.plotlymap.Map` | `(lat, lon)` | `Map(ee_initialize=False)` |
| `geemap.deck.Map` | `(lat, lon)` | `Map(ee_initialize=False)` |
| `geemap.kepler.Map` | list interpreted as `[lat, lon]` in its config | no EE initialization in constructor |
| `geemap.maplibregl.Map` | `(lon, lat)` | constructor does not initialize EE unless an EE method asks for it |

When porting a center between backends, rewrite coordinate order deliberately and verify the resulting viewport.

## Renderer/display guidance

- `geemap.chart` uses bqplot and ipywidgets; it is best in Jupyter-like contexts. For headless scripts, use the smoke script or Plotly figure export instead of relying on notebook display.
- `geemap.cartoee` uses matplotlib; set a non-interactive backend such as `Agg` for scripts and save with `cartoee.savefig`.
- `plotlymap.Map` is a `FigureWidget`; if widget display fails, try `fix_widget_error()` for the known `mapbox._derived` error, restart the kernel, or export a Plotly static image if Kaleido is installed.
- `kepler.Map.static_map` and `to_html` can create standalone outputs; `to_streamlit` requires Streamlit.
- `maplibregl.Map.to_html` renders an HTML page. Verify tokens before sharing HTML that references private tile services.

## Visual fallback strategy

If an optional backend is unavailable, preserve the analytical result and choose a lighter visualization:

1. Convert EE results to a bounded table or local raster/vector only if that is the user's goal; otherwise state the missing backend and credentials.
2. Use `geemap.colormaps.get_colorbar(..., return_fig=True)` to validate palettes independent of a map backend.
3. Use `geemap.plot` for tabular summaries.
4. Use [interactive Earth Engine maps](../../interactive-earth-engine-maps/SKILL.md) for ipyleaflet/folium maps when Plotly/pydeck/MapLibre is not required.
