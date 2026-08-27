# Raster API reference

This file records the verified ArcGIS API for Python surfaces used by the imagery/raster notebooks and samples.

## `ImageryLayer`

Verified signature:

```python
ImageryLayer(url: str, gis: Optional[GIS] = None, parent_url=None)
```

Verified facts:

- Represents an image service resource as a layer.
- Retrieves and displays data from image services.
- Supports server-defined or client-defined raster functions and mosaic rules.
- Can also be created from raster datasets or raster products in datastores registered with the server or active GIS.

Common notebook patterns:

- Read `layer.properties.rasterFunctionInfos` to discover published raster functions.
- Use `apply(layer, function_name)` to visualize a published function.
- Use `save(name, for_viz=True)` for display-oriented persistence.
- Use `save(name, for_viz=False)` when the user wants a source-resolution analysis product.
- Use `draw_graph()` on a chained result to inspect the workflow before saving.

## Raster function surfaces

The notebooks exercise these client-side and service-published raster function patterns:

- `apply`
- `stretch`
- `extract_band`
- `band_arithmetic`
- `clip`
- `colormap`
- `savi`
- `ndvi`
- `composite_band`
- `create_color_composite`
- `constant_raster`
- `aggregate`
- `remap`
- `con`

Practical facts:

- Raster functions are lightweight and intended for on-the-fly processing or chained visualization.
- They can be combined into graphs before being rendered or persisted.
- They operate at display resolution when used for visualization.
- The user should validate band ordering and available function names before building a chain.

## `arcgis.raster.analytics.copy_raster`

Verified signature:

```python
copy_raster(input_raster, output_cellsize: Optional[dict[str, Any]] = None, resampling_method: str = 'NEAREST', clip_setting: Optional[str] = None, output_name: Optional[str] = None, process_as_multidimensional: Optional[bool] = None, build_transpose: Optional[bool] = None, context: Optional[dict[str, Any]] = None, raster_type_name: Optional[str] = None, raster_type_params: Optional[dict[str, Any]] = None, source_mosaic_dataset: Optional[str] = None, *, gis: Optional[GIS] = None, future: bool = False, **kwargs)
```

Verified facts:

- Takes a single raster input and generates output imagery using parallel processing.
- Can clip, resample, and reproject the output.
- Can create hosted imagery layers in ArcGIS Enterprise and ArcGIS Online from local raster datasets by uploading data to the server.
- Supports `context` for options such as by-reference handling and image-collection properties.
- Supports multidimensional handling through `process_as_multidimensional` and `build_transpose`.
- Accepts `future=True` for asynchronous execution.

Notebook patterns:

- `raster_type_name` identifies the raster format/sensor family.
- `raster_type_params` carries product type and processing template settings.
- Unique `output_name` values are used for every persisted output.

## Raster analytics tool family

The repository examples and API inspection confirm these tools as part of the raster analytics surface:

- `is_supported`
- `create_image_collection`
- `calculate_density`
- `create_viewshed`
- `interpolate_points`
- `convert_feature_to_raster`
- `convert_raster_to_feature`
- `add_image`
- `generate_raster`
- `train_classifier`
- `classify`
- `segment`
- `aggregate_multidimensional_raster`
- `build_multidimensional_transpose`
- `subset_multidimensional_raster`
- `merge_multidimensional_rasters`
- `manage_multidimensional_raster`
- `copy_raster`

Return-value notes:

- `interpolate_points(...)` returns a named result with `output_raster`, `process_info`, and optional `output_error_raster`.
- Many raster analytics tools accept `output_name` and/or `future=True`.
- `segment(...)` is shown in the guide with an 8-bit input raster requirement.
- Classification and segmentation in this skill are raster analytics tools, not `arcgis.learn` model training.

## Orthomapping surfaces

The notebooks confirm these orthomapping functions as the main server-side workflow:

- `is_supported`
- `query_camera_info`
- `compute_sensor_model`
- `compute_control_points`
- `match_control_points`
- `edit_control_points`
- `query_control_points`
- `compute_seamlines`
- `generate_orthomosaic`
- `generate_dem`
- `generate_report`
- `alter_processing_states`
- `reset_image_collection`

Notebook-confirmed product boundaries:

- `generate_orthomosaic(...)` produces the orthomosaic output.
- `generate_dem(...)` is used for both DSM and DTM outputs by changing `surface_type`.
- `alter_processing_states(...)` updates orthomapping processing configuration.
- `reset_image_collection(...)` restores the image collection state.

## Support checks to prefer first

- `arcgis.raster.analytics.is_supported(gis)`
- `arcgis.raster.orthomapping.is_supported(gis)`

If either check fails, treat the operation as unsupported in the current GIS and move the user to a prerequisite or fallback path.

## Cross-skill routing reminders

- `arcgis.learn` model training/inference belongs to `deep-learning`.
- Feature-layer analysis belongs to `features-dataframes-analysis`.
- Map widget and geocoding/routing workflows belong to `mapping-location-services`.
