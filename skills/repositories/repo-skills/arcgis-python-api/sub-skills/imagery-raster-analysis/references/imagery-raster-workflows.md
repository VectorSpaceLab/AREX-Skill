# Imagery and raster workflows

This reference distills the repo notebooks into a safe decision guide for imagery layers, raster functions, raster analytics, multidimensional rasters, and orthomapping.

## 1) Choose the right path

| Need | Prefer | Why |
| --- | --- | --- |
| Open or inspect an existing image service | `ImageryLayer` | It represents an image service as a layer and is the starting point for service-backed imagery work. |
| Visualize or transform pixels on the fly | Raster functions | Lightweight map algebra and rendering at display resolution. |
| Create hosted or persisted analysis outputs | Raster analytics | Server-side tools, distributed processing, and saved raster products. |
| Work with UAV image collections, GCPs, seamlines, DSM/DTM, or orthomosaics | Orthomapping | Dedicated image collection and product-generation workflow. |
| Handle multidimensional rasters | Raster analytics or `copy_raster` with multidimensional settings | These workflows preserve dimension metadata and can transpose or aggregate along time/depth-like axes. |

If the GIS does not support raster analytics or orthomapping, stop after the preflight check and explain the missing capability.

## 2) Start from imagery layers

Use `ImageryLayer` when you already have an image-service URL or a hosted imagery item. The layer can be created from an image service, then inspected for available server raster functions.

Typical flow:

1. Get an authenticated `GIS`.
2. Create or retrieve the `ImageryLayer`.
3. Inspect `layer.properties.rasterFunctionInfos`.
4. Apply a published raster function by name, or chain local raster functions.
5. Add the result to a map only if the user needs visualization.

Important notebook patterns:

- `ImageryLayer` is treated as the service-backed data source.
- Published functions are discovered through `rasterFunctionInfos`.
- `apply(layer, function_name)` cycles through available service functions.
- `save(name, for_viz=True)` stores a display-oriented visualization.
- `save(name, for_viz=False)` uses distributed raster analysis for a source-resolution product.

## 3) Use raster functions for on-the-fly work

Raster functions are the right choice when the user wants interactive visualization, lightweight map algebra, or a chained pixel operation.

Common notebook patterns:

- `stretch(extract_band(layer, [4, 5, 3]), ...)` for natural-color or land/water views.
- `band_arithmetic(layer, "(b5 - b4) / (b5 + b4)")` for NDVI-style math.
- `savi(layer, band_indexes="5 4 0.3")` for a vegetation index.
- `clip(layer, geometry)` to crop to an area of interest.
- `colormap(...)` and similar functions to style results.
- `draw_graph()` on a chained result to inspect the workflow before saving.

Validation habits:

- Verify the available function names before applying a published function.
- Confirm band order and band count before using band arithmetic.
- Keep the first version of a chain small enough to inspect visually.
- Use `draw_graph()` when the chain gets complex.

## 4) Use raster analytics for server-side processing

Raster analytics is the choice when the output needs to be persisted, the dataset is large, or the workflow depends on Image Server / raster analytics services.

Examples from the notebooks and samples:

- `copy_raster(...)` to create hosted imagery layers from local rasters or supported datastore inputs.
- `create_image_collection(...)` to build imagery layers from multiple rasters.
- `calculate_density(...)` for point-density surfaces.
- `create_viewshed(...)` for visibility surfaces.
- `interpolate_points(...)` for continuous raster surfaces from sample points.
- `convert_feature_to_raster(...)` and `convert_raster_to_feature(...)` for raster/vector conversion.
- `train_classifier(...)`, `classify(...)`, and `segment(...)` for raster analytics classification and segmentation.
- `generate_raster(...)` and other server-side outputs for persisted products.

Output and async guidance:

- Use a unique `output_name` for every persisted job, preferably with a timestamp or GUID suffix.
- Treat calls with `future=True` as asynchronous jobs.
- Some tools return a result object or named tuple; `interpolate_points(...)` exposes `output_raster`, `process_info`, and optionally `output_error_raster`.
- Do not assume the result is ready just because the function returned.

## 5) Handle multidimensional rasters explicitly

The repo examples treat multidimensional data as a separate concern from ordinary 2-D map algebra.

Use the multidimensional raster path when you need to:

- preserve dimension metadata,
- process a raster as a collection of slices,
- transpose or aggregate across dimensions,
- or publish a hosted imagery layer from multidimensional inputs.

Useful knobs seen in the examples include:

- `process_as_multidimensional`
- `build_transpose`
- `aggregate_multidimensional_raster`
- `build_multidimensional_transpose`
- `subset_multidimensional_raster`
- `merge_multidimensional_rasters`
- `manage_multidimensional_raster`

## 6) Orthomapping boundary

Use orthomapping when the user needs the UAV/image-collection workflow, not generic raster styling.

Typical boundary:

- Prepare an image collection from raw images and metadata.
- Provide `gps`, `cameraProperties`, and any elevation reference data the workflow needs.
- Check both orthomapping and raster analytics support on the target GIS.
- Run sensor-model and control-point steps first.
- Then compute seamlines and generate downstream products such as orthomosaics and DSM/DTM outputs.

Typical orthomapping sequence:

1. Verify support with `orthomapping.is_supported(gis)`.
2. Create the image collection.
3. Optionally query camera information.
4. Run `compute_sensor_model(...)`.
5. Use `compute_control_points(...)`, `match_control_points(...)`, and `edit_control_points(...)` when GCPs are involved.
6. Generate seamlines with `compute_seamlines(...)`.
7. Create `generate_orthomosaic(...)` and `generate_dem(...)` outputs.
8. Adjust or reset processing state with `alter_processing_states(...)` and `reset_image_collection(...)` when needed.

If the GIS lacks the required raster services, stop after collection prep and explain that DSM/orthomosaic generation cannot proceed.

## 7) Service and data-size caveats

- `ImageryLayer` is service-backed; it is not a substitute for local raster processing libraries.
- Hosted imagery products can incur storage and service costs.
- Large raster jobs belong on the server-side analytics path, not in client-side function chains.
- `save(for_viz=True)` is for visualization; it is not the same as a source-resolution analysis output.
- Registered datastores and image-service URLs behave differently; choose the workflow that matches the source data.

## 8) Recommended preflight checklist

- Confirm the data source type: image service, local raster, raster store, or image collection.
- Confirm the GIS supports the needed server capability.
- Confirm the output naming scheme is unique.
- Confirm the band order, raster type, and dimensionality.
- Confirm the user wants visualization, persistence, or orthomapping products.
- Confirm credentials are available before any service-backed call.

For API-level details and troubleshooting, continue to [API reference](raster-api-reference.md) and [Troubleshooting](troubleshooting.md).
