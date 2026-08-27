# Visualization troubleshooting

## Cartoee and cartopy failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `cartopy not available` printed during import | `cartopy` optional dependency is missing | Install cartopy, restart the kernel, and retry `geemap.cartoee`. Palette helpers can still be used without cartopy. |
| `NameError` or undefined cartopy classes when calling `add_colorbar`/`add_gridlines` | `geemap.cartoee` imported after missing cartopy, leaving cartopy symbols unavailable | Fix cartopy installation, restart the Python process, then re-import. |
| Blank or wrong static EE image | Region omitted or coordinate order/extent is wrong; EE thumbnail default region is not suitable | Pass a bounded `region`; start with a known rectangle and verify the viewport visually. If using an RGB visualization, source code warns to specify `region` when blank. |
| `KeyError` about `palette` with `cmap` | `cartoee.add_layer` was given both `cmap` and `vis_params['palette']` | Choose one: either `cmap='viridis'` or `vis_params={'palette': [...]}`. |
| HTTP error from thumbnail request | Earth Engine auth/network/project problem, invalid visualization parameters, or inaccessible asset | Confirm EE initialization and asset access; reduce region/dimensions; validate `min`, `max`, bands, and palette. |

## Colorbar and legend validation

| Symptom | Likely cause | Recovery |
|---|---|---|
| `loc or cax keywords must be specified` in `cartoee.add_colorbar` | No colorbar placement was supplied | Pass `loc='right'`, `left`, `bottom`, or `top`, or create and pass a matplotlib `cax`. |
| `Provided loc not of type str` or invalid location | `loc` is not one of cartoee's allowed strings | Use only `left`, `right`, `bottom`, or `top` for cartoee. MapLibre positions are `top-left`, `top-right`, `bottom-left`, `bottom-right`. |
| `Provided min/max value not of scalar type` | `vis_params['min']` or `vis_params['max']` is a list/string/dict | Use numeric scalar `min` and `max`; for multi-band visualization, still supply scalar display range or handle bands separately. |
| `Provided opacity value of not type scalar` or invisible layer | Opacity is non-numeric or outside expected 0-1 range | Use a numeric opacity between 0 and 1 for map layers. |
| Matplotlib error about colorbar orientation | Orientation is not `horizontal` or `vertical` | Validate orientation before calling `colormaps.get_colorbar`, `plot_colormap`, or MapLibre `add_colorbar`. |
| Legend silently does not render in MapLibre | Labels/colors are not lists, lengths differ, position invalid, or built-in name not found | Use `legend_dict={label: color}` or same-length `labels`/`colors`; check built-in keys exactly; use a corner position string. |
| Color strings render incorrectly | Mixed `RRGGBB`, `#RRGGBB`, RGB tuples, or invalid color names | Normalize with `colormaps.get_palette(..., hashtag=True)` or convert RGB tuples to hex before passing to widgets. |
| `AttributeError: module 'matplotlib.cm' has no attribute 'get_cmap'` after an invalid colormap name | A newer matplotlib version removed a fallback path that geemap's invalid-name branch tries after `plt.get_cmap` rejects the name | Treat this as an invalid colormap or upstream compatibility issue: choose a valid matplotlib colormap, pin/use a compatible matplotlib if necessary, and avoid relying on invalid-name exceptions for control flow. |

## Chart failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Column '<name>' not found in DataFrame` from `transpose_df` | Wrong label column | Inspect `df.columns` and pass an existing column. |
| `Length of custom indexes must match...` | Custom index labels do not match transposed rows | Provide one index label per transposed row or omit `indexes`. |
| `The length of y_labels must match...` | `array_to_df` labels do not match y-series count | Count the top-level y-series after axis handling; adjust `y_labels`. |
| `features must be an ee.FeatureCollection` | Feature chart received a local dataframe or wrong EE object | Use `chart.Chart`/`geemap.plot` for local data, or cast valid EE features with `ee.FeatureCollection(...)`. |
| `property <name> not found` in feature histogram | Histogram property missing from first feature | Check property names, select/rename properties, or choose an existing numeric property. |
| EE chart hangs or fails with quota/network errors | Large unfiltered collection, missing auth/project, or remote reduction too expensive | Filter/limit the collection, simplify region, set scale, authenticate EE, or export a bounded table via [conversion and I/O](../../conversion-and-io/SKILL.md). |
| Image chart returns empty/incorrect values | Missing region, inappropriate reducer, wrong scale, masked pixels, or wrong band/class names | Specify a bounded `region`, reducer, scale, selected band, and class labels; unmask or filter data when appropriate. |

## Plotly and Plotly map issues

| Symptom | Likely cause | Recovery |
|---|---|---|
| `data must be a pandas DataFrame...` from `geemap.plot` | Input was not a DataFrame or CSV path/URL | Convert to DataFrame first or pass a readable CSV file/URL. |
| Plotly FigureWidget `mapbox._derived` error | Known Plotly FigureWidget issue | Run `geemap.plotlymap.fix_widget_error()` only for this specific error, then restart if needed. |
| `Controls must be a string or a list of strings` | Wrong control argument type | Pass one modebar control string or a list of strings. |
| `Basemap ... not found` | Basemap name is not in Plotly basemap dictionary | Inspect available keys or use built-in Plotly styles such as `open-street-map`, `carto-positron`, or route base map work to [interactive maps](../../interactive-earth-engine-maps/SKILL.md). |
| `The image argument in 'addLayer'...` | `add_ee_layer` received a non-EE object | Pass an `ee.Image`, `ee.ImageCollection`, `ee.Feature`, `ee.FeatureCollection`, or `ee.Geometry`; use `add_tile_layer` for raw tile URLs. |
| `The palette must be a list...` | Palette is not list, string colormap name, tuple, or Box default palette | Convert palette with `colormaps.get_palette` or pass a valid matplotlib colormap string. |
| Heatmap input error | `add_heatmap` received neither DataFrame nor CSV path, or column names are wrong | Pass DataFrame/CSV with latitude, longitude, and value columns or override column names. |

## Missing optional backends

| Missing import | Needed for | Recovery |
|---|---|---|
| `pydeck` | `geemap.deck` | Install `geemap[backends]` or `pydeck`. Use Plotly map as a fallback. |
| `keplergl` | `geemap.kepler` | Install `geemap[backends]` or `keplergl`; restart notebook widget kernel. |
| `geopandas` | GeoDataFrame/vector methods in Plotly, pydeck, kepler, MapLibre | Install vector/maplibre extras; verify native GEOS/GDAL wheels are available for the platform. |
| `maplibre`, `ipyvuetify`, `pmtiles`, `localtileserver`, or raster dependencies | `geemap.maplibregl` and local raster/PMTiles workflows | Install `geemap[maplibre]`; if only a simple map is needed, use Plotly or interactive ipyleaflet/folium instead. |
| Streamlit integration | `to_streamlit` methods | Install Streamlit or choose HTML/notebook output. |

## MapTiler and style/token problems

| Symptom | Likely cause | Recovery |
|---|---|---|
| MapLibre falls back to `dark-matter` | Requested MapTiler style lookup failed | Check style name, network, and `MAPTILER_KEY`; use Carto styles (`dark-matter`, `positron`, `voyager`) or `demotiles` without a private key. |
| 3D terrain/buildings do not load | `style='3d-*'` or `add_3d_buildings` needs MapTiler tiles and a key | Set `MAPTILER_KEY` or pass `api_key`; verify the key has access to terrain/vector tiles. |
| Shared HTML exposes or loses private key | HTML export key replacement not configured | Use public key replacement only when intended; verify `MAPTILER_KEY_PUBLIC` and `MAPTILER_REPLACE_KEY` behavior before sharing. |
| Mapbox Plotly style is blank | Missing `MAPBOX_TOKEN` or invalid style | Pass `access_token=` explicitly or set `MAPBOX_TOKEN`; use token-free Plotly styles for fallback. |

## Headless and CI-safe checks

Use the bundled smoke script for deterministic checks that do not require EE credentials:

```bash
python sub-skills/visualization-and-charts/scripts/visualization_smoke.py
python sub-skills/visualization-and-charts/scripts/visualization_smoke.py --check-optional-backends
```

The default run checks pandas/chart helpers, palettes, matplotlib colorbars, and cartoee palette generation. Optional backend checks report missing extras without failing unless `--require-optional-backends` is used.
