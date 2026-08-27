# Data And Pipeline Workflows

This reference distills the GeoAI geospatial I/O and batch-pipeline surface into safe, reusable operating guidance.

## 1) Decide the workflow first

| Need | Recommended path |
| --- | --- |
| Inspect a raster or vector file | `geoai info FILEPATH` or `geoai.utils.get_raster_info` / `geoai.utils.get_vector_info` |
| Download NAIP or STAC data | `geoai.download.download_naip`, `pc_stac_search`, `pc_stac_download`, `download_pc_stac_item` |
| Download Overture Maps features | `get_all_overture_types`, `get_overture_data`, `download_overture_buildings` |
| Validate a pipeline config | [`scripts/validate_pipeline_config.py`](../scripts/validate_pipeline_config.py) |
| Run a JSON/YAML batch pipeline | `geoai pipeline run CONFIG_PATH` |
| Show a pipeline config | `geoai pipeline show CONFIG_PATH` |
| Clip / tile / mosaic / stack rasters | `clip_raster_by_bbox`, `mosaic_geotiffs`, `stack_bands`, `get_raster_resolution` |
| Rasterize vectors or vectorize masks | `vector_to_raster`, `raster_to_vector`, `masks_to_vector` |
| Check raster/vector CRS compatibility | [`scripts/geospatial_io_smoke.py`](../scripts/geospatial_io_smoke.py) |

## 2) File inspection and format validation

### Raster inspection

Start with metadata before loading large arrays.

- `get_raster_info(path)` returns driver, size, band count, dtype, CRS, transform, bounds, resolution, nodata, and per-band stats.
- `get_raster_stats(path, divide_by=...)` returns bandwise min/max/mean/std.
- `get_raster_resolution(path)` returns `(x_res, y_res)`.
- `read_raster(path, band=None, masked=True)` loads a `xarray.DataArray` and keeps geospatial metadata.
- `clip_raster_by_bbox(...)` can clip by geographic bbox or pixel window.

Use these checks when:

- a GeoTIFF opens but tiling or vectorization fails,
- a raster has no CRS or an unexpected band count,
- nodata handling changes downstream statistics,
- you need to confirm the file is safe for batch processing.

### Vector inspection

- `get_vector_info(path)` returns feature count, geometry types, CRS, bounds, and attribute stats.
- `get_vector_info_ogr(path)` is the OGR-backed alternative when GeoPandas layer handling is tricky.
- `read_vector(path, layer=None)` loads GeoJSON, Shapefile, GeoPackage, GeoParquet, GML, KML, GPX, and URLs when supported.
- `analyze_vector_attributes(path, attribute_name)` is useful for schema or class-value sanity checks.
- `geojson_to_coords`, `geojson_to_xy`, `boxes_to_vector`, and `vector_to_geojson` help convert bbox-like or GeoJSON inputs into GeoDataFrames.

### Safe format rules

- Raster operations in this sub-skill assume local geospatial files or trusted URLs.
- Vector readers accept common formats, but downstream GeoAI operations still need a valid CRS and geometry column.
- `geoai info` first uses extension hints, then falls back to raster and vector readers if the extension is unknown.

## 3) Download workflows

### NAIP

`download_naip(bbox, output_dir, year=None, max_items=10, overwrite=False, preview=False, **kwargs)`

- `bbox` must be `(minx, miny, maxx, maxy)` in EPSG:4326.
- It searches Planetary Computer NAIP items, signs assets, and downloads the `image` asset.
- It writes files under `output_dir`.
- Use `preview=True` only when you want an on-screen preview.

### Overture Maps

- `get_all_overture_types()` lists available data types.
- `get_overture_data(overture_type, bbox=None, columns=None, output=None, **kwargs)` returns a GeoDataFrame and can write to disk.
- `download_overture_buildings(...)` is a convenience wrapper that routes to `get_overture_data`.
- `convert_vector_format(input_file, output_format='geojson', filter_expression=None)` is a local format-conversion helper for already-downloaded vector data.

### Planetary Computer STAC

- `pc_collection_list(...)` lists collections and can filter/sort them.
- `pc_stac_search(collection, bbox=None, time_range=None, query=None, limit=10, max_items=None, quiet=False, endpoint=...)` returns STAC items.
- `pc_item_asset_list(item)` lists the asset keys on a STAC item.
- `read_pc_item_asset(item, asset, output=None, as_cog=True, **kwargs)` reads a single asset.
- `pc_stac_download(items, output_dir='.', assets=None, max_workers=1, skip_existing=True)` downloads assets for one or many items.
- `download_pc_stac_item(item_url, bands=None, output_dir=None, show_progress=True, merge_bands=False, merged_filename=None, overwrite=False, cell_size=None)` is the higher-level asset downloader for one STAC item.
- `view_pc_item(...)` and `view_pc_items(...)` are interactive map helpers for visual review, not core batch processing.

### Download safety notes

- `download_with_progress(url, output_path, max_size=None)` validates `http`/`https` URLs before downloading.
- The helper rejects `ftp:`, `file:`, and other unsupported URL schemes.
- The CLI `download` command is available, but the Python API is the more explicit choice when you need to control output directories and error handling precisely.

## 4) Pipeline workflows

### Pipeline architecture

`geoai.pipeline` provides:

- `PipelineStep`: base class for steps.
- `FunctionStep`: wrapper for a plain callable; useful in Python code.
- `GlobStep`: expands `input_dir` or `input_pattern` into `input_path` items.
- `SemanticSegmentationStep`: runs semantic segmentation inference.
- `RasterToVectorStep`: converts raster masks to vector output.
- `Pipeline`: executes steps sequentially or with thread workers.
- `ErrorPolicy`: `skip` or `fail`.
- `CheckpointManager`: JSON checkpoint persistence and resume.
- `load_pipeline(config_path, **overrides)`: JSON/YAML loader.
- `register_step(cls)`: registers a custom step class for config deserialization.

### Registered config step types

Only these built-in step types are registered for JSON/YAML loading:

- `GlobStep`
- `SemanticSegmentationStep`
- `RasterToVectorStep`

`FunctionStep` is a useful Python helper, but it is not config-registered in the bundled loader.

### Distilled config patterns

#### Glob-only scan

```json
{
  "name": "glob_only",
  "max_workers": 1,
  "on_error": "skip",
  "steps": [
    {
      "type": "GlobStep",
      "name": "find_images",
      "extensions": [".tif", ".tiff", ".jp2", ".img"]
    }
  ]
}
```

Use this when a pipeline only needs to expand a directory into file-level work items.

#### Semantic segmentation + vectorization

```yaml
name: semantic_segmentation
max_workers: 1
executor_type: thread
on_error: skip
steps:
  - type: GlobStep
    name: find_images
    extensions: [".tif", ".tiff"]
  - type: SemanticSegmentationStep
    name: segment
    model_path: path/to/model.pth
    architecture: unet
    encoder_name: resnet34
    num_channels: 3
    num_classes: 2
    window_size: 512
    overlap: 256
    batch_size: 4
    suffix: "_mask"
  - type: RasterToVectorStep
    name: vectorize
    output_format: ".geojson"
    input_key: output_path
    output_key: vector_path
```

Use this pattern when the batch job should create masks and then vectorize them.

#### Building extraction with simplification

```yaml
name: building_extraction
max_workers: 2
executor_type: thread
on_error: skip
steps:
  - type: GlobStep
    name: find_tiles
    extensions: [".tif", ".tiff", ".jp2"]
  - type: SemanticSegmentationStep
    name: segment_buildings
    model_path: path/to/building_model.pth
    architecture: unet
    encoder_name: resnet50
    num_channels: 3
    num_classes: 2
    window_size: 512
    overlap: 256
    batch_size: 8
    suffix: "_buildings"
  - type: RasterToVectorStep
    name: vectorize_buildings
    output_format: ".gpkg"
    simplify_tolerance: 1.0
    input_key: output_path
    output_key: vector_path
```

Use this when the output should be a cleaned vector footprint layer rather than a raw mask.

#### Batch vectorization only

```json
{
  "name": "batch_vectorize",
  "max_workers": 4,
  "executor_type": "thread",
  "on_error": "skip",
  "steps": [
    {
      "type": "GlobStep",
      "name": "find_masks",
      "extensions": [".tif"]
    },
    {
      "type": "RasterToVectorStep",
      "name": "vectorize",
      "output_format": ".gpkg",
      "input_key": "input_path",
      "output_key": "vector_path"
    }
  ]
}
```

Use this when the masks already exist and the pipeline only needs to emit vectors.

### Checkpoints and error policy

- `on_error='skip'` keeps processing other items after a failure.
- `on_error='fail'` stops at the first failure.
- `checkpoint_dir` enables JSON checkpoint files named after the pipeline.
- Checkpoints store completed/failed states plus the step names that were completed.
- The checkpoint hash changes when the pipeline config changes, so stale checkpoints are reset.
- `Pipeline` only supports `executor_type='thread'`.

### Practical config flow

1. Validate the config with [`scripts/validate_pipeline_config.py`](../scripts/validate_pipeline_config.py).
2. Confirm the input directory or item list.
3. Confirm output paths and checkpoint paths are intentional.
4. Run `geoai pipeline show CONFIG_PATH` to inspect the loaded structure.
5. Run `geoai pipeline run CONFIG_PATH ...` only after the config and inputs are clean.

## 5) Source script handling

The public data-preparation script for DC impervious surface data is reference-only because it is network-bound. Do not copy it as a runtime helper. Instead, distill its useful ideas into safe workflows:

- bbox-driven public data search,
- explicit CRS transforms before masking/clipping,
- clipping vector data to raster extent,
- writing local GeoTIFF and GeoJSON outputs,
- reprojecting vector data to the raster CRS before downstream work.

When you need the same style of workflow, compose the download and conversion helpers in this sub-skill rather than running a network-heavy source script verbatim.

## 6) Minimal safe review checklist

- Is the file a supported raster or vector format?
- Is the CRS known and aligned across inputs?
- Is the bbox order correct for the API being used?
- Does the pipeline config only use registered step types?
- Are checkpoint and output directories intentional and writable?
- Is any network access, signing, or model use actually required?
