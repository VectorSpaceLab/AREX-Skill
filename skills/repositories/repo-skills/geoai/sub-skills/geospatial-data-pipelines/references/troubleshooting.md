# Troubleshooting

Use this guide when GeoAI geospatial data workflows fail before or during a download, conversion, or pipeline run.

## 1) CRS and bbox issues first

### Symptom: raster/vector outputs do not overlap

Most GeoAI geospatial failures are actually CRS mismatches.

**Likely causes**

- vector data is still in EPSG:4326 while the raster is projected,
- bbox coordinates were passed in the wrong order,
- a geographic bbox was clipped against a projected raster without `bbox_crs`,
- `vector_to_raster` was called without a `reference_raster` or explicit transform/bounds.

**Fix**

1. Inspect both files:
   - `get_raster_info(raster_path)`
   - `get_vector_info(vector_path)`
2. Compare CRS values.
3. Reproject the vector to the raster CRS before clipping, rasterizing, or vectorizing.
4. For `clip_raster_by_bbox`, use:
   - geographic bbox: `(minx, miny, maxx, maxy)`
   - pixel bbox: `(min_row, min_col, max_row, max_col)`
5. If the bbox is in a different CRS, pass `bbox_crs` explicitly.

### Symptom: `clip_raster_by_bbox` says the bbox is invalid

Check the order.

- Geographic order must be `minx, miny, maxx, maxy`
- Pixel order must be `min_row, min_col, max_row, max_col`

A swapped latitude/longitude pair often looks like `minx >= maxx` or `miny >= maxy`.

### Symptom: `raster_to_vector` filters away everything unexpectedly

If the raster is in a geographic CRS, area thresholds are tricky because the raw area is in square degrees, not square meters.

**Fix**

- lower `min_area`, or
- project the raster/vector before applying area-based filtering, or
- verify the output with a tiny synthetic mask first.

## 2) GDAL / PROJ / rasterio errors

### Symptom: `rasterio` cannot open the file, or CRS metadata is missing

**Likely causes**

- broken GDAL/PROJ data installation,
- a corrupt file,
- unsupported extension,
- a path that is not actually a raster or vector.

**Fix**

- run `geoai info FILEPATH` to see whether the file is recognized,
- confirm the extension is one of the supported raster or vector types,
- use `read_raster` or `read_vector` directly to isolate the failure,
- check that the file opens in another GIS tool if needed.

### Symptom: PROJ or CRS transform errors during clipping or reprojection

**Likely causes**

- missing projection tables,
- invalid CRS definition,
- mismatched source and destination CRS values,
- unsupported transformation path in the installed environment.

**Fix**

- verify the source and destination CRS strings are valid,
- test a smaller reprojection step before batch processing,
- use the bundled smoke script to compare raster and vector CRS values:
  - [`scripts/geospatial_io_smoke.py`](../scripts/geospatial_io_smoke.py)

### Symptom: GDAL writes fail even though reading works

**Likely causes**

- output directory is not writable,
- the driver/extension pair is inconsistent,
- the target file already exists and the function is not set to overwrite,
- the output directory was not created.

**Fix**

- write to a temporary directory first,
- ensure the path extension matches the intended driver,
- confirm there is no stale file from a previous run.

## 3) Unsupported extensions or schema mismatches

### Symptom: `geoai info` or a reader says the format is unsupported

**Fix**

- use a supported raster extension: `.tif`, `.tiff`, `.img`, `.jp2`, `.vrt`, `.nc`, `.hdf`
- use a supported vector extension: `.geojson`, `.json`, `.shp`, `.gpkg`, `.parquet`, `.geoparquet`, `.fgb`, `.kml`
- if the file is a different format, convert it first with `convert_vector_format` or a safe external conversion step

### Symptom: vector schema problems after conversion

**Likely causes**

- geometry column is missing,
- attribute names contain unsupported characters for a downstream driver,
- a GeoPackage layer name or Shapefile field name is being truncated,
- the file contains mixed geometry types.

**Fix**

- inspect with `get_vector_info` or `get_vector_info_ogr`,
- simplify to a single output format with `convert_vector_format`,
- prefer GeoJSON or GeoPackage when you need fewer field-name surprises.

### Symptom: raster schema problems after rasterization

**Likely causes**

- `vector_to_raster` was called without a reference raster, transform, bounds, or pixel size,
- the output CRS is missing,
- attribute values are not numeric or are not the ones you expected,
- the raster dimensions are incompatible with the intended spatial extent.

**Fix**

- use `reference_raster` when available,
- otherwise provide `transform` plus `output_shape`, or `pixel_size` plus `bounds` plus `crs`,
- validate the burned values on a tiny polygon first.

## 4) STAC / network / download failures

### Symptom: Planetary Computer search fails or returns no items

**Likely causes**

- network access is blocked,
- the bbox does not overlap the dataset,
- the time range or query is too restrictive,
- the API endpoint is unavailable.

**Fix**

- confirm the bbox in WGS84 order `(minx, miny, maxx, maxy)`,
- loosen the query or date range,
- run `pc_collection_list` or `pc_stac_search` with a smaller scope,
- avoid live download checks when the environment is offline.

### Symptom: NAIP download fails

**Likely causes**

- wrong bbox order,
- no NAIP coverage in the requested region,
- network or signing failure,
- output path confusion.

**Fix**

- validate the bbox with the bundled smoke script,
- inspect the search results before downloading,
- use `download_naip(..., output_dir=...)` in Python when you need exact control.

### Symptom: `download_with_progress` rejects the URL

That is expected for unsupported schemes.

- Only `http` and `https` are allowed
- `ftp`, `file`, and `data:` URLs are rejected

### Symptom: STAC asset download or signed-asset read fails

**Likely causes**

- unavailable network,
- expired or inaccessible asset,
- wrong asset key,
- a local file path was passed where a STAC item or URL was expected.

**Fix**

- check `pc_item_asset_list(item)` first,
- use `read_pc_item_asset` for a single asset,
- if output is optional, inspect the returned data array before writing.

## 5) Pipeline config, step, and checkpoint issues

### Symptom: `load_pipeline` says the step type is unknown

**Likely causes**

- the config uses a step that is not registered,
- the config uses `FunctionStep`, which is not registered in the bundled JSON/YAML loader,
- the type string is misspelled.

**Repair path**

1. Run [`scripts/validate_pipeline_config.py`](../scripts/validate_pipeline_config.py) on the config.
2. Compare the reported step types with the registered list.
3. Keep only these built-in config step types in JSON/YAML:
   - `GlobStep`
   - `SemanticSegmentationStep`
   - `RasterToVectorStep`
4. If you need custom Python logic, build the pipeline in Python and register a custom `PipelineStep` subclass.

### Symptom: pipeline config parses, but checkpoint resume behaves oddly

**Likely causes**

- the config hash changed since the checkpoint was created,
- item keys changed,
- the checkpoint directory contains stale progress from another pipeline.

**Fix**

- compare the config against the checkpoint with the bundled validator using `--checkpoint`,
- delete or isolate stale checkpoints,
- keep pipeline `name` stable only when the step set and key function are intentionally unchanged.

### Symptom: `Pipeline` rejects the executor type

`Pipeline` only supports `executor_type='thread'`.

Use thread workers for GeoAI batch jobs.

### Symptom: a pipeline step fails only on one item

**Likely causes**

- bad input file,
- CRS mismatch on that item,
- missing output directory,
- unsupported band or mask shape,
- an inference or vectorization step produced partial output.

**Fix**

- re-run the item in isolation,
- inspect the input with `geoai info`,
- verify the step input key (`input_path`, `output_path`, or custom key) is actually present.

## 6) Vector/raster schema failures

### Symptom: `RasterToVectorStep` writes an empty file or very few polygons

**Likely causes**

- the mask threshold is too high,
- the raster is multi-class but the step is using the wrong band,
- the raster is not a mask-like image,
- the output path is fine but the input raster has no foreground pixels.

**Fix**

- inspect the mask values first,
- run `raster_to_vector` on a small synthetic mask,
- reduce the threshold or confirm the foreground class values.

### Symptom: `vector_to_raster` output is blank

**Likely causes**

- geometries lie outside the raster extent,
- the CRS is mismatched,
- the attribute field is missing or non-numeric,
- the burn value was overwritten by fill or nodata choices.

**Fix**

- compare bounds and CRS before rasterizing,
- use a `reference_raster` when possible,
- confirm the attribute field exists.

### Symptom: `clean_instance_mask` or `masks_to_vector` changes instance IDs unexpectedly

**Likely causes**

- the mask is semantic-class output, not instance IDs,
- the `min_area` threshold is too aggressive,
- hole-filling or smoothing is collapsing narrow objects.

**Fix**

- confirm whether the mask is semantic or instance output,
- lower the cleanup thresholds,
- test on a tiny mask crop before the full batch.

## 7) Fast repair recipes for difficult usability cases

### Unknown pipeline step repair

1. Open the config with [`scripts/validate_pipeline_config.py`](../scripts/validate_pipeline_config.py).
2. Confirm whether the raw step type exists in the registered config step list.
3. If the step is custom logic, rewrite it as a Python-built pipeline step or register a subclass.
4. Keep JSON/YAML pipeline configs limited to the registered built-in step types.

### CRS mismatch before tiling or vectorizing

1. Compare `get_raster_info(...)["crs"]` and `get_vector_info(...)["crs"]`.
2. Reproject the vector to the raster CRS before any rasterization or clipping.
3. If clipping by bbox, pass `bbox_crs` when the bbox is not already in the raster CRS.
4. Re-run the pair through [`scripts/geospatial_io_smoke.py`](../scripts/geospatial_io_smoke.py) before the full batch.

## 8) When to stop and route elsewhere

Stop this sub-skill and route out when the issue becomes:

- model architecture / checkpoint selection,
- training or label schema design,
- foundation model loading or embeddings,
- QGIS plugin or MCP integration,
- credentialed upload or external release behavior.
