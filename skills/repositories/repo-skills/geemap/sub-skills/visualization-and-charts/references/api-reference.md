# Visualization API reference

Signatures below are distilled from installed package inspection and source-level API contracts. Use them as call-shape guidance; still validate optional imports and Earth Engine authentication at runtime.

## `geemap.chart`

### Installed-inspected public chart functions

| API | Signature | Purpose and constraints |
|---|---|---|
| `feature_by_feature` | `(features: ee.featurecollection.FeatureCollection, x_property: str, y_properties: list[str], **kwargs: Any) -> None` | Plot one or more properties for each feature. Requires `ee.FeatureCollection` and named properties. |
| `feature_histogram` | `(features: ee.featurecollection.FeatureCollection, property: str, max_buckets: int | None = None, min_bucket_width: float | None = None, show: bool = True, **kwargs: Any) -> typing.Any | None` | Feature-property histogram. Validates collection type and property existence; `show=False` returns the chart object. |
| `image_by_region` | `(image: ee.image.Image, regions: ee.featurecollection.FeatureCollection | ee.geometry.Geometry, reducer: str | ee.reducer.Reducer, scale: int, x_property: str, **kwargs: Any) -> None` | Reduce an image over one or more regions. Requires reducer, scale, and x-property. |
| `image_series` | `(image_collection: ee.imagecollection.ImageCollection, region: ee.geometry.Geometry | ee.featurecollection.FeatureCollection, reducer: str | ee.reducer.Reducer | None = None, scale: int | None = None, x_property: str = 'system:time_start', chart_type: str = 'LineChart', x_cols: list[str] | None = None, y_cols: list[str] | None = None, colors: list[str] | None = None, title: str | None = None, x_label: str | None = None, y_label: str | None = None, **kwargs: Any) -> geemap.chart.Chart` | Time series over a region. Defaults x-axis to image time; set reducer and scale explicitly for reproducibility. |
| `array_values` | `(array: ee.ee_array.Array | ee.ee_list.List | list[list[float]], x_labels: ee.ee_array.Array | ee.ee_list.List | list[float] | None = None, axis: int = 1, series_names: list[str] | None = None, chart_type: str = 'LineChart', colors: list[str] | None = None, title: str | None = None, x_label: str | None = None, y_label: str | None = None, **kwargs: Any) -> geemap.chart.Chart` | Convert a local/EE array to a `Chart`. Use local lists for no-auth smoke tests. |

### Additional source-backed chart helpers

| API | Signature | Notes |
|---|---|---|
| `DataTable` | `(data: dict[str, list[Any]] | pd.DataFrame | None = None, date_column: str | None = None, date_format: str | None = None, **kwargs)` | Pandas-backed table; converts a named date column with `pd.to_datetime`. |
| `transpose_df` | `(df: pd.DataFrame, label_col: str, index_name: str | None = None, indexes: list | None = None) -> pd.DataFrame` | Raises `ValueError` if `label_col` is missing or custom index length is wrong. |
| `pivot_df` | `(df: pd.DataFrame, index: str, columns: str, values: str) -> pd.DataFrame` | Wide pivot with reset index. |
| `array_to_df` | `(y_values, x_values=None, y_labels=None, x_label='x', axis=1, **kwargs) -> pd.DataFrame` | Raises `ValueError` when `y_labels` count does not match the number of y-series. |
| `Chart` | `(data_table, chart_type='LineChart', x_cols=None, y_cols=None, colors=None, title=None, x_label=None, y_label=None, **kwargs)` | bqplot wrapper. Types include scatter, line, column, bar, pie, area, interval, and table. |
| `feature_by_property` | `(features, x_properties, series_property, **kwargs) -> None` | `x_properties` must be list or dict. |
| `feature_groups` | `(features, x_property, y_property, series_property, **kwargs) -> None` | Grouped or stacked feature charts. |
| `image_by_class` | `(image, class_band, region, reducer='MEAN', scale=None, class_labels=None, x_labels=None, chart_type='LineChart', **kwargs)` | Uses zonal statistics by class. |
| `image_histogram` | `(image, region, scale, max_buckets, min_bucket_width, max_raw, max_pixels, reducer_args={}, **kwargs)` | Strict region/scale/histogram limits; set pixel limits deliberately. |
| `image_series_by_region` | `(image_collection, regions, reducer=None, band=None, scale=None, x_property='system:time_start', series_property='system:index', chart_type='LineChart', ...)` | Multiple region time series. |

## `geemap.cartoee`

### Installed-inspected static map functions

| API | Signature | Purpose and constraints |
|---|---|---|
| `get_map` | `(ee_object, proj=None, basemap: str | None = None, zoom_level: int = 2, **kwargs)` | Create a cartopy axes and add an EE layer. Defaults projection to `PlateCarree`. |
| `add_layer` | `(ax, ee_object, dims=1000, region=None, cmap: str | None = None, vis_params=None, **kwargs)` | Add EE image/features to cartopy axes. `dims` must be list, tuple, or int; `ax` must be cartopy GeoAxes; do not combine `cmap` with `vis_params['palette']`. |
| `add_colorbar` | `(ax, vis_params: dict, loc: str | None = None, cmap: str = 'gray', discrete: bool = False, label=None, **kwargs)` | Adds matplotlib colorbar. Requires `loc` or `cax`, scalar `min`/`max`, and a `palette` or `cmap`. |
| `add_gridlines` | `(ax, interval: float | list[float] | None = None, n_ticks: int | list[int] | None = None, xs: list[float] | None = None, ys: list[float] | None = None, buffer_out: bool = True, xtick_rotation: float | str = 'horizontal', ytick_rotation: float | str = 'horizontal', **kwargs)` | Gridline ticks; provide one of interval, tick counts, or explicit `xs`/`ys`. |
| `add_scale_bar` | `(ax, metric_distance: float = 4, unit: str = 'km', at_x: tuple[float, float] = (0.05, 0.5), at_y: tuple[float, float] = (0.08, 0.11), max_stripes: int = 5, ytick_label_margins: float = 0.25, fontsize: int = 8, font_weight: str = 'bold', rotation: int = 0, zorder: float = 999, paddings: dict[str, float] | None = None, bbox_kwargs: dict[str, typing.Any] | None = None)` | Detailed scale bar. `add_scale_bar_lite` is often simpler for quick figures. |
| `add_legend` | `(ax, legend_elements=None, loc: str = 'lower right', font_size: int | str = 14, font_weight: int | str = 'normal', font_color: str = 'black', font_family: str | None = None, title=None, title_fontize=16, title_fontproperties=None, **kwargs) -> None` | Matplotlib legend from `Line2D`-style elements. |
| `savefig` | `(fig, fname: str, dpi: int | str = 'figure', bbox_inches: str = 'tight', **kwargs) -> None` | Wrapper over `matplotlib.pyplot.savefig`. |

### Additional cartoee helpers

| API | Signature | Notes |
|---|---|---|
| `build_palette` | `(cmap: str, n: int = 256) -> list[str]` | Matplotlib colormap to `#RRGGBB` palette. |
| `bbox_to_extent` | `(bbox: list[float] | tuple[float, float, float, float]) -> tuple` | Reorders `[W, S, E, N]`-like bbox to a matplotlib extent. |
| `pad_view` | `(ax, factor: float | list[float] = 0.05)` | Adds margins around the current extent. |
| `add_north_arrow` | `(ax, text='N', xy=(0.1, 0.1), arrow_length=0.1, ...)` | Annotation helper. |
| `add_scale_bar_lite` | `(ax, length=None, xy=(0.5, 0.05), linewidth=3, fontsize=20, color='black', unit='km', ha='center', va='bottom')` | Lightweight scale bar. |
| `create_legend` | `(linewidth=None, linestyle=None, color=None, marker=None, ..., **kwargs)` | Creates a matplotlib `Line2D`; requires linewidth or marker. |
| `get_image_collection_gif` | `(ee_ic, out_dir, out_gif, vis_params, region, ..., **kwargs)` | Animation-like workflow; route most GIF/video tasks to [timelapse and apps](../../timelapse-and-apps/SKILL.md). |

## Colorbars, colormaps, and legends

| API | Signature | Notes |
|---|---|---|
| `geemap.create_colorbar` | `(width=150, height=30, palette: list[int | str] | None = None, add_ticks=True, add_labels=True, labels=None, vertical=False, out_file=None, font_type='arial.ttf', font_size=12, font_color='black', add_outline=True, outline_color='black')` | Top-level helper for compact colorbar images. |
| `colormaps.get_palette` | `(cmap_name: str | None = None, n_class: int | None = None, hashtag: bool = False)` | Extra palettes: `ndvi`, `ndwi`, `dem`, `dw`, `esri_lulc`; otherwise matplotlib colormap lookup. |
| `colormaps.get_colorbar` | `(colors: list[str], vmin: float = 0, vmax: float = 1, width: float = 6.0, height: float = 0.4, orientation: str = 'horizontal', discrete: bool = False, return_fig: bool = False)` | Local matplotlib colorbar; returns figure when `return_fig=True`. |
| `colormaps.list_colormaps` | `(add_extra: bool = False, lowercase: bool = False) -> list[str]` | Matplotlib colormap list plus optional extra names. |
| `colormaps.plot_colormap` | `(cmap: str, width: float = 8.0, height: float = 0.4, orientation: str = 'horizontal', vmin: float = 0, vmax: float = 1.0, axis_off: bool = True, show_name: bool = False, font_size: int = 12, return_fig: bool = False)` | Plot one colormap. |
| `colormaps.plot_colormaps` | `(width: float = 8.0, height: float = 0.4) -> None` | Plot all available colormaps. |
| `colormaps.get_palettes` | `() -> box.Box` | Frozen `Box` of named palettes; exposed as `colormaps.palettes`. |
| `legends.builtin_legends` | dictionary | Built-ins include `NLCD`, `ESA_WorldCover`, `ESRI_LandCover`, `Dynamic_World`, `NWI`, `MODIS/...`, `USDA/NASS/CDL`, and more. |
| `legends.ee_table_to_legend` | `(in_table: str, out_file: str) -> None` | Converts Earth Engine tab-separated color tables with `Value`, `Color`, `Description` columns to a Python dictionary text file. |

## `geemap.plot` Plotly Express wrappers

Each wrapper accepts a pandas DataFrame, dictionary/array data that pandas can consume, or a CSV file/HTTP URL. Invalid non-DataFrame inputs raise `ValueError` after CSV handling.

| API | Signature summary | Notes |
|---|---|---|
| `bar_chart` | `(data=None, x=None, y=None, color=None, descending=True, sort_column=None, max_rows=None, x_label=None, y_label=None, title=None, legend_title=None, width=None, height=500, layout_args=None, **kwargs)` | Sorts by `sort_column` or y column when `descending` is not `None`; defaults grouped barmode. |
| `line_chart` | `(data=None, x=None, y=None, color=None, descending=None, max_rows=None, x_label=None, y_label=None, title=None, legend_title=None, width=None, height=500, layout_args=None, **kwargs)` | Plotly Express line. |
| `histogram` | `(data=None, x=None, y=None, color=None, descending=None, max_rows=None, x_label=None, y_label=None, title=None, width=None, height=500, layout_args=None, **kwargs)` | Plotly Express histogram. |
| `pie_chart` | `(data, names=None, values=None, descending=True, max_rows=None, other_label=None, color=None, color_discrete_sequence=None, color_discrete_map=None, hover_name=None, hover_data=None, custom_data=None, labels=None, title=None, legend_title=None, template=None, width=None, height=None, opacity=None, hole=None, layout_args=None, **kwargs)` | When `max_rows` is set with string `names`/`values`, small slices are grouped under `other_label`. |

## `geemap.plotlymap`

| API | Signature | Notes |
|---|---|---|
| `Map` | `(center: tuple[int, int] = (20, 0), zoom: int = 1, basemap: str = 'open-street-map', height: int = 600, **kwargs)` | Inherits `plotly.graph_objects.FigureWidget`; pass `ee_initialize=False` for no-auth local work. Center is `(lat, lon)`. |
| `Map.add_controls` | `(controls)` | String or list; otherwise raises `ValueError`. |
| `Map.remove_controls` | `(controls)` | String or list; otherwise raises `ValueError`. |
| `Map.set_center` | `(lat: float, lon: float, zoom: int | None = None) -> None` | Keeps current zoom when omitted. |
| `Map.add_basemap` | `(basemap: str = 'ROADMAP') -> None` | Validates against Plotly basemap dictionary; use [interactive maps](../../interactive-earth-engine-maps/SKILL.md) for ordinary base map controls. |
| `Map.add_mapbox_layer` | `(style, access_token=None)` | Reads `MAPBOX_TOKEN` when token omitted. |
| `Map.add_tile_layer` | `(url: str, name: str = 'TileLayer', attribution: str = '', opacity: float = 1.0, **kwargs) -> None` | Adds raster tile layer. |
| `Map.add_ee_layer` / `addLayer` | `(ee_object, vis_params={}, name: str | None = None, shown: bool = True, opacity: float = 1.0, **kwargs)` | Validates EE object type and palette type before generating a tile URL. |
| `Map.add_heatmap` | `(data, latitude='latitude', longitude='longitude', z='value', radius=10, colorscale=None, name='Heat map', **kwargs)` | DataFrame or CSV path; invalid data raises `ValueError`. |
| `Map.add_gdf` | `(gdf, label_col=None, color_col=None, labels=None, opacity=1.0, zoom=None, color_continuous_scale='Viridis', **kwargs)` | Requires a GeoPandas GeoDataFrame. |
| `fix_widget_error` | `()` | Patch for the known Plotly FigureWidget `mapbox._derived` error. |

## Optional backend map classes

| Backend | Constructor or key API | Notes |
|---|---|---|
| pydeck `deck.Layer` | `(type: str, data: str | None = None, id=None, use_binary_transport: bool | None = None, **kwargs)` | Thin wrapper over `pydeck.Layer`; `geemap.deck` import raises `ImportError` if `pydeck` is missing. |
| pydeck `deck.Map` | `(center: tuple[float, float] = (20, 0), zoom: float = 1.2, height: int = 800, width: int | None = None, **kwargs)` | Inherits `pydeck.Deck`; pass `ee_initialize=False` for local-only maps. Center is `(lat, lon)`. |
| `deck.Map.add_layer` | `(layer, layer_name: str | None = None, **kwargs)` | Accepts a pydeck layer or an HTTP tile URL. |
| `deck.Map.add_ee_layer` / `addLayer` | `(ee_object, vis_params={}, name=None, **kwargs)` | Same EE type and palette validation pattern as Plotly. |
| `deck.Map.add_gdf` | `(gdf, layer_name=None, random_color_column=None, **kwargs)` | Requires GeoPandas. |
| kepler `kepler.Map` | `(**kwargs)` | Defaults `center=[20, 0]`, `zoom=1.3`, `height=600`, `width=600`, `dragRotate=False`, and `show_docs=False`. |
| `kepler.Map.add_geojson` | `(in_geojson: str | dict, layer_name='Untitled', config=None, **kwargs)` | File path, HTTP URL, or dictionary; missing files raise `FileNotFoundError`; invalid type raises `TypeError`. |
| `kepler.Map.add_shp/add_csv/add_vector/add_kml` | file-oriented methods | Need local files, network for URLs, and vector extras such as GeoPandas where applicable. |
| `kepler.Map.to_html` | `(filename: str | None = None, read_only: bool = False, **kwargs)` | Filename extension must be `.html` when supplied. |
| `kepler.Map.to_streamlit` | `(width=800, height=600, responsive=True, scrolling=False, **kwargs)` | Requires Streamlit integration. |
| MapLibre `maplibregl.Map` | `(center: tuple[float, float] = (0, 20), zoom: float = 1, pitch: float = 0, bearing: float = 0, style: str = 'dark-matter', height: str = '600px', controls: dict[str, str] = {...}, **kwargs)` | Inherits MapLibre ipywidget. Center is `(lon, lat)`. Style may be Carto, demo, URL, MapTiler, or `3d-*`. |
| `maplibregl.Map.add_geojson` | `(data: str | dict, layer_type=None, filter=None, paint=None, name=None, fit_bounds=True, visible=True, before_id=None, source_args={}, **kwargs)` | URL or GeoJSON dictionary. |
| `maplibregl.Map.add_ee_layer` | `(ee_object=None, vis_params={}, asset_id=None, name=None, opacity=1.0, attribution='Google Earth Engine', visible=True, before_id=None, ee_initialize=False, **kwargs)` | Can defer EE initialization with `ee_initialize=False`; still needs EE auth for real tile IDs. |
| `maplibregl.Map.add_legend` | `(title='Legend', legend_dict=None, labels=None, colors=None, fontsize=15, bg_color='white', position='bottom-right', builtin_legend=None, **kwargs)` | Labels/colors must be lists of equal length; positions are corner strings. |
| `maplibregl.Map.add_colorbar` | `(width=3.0, height=0.2, vmin=0, vmax=1.0, palette=None, vis_params=None, cmap='gray', discrete=False, label=None, label_size=10, label_weight='normal', tick_size=8, bg_color='white', orientation='horizontal', dpi='figure', transparent=False, position='bottom-right', **kwargs)` | Generates a PNG colorbar and adds it as HTML. |
| `construct_maptiler_style` | `(style: str, api_key: str | None = None)` | Returns MapTiler style URL or falls back to `dark-matter` when style retrieval fails. |
| `maptiler_3d_style` | `(style='satellite', exaggeration=1.0, tile_size=512, tile_type=None, max_zoom=24, hillshade=True, token='MAPTILER_KEY', api_key=None)` | 3D terrain style; requires a MapTiler key via argument or token env var. |
