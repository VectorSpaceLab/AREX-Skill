# API Reference

This reference captures the verified GeoAI surfaces that matter for geospatial data pipelines, file inspection, downloads, tiling, raster/vector conversion, and batch config execution.

## CLI surface

### `geoai info FILEPATH`

Detects file type by extension, then prints raster or vector metadata.

- Vector extensions recognized directly: `.geojson`, `.json`, `.shp`, `.gpkg`, `.parquet`, `.geoparquet`, `.fgb`, `.kml`
- Raster extensions recognized directly: `.tif`, `.tiff`, `.img`, `.jp2`, `.vrt`, `.nc`, `.hdf`
- Unknown extensions fall back to raster first, then vector
- Non-readable files exit nonzero

Use it for quick inspection before any conversion or pipeline run.

### `geoai download naip --bbox minx,miny,maxx,maxy --output PATH [--year YEAR]`

Thin convenience wrapper around NAIP download logic.

- `bbox` is WGS84 order `(minx, miny, maxx, maxy)`
- the command supports NAIP only
- it is safest to treat this as a convenience entry point and prefer the Python API when exact output-directory handling matters

### `geoai pipeline show CONFIG_PATH`

Loads a JSON/YAML config and prints pipeline name, workers, error policy, and step list.

### `geoai pipeline run CONFIG_PATH [--input-dir DIR] [--output-dir DIR] [--max-workers N] [--checkpoint-dir DIR] [--on-error skip|fail] [--quiet]`

Runs a batch pipeline.

- `--input-dir` expands through `GlobStep` or the pipeline's auto-glob fallback
- `--output-dir` is injected into item dictionaries
- `--checkpoint-dir` creates JSON checkpoints
- `--on-error` controls `skip` versus `fail`
- `--quiet` suppresses progress bars

## `geoai.pipeline`

### Classes and enums

| Symbol | Signature | Role |
| --- | --- | --- |
| `PipelineStep` | `(name: str) -> None` | Base class for custom steps. |
| `FunctionStep` | `(name: str, fn, setup_fn=None, teardown_fn=None) -> None` | Python-only wrapper around a callable. |
| `GlobStep` | `(name: str = 'glob', extensions: Optional[List[str]] = None) -> None` | Expands directories or glob patterns into work items. |
| `SemanticSegmentationStep` | `(name='semantic_segmentation', model_path='', architecture='unet', encoder_name='resnet34', num_channels=3, num_classes=2, window_size=512, overlap=256, batch_size=4, device=None, suffix='_mask') -> None` | Runs segmentation inference and writes a mask GeoTIFF. |
| `RasterToVectorStep` | `(name='raster_to_vector', output_format='.geojson', simplify_tolerance=None, input_key='output_path', output_key='vector_path') -> None` | Converts raster masks to vector output. |
| `Pipeline` | `(steps, max_workers=1, executor_type='thread', on_error='skip', checkpoint_dir=None, item_key_fn=None, name=None, quiet=False) -> None` | Runs ordered batch steps. |
| `PipelineResult` | `(completed=[], failed=[], skipped=[], total_duration=0.0, checkpoint_path=None) -> None` | Aggregated run result. |
| `StepResult` | `(item, success, error=None, duration=0.0) -> None` | Per-item result container. |
| `ErrorPolicy` | `(*values)` | `skip` or `fail`. |
| `ItemStatus` | `(*values)` | `pending`, `completed`, `failed`, `skipped`. |
| `CheckpointEntry` | `(item_key, status, error=None, completed_steps=[], timestamp='') -> None` | Single checkpoint record. |
| `CheckpointManager` | `(checkpoint_path, config_hash='') -> None` | JSON checkpoint persistence and resume. |

### Loader and registry

| API | Signature | Notes |
| --- | --- | --- |
| `load_pipeline` | `(config_path: str, **overrides: Any) -> Pipeline` | JSON/YAML loader only. Supports config overrides. |
| `register_step` | `(cls: type) -> type` | Registers a custom `PipelineStep` subclass for config deserialization. |

#### Config registration rules

Only these built-in steps are registered for JSON/YAML configs:

- `GlobStep`
- `SemanticSegmentationStep`
- `RasterToVectorStep`

`FunctionStep` is useful when building pipelines in Python code, but it is not registered for config deserialization in the bundled loader.

#### Loader behavior

- unsupported file extensions raise `ValueError`
- missing configs raise `FileNotFoundError`
- unknown step types raise `ValueError` and include the available registry keys
- checkpoint state is reset when the config hash changes
- `Pipeline` only accepts `executor_type='thread'`

## `geoai.download`

| API | Signature | Use |
| --- | --- | --- |
| `download_naip` | `(bbox, output_dir, year=None, max_items=10, overwrite=False, preview=False, **kwargs)` | Search and download NAIP imagery from Planetary Computer. |
| `download_overture_buildings` | `(bbox, output, overture_type='building', **kwargs)` | Convenience wrapper around Overture data retrieval. |
| `get_overture_data` | `(overture_type, bbox=None, columns=None, output=None, **kwargs)` | Return a GeoDataFrame for Overture data and optionally save it. |
| `get_all_overture_types` | `() -> List[str]` | List Overture feature types. |
| `convert_vector_format` | `(input_file, output_format='geojson', filter_expression=None)` | Local vector format conversion. |
| `extract_building_stats` | `(data) -> Dict[str, Any]` | Summarize building features. |
| `download_pc_stac_item` | `(item_url, bands=None, output_dir=None, show_progress=True, merge_bands=False, merged_filename=None, overwrite=False, cell_size=None)` | Download one STAC item and optionally merge bands. |
| `pc_collection_list` | `(endpoint='https://planetarycomputer.microsoft.com/api/stac/v1', detailed=False, filter_by=None, sort_by='id')` | List collections from Planetary Computer. |
| `pc_stac_search` | `(collection, bbox=None, time_range=None, query=None, limit=10, max_items=None, quiet=False, endpoint='https://planetarycomputer.microsoft.com/api/stac/v1')` | Search STAC items. |
| `pc_stac_download` | `(items, output_dir='.', assets=None, max_workers=1, skip_existing=True)` | Download assets from one or more STAC items. |
| `pc_item_asset_list` | `(item) -> List[str]` | List asset keys on a STAC item. |
| `read_pc_item_asset` | `(item, asset, output=None, as_cog=True, **kwargs)` | Read a single signed asset through rioxarray. |
| `view_pc_item` | `(url=None, collection=None, item=None, assets=None, bands=None, titiler_endpoint=None, name='STAC Item', attribution='Planetary Computer', opacity=1.0, shown=True, fit_bounds=True, layer_index=None, backend='folium', basemap=None, map_args=None, **kwargs)` | Interactive map preview for one STAC item. |
| `view_pc_items` | `(urls=None, collection=None, items=None, assets=None, bands=None, titiler_endpoint=None, attribution='Planetary Computer', opacity=1.0, shown=True, fit_bounds=True, layer_index=None, backend='folium', basemap=None, map_args=None, **kwargs)` | Interactive map preview for multiple STAC items. |
| `download_with_progress` | `(url, output_path, max_size=None)` | Stream a file after URL validation. |
| `_validate_url` | `(url)` | Allows only `http` and `https` URLs with a host. |
| `preview_raster` | `(data, title=None)` | Small matplotlib preview for downloaded raster data. |

### Download behavior to remember

- `download_naip` and Overture helpers assume a bbox in WGS84 order `(minx, miny, maxx, maxy)`.
- `download_pc_stac_item` and `pc_stac_download` sign Planetary Computer assets before download.
- `download_with_progress` uses `requests` streaming and can enforce a maximum size.
- `convert_vector_format` can convert to GeoJSON, GeoParquet, Shapefile, or CSV; CSV stores WKT geometry in a `geometry_wkt` column.

## `geoai.utils.raster`

### Inspection and I/O

| API | Signature | Notes |
| --- | --- | --- |
| `read_raster_metadata` | `(raster_path) -> RasterMetadata` | Lightweight metadata-only read. |
| `get_raster_info` | `(raster_path) -> Dict[str, Any]` | Driver, shape, dtype, CRS, transform, bounds, resolution, nodata, band stats. |
| `get_raster_stats` | `(raster_path, divide_by=1.0) -> Dict[str, Any]` | Bandwise min/max/mean/std. |
| `print_raster_info` | `(raster_path, show_preview=True, figsize=(10, 8))` | Prints metadata and optionally previews. |
| `get_raster_info_gdal` | `(raster_path) -> Optional[Dict[str, Any]]` | GDAL-backed alternative. |
| `read_raster` | `(source, band=None, masked=True, **kwargs) -> xr.DataArray` | Reads local or URL raster data with geospatial metadata. |
| `get_raster_resolution` | `(image_path) -> Tuple[float, float]` | Returns raster resolution. |

### Spatial transforms and conversions

| API | Signature | Notes |
| --- | --- | --- |
| `clip_raster_by_bbox` | `(input_raster, output_raster, bbox, bands=None, bbox_type='geo', bbox_crs=None) -> str` | Clip by geographic bbox or pixel window. |
| `raster_to_vector` | `(raster_path, output_path=None, threshold=0, min_area=10, simplify_tolerance=None, class_values=None, attribute_name='class', unique_attribute_value=False, output_format='geojson', plot_result=False) -> gpd.GeoDataFrame` | Polygonize a raster mask. |
| `raster_to_vector_batch` | `(input_dir, output_dir, pattern='*.tif', threshold=0, min_area=10, simplify_tolerance=None, class_values=None, attribute_name='class', output_format='geojson', merge_output=False, merge_filename='merged_vectors')` | Batch polygonize rasters. |
| `vector_to_raster` | `(vector_path, output_path=None, reference_raster=None, attribute_field=None, output_shape=None, transform=None, pixel_size=None, bounds=None, crs=None, all_touched=False, fill_value=0, dtype=np.uint8, nodata=None, plot_result=False) -> np.ndarray` | Burn vector features into a raster. |
| `batch_vector_to_raster` | `(vector_path, output_dir, attribute_field=None, reference_rasters=None, bounds_list=None, output_filename_pattern='{vector_name}_{index}', pixel_size=1.0, all_touched=False, fill_value=0, dtype=np.uint8, nodata=None) -> List[str]` | Batch rasterization. |
| `masks_to_vector` | `(mask_path, output_path=None, simplify_tolerance=1.0, mask_threshold=0.5, min_object_area=100, max_object_area=None, nms_iou_threshold=0.5) -> gpd.GeoDataFrame` | Convert instance masks to vectors. |
| `mosaic_geotiffs` | `(input_dir, output_file, mask_file=None) -> None` | Build a COG-style mosaic from GeoTIFFs. |
| `stack_bands` | `(input_files, output_file, resolution=None, dtype=None, temp_vrt='stack.vrt', overwrite=False, compress='DEFLATE', output_format='COG', extra_gdal_translate_args=None) -> str` | Stack files into a multiband raster. |
| `write_colormap` | `(image, colormap, output=None) -> None` | Apply a colormap using leafmap. |
| `clean_instance_mask` | `(input_path, output_path=None, min_area=50, fill_holes=True, max_hole_area=100, smooth=True, smooth_sigma=1.5, band=1) -> str` | Clean instance masks after inference. |

### Read format support

`read_vector` accepts common vector formats including GeoJSON, Shapefile, GeoPackage, GeoParquet, GML, KML, GPX, URLs, and layer-qualified files.

## `geoai.utils.vector`

| API | Signature | Use |
| --- | --- | --- |
| `get_vector_info` | `(vector_path) -> Optional[Dict[str, Any]]` | Feature count, CRS, geometry types, bounds, attribute stats. |
| `print_vector_info` | `(vector_path, show_preview=True, figsize=(10, 8)) -> Optional[Dict[str, Any]]` | Print-and-preview helper. |
| `get_vector_info_ogr` | `(vector_path) -> Optional[Dict[str, Any]]` | OGR-backed alternative. |
| `analyze_vector_attributes` | `(vector_path, attribute_name) -> Optional[Dict[str, Any]]` | Attribute distribution / histogram helper. |
| `visualize_vector_by_attribute` | `(vector_path, attribute_name, cmap='viridis', figsize=(10, 8)) -> bool` | Thematic plot by attribute. |
| `export_tiles_to_geojson` | `(tile_coordinates, src, output_path, tile_size=None, stride=None) -> str` | Emit tile footprints as GeoJSON. |
| `add_geometric_properties` | `(data, properties=None, area_unit='m2', length_unit='m') -> gpd.GeoDataFrame` | Add area/length-style geometry properties. |
| `vector_to_geojson` | `(filename, output=None, **kwargs)` | Convert a vector file to GeoJSON-like output. |
| `geojson_to_coords` | `(geojson, src_crs='epsg:4326', dst_crs='epsg:4326') -> List[List[float]]` | Extract coordinates from GeoJSON. |
| `boxes_to_vector` | `(coords, src_crs, dst_crs='EPSG:4326', output=None, **kwargs) -> Optional[gpd.GeoDataFrame]` | Convert bounding boxes into polygons. |
| `geojson_to_xy` | `(src_fp, geojson, coord_crs='epsg:4326', **kwargs) -> List[List[float]]` | Raster-pixel coordinate conversion helper. |
| `smooth_vector` | `(vector_data, output_path=None, segment_length=None, smooth_iterations=3, num_cores=0, merge_collection=True, merge_field=None, merge_multipolygons=True, preserve_area=True, area_tolerance=0.01, **kwargs) -> gpd.GeoDataFrame` | Geometry smoothing / regularization helper. |

## `geoai.utils.sampling`

These helpers import TorchGeo lazily and raise a clear `ImportError` if TorchGeo is missing.

| API | Signature | Use |
| --- | --- | --- |
| `create_raster_dataset` | `(paths='data', is_image=True, filename_glob='*.tif', separate_files=False, filename_regex='.*', date_format='%Y%m%d', crs=None, res=None, bands=None, transforms=None, cache=True, time_series=False, **kwargs)` | Build a TorchGeo `RasterDataset`. |
| `create_segmentation_dataset` | `(image_paths_or_dataset, mask_paths_or_dataset, image_filename_glob='*.tif', mask_filename_glob='*.tif', image_transforms=None, mask_transforms=None, crs=None, res=None, bands=None, cache=True, **kwargs)` | Build aligned image/mask datasets. |
| `create_geo_sampler` | `(dataset, sampler='random', size=256, stride=None, length=None, roi=None, toi=None, units='pixels', generator=None, **kwargs)` | Create a TorchGeo sampler. |
| `create_geo_dataloader` | `(dataset, sampler=None, sampler_type='random', size=256, stride=None, length=None, roi=None, toi=None, units='pixels', generator=None, batch_size=1, num_workers=0, collate_fn=None, **dataloader_kwargs)` | Create a single data loader. |
| `create_geo_dataloaders` | `(train_dataset, val_dataset=None, test_dataset=None, size=256, stride=None, length=None, batch_size=1, num_workers=0, train_sampler='random', eval_sampler='grid', collate_fn=None, **dataloader_kwargs)` | Create train/val/test loaders. |
| `create_torchgeo_segmentation_dataloaders` | `(image_path, mask_path, chip_size=256, stride=None, train_length=128, val_length=32, batch_size=4, num_workers=0, val_sampler='random', include_grid_loader=True, image_filename_glob='*.tif', mask_filename_glob='*.tif', **kwargs)` | Convenience wrapper for segmentation chips. |
| `geo_sample_to_tuple` | `(batch, image_key='image', target_key='mask', num_channels=None, normalize=False, squeeze_target=True)` | Convert TorchGeo batches to `(image, target)` tuples. |
| `predict_torchgeo_segmentation_batch` | `(model, dataloader_or_batch, device=None, num_channels=3, normalize=True, binary=True, mask_threshold=0) -> Dict[str, Any]` | Predict on one batch. |
| `plot_torchgeo_segmentation_predictions` | `(model, dataloader_or_batch, n=4, figsize=(9, 12), cmap='Blues', **predict_kwargs)` | Visualize images/masks/predictions. |
| `train_torchgeo_segmentation_model` | `(image_path=None, mask_path=None, train_dataloader=None, val_dataloader=None, model=None, output_dir=None, num_channels=3, num_classes=2, chip_size=256, stride=None, train_length=128, val_length=32, batch_size=4, num_workers=0, num_epochs=5, learning_rate=0.001, weight_decay=0.0001, loss_fn=None, optimizer=None, device=None, normalize=True, binary=True, mask_threshold=0, verbose=True, **dataset_kwargs)` | Quick TorchGeo-style training helper. |

## `geoai.utils.visualization`

These helpers are for QA and review; they do not mutate source data.

| API | Signature | Use |
| --- | --- | --- |
| `view_raster` | `(source, indexes=None, colormap=None, vmin=None, vmax=None, nodata=None, attribution=None, layer_name='Raster', layer_index=None, zoom_to_layer=True, visible=True, opacity=1.0, array_args=None, client_args={'cors_all': False}, legend_args=None, basemap='OpenStreetMap', basemap_args=None, backend='folium', **kwargs)` | Interactive raster display. |
| `view_image` | `(image, transpose=False, bdx=None, clip_percentiles=(2, 98), gamma=None, figsize=(10, 5), axis_off=True, title=None, **kwargs)` | Matplotlib image preview. |
| `plot_images` | `(images, axs, chnls=[2, 1, 0], bright=1.0)` | Plot image chips in axes. |
| `plot_masks` | `(masks, axs, cmap='Blues')` | Plot mask chips. |
| `plot_batch` | `(batch, bright=1.0, cols=4, width=5, chnls=[2, 1, 0], cmap='Blues')` | Batch QA viewer. |
| `view_vector` | `(vector_data, column=None, cmap='viridis', figsize=(10, 10), title=None, legend=True, basemap=False, basemap_type='streets', alpha=0.7, edge_color='black', classification='quantiles', n_classes=5, highlight_index=None, highlight_color='red', scheme=None, save_path=None, dpi=300, raster_path=None, raster_bands=None, raster_cmap='gray', outline_only=False, outline_linewidth=1.0)` | Interactive/static vector review. |
| `view_vector_interactive` | `(vector_data, layer_name='Vector', tiles_args=None, opacity=0.7, **kwargs)` | Interactive vector layer preview. |
| `create_split_map` | `(left_layer='TERRAIN', right_layer='OpenTopoMap', left_args=None, right_args=None, left_array_args=None, right_array_args=None, zoom_control=True, fullscreen_control=True, layer_control=True, add_close_button=False, left_label=None, right_label=None, left_position='bottomleft', right_position='bottomright', widget_layout=None, draggable=True, center=[20, 0], zoom=2, height='600px', basemap=None, basemap_args=None, m=None, **kwargs)` | Split-map comparison. |
| `display_training_tiles` | `(output_dir, num_tiles=6, figsize=(18, 6), cmap='gray', show_axes=True, save_path=None, image_subdir=None, mask_subdir=None)` | Review tiles from an output directory. |
| `display_image_with_vector` | `(image_path, vector_path, figsize=(16, 8), vector_color='red', vector_linewidth=1, vector_facecolor='none', save_path=None)` | Overlay vectors on imagery. |
| `create_overview_image` | `(src, tile_coordinates, output_path, tile_size, stride, geojson_path=None, in_class_data=None) -> str` | Build a tile overview image. |
| `plot_performance_metrics` | `(history_path, figsize=None, verbose=True, save_path=None, csv_path=None, kwargs=None) -> pd.DataFrame` | Plot training history stored on disk. |
| `plot_prediction_comparison` | `(original_image, prediction_image, ground_truth_image=None, titles=None, figsize=(15, 5), save_path=None, show_plot=True, prediction_colormap='gray', ground_truth_colormap='gray', original_colormap=None, indexes=None, divider=None)` | Compare source / prediction / truth panels. |

## Practical call patterns

- Prefer module-level imports when writing scripts: `from geoai.pipeline import load_pipeline`.
- Use top-level convenience exports when working interactively: `from geoai import get_raster_info, raster_to_vector`.
- For batch configs, start with `load_pipeline` or the bundled validator before running `geoai pipeline run`.
- For vector/raster conversion, load metadata first, then choose `reference_raster` or a precise `transform`/`bounds` pair.
- For TorchGeo sampling, keep the sampling step separate from model training so this sub-skill stays focused on data and pipeline preparation.
