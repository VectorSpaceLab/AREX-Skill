# Data formats

This reference is a cheat sheet for the serialized configs and file formats that appear most often in Raster Vision data/model workflows.

## Config `type_hint` cheat sheet

| Config | `type_hint` |
| --- | --- |
| `ClassConfig` | `class_config` |
| `DatasetConfig` | `dataset` |
| `SceneConfig` | `scene` |
| `RasterioSourceConfig` | `rasterio_source` |
| `GeoJSONVectorSourceConfig` | `geojson_vector_source` |
| `RasterizedSourceConfig` | `rasterized_source` |
| `SemanticSegmentationLabelSourceConfig` | `semantic_segmentation_label_source` |
| `ObjectDetectionLabelSourceConfig` | `object_detection_label_source` |
| `ChipClassificationLabelSourceConfig` | `chip_classification_label_source` |
| `SemanticSegmentationLabelStoreConfig` | `semantic_segmentation_label_store` |
| `ObjectDetectionGeoJSONStoreConfig` | `object_detection_geojson_store` |
| `ChipClassificationGeoJSONStoreConfig` | `chip_classification_geojson_store` |
| `WindowSamplingConfig` | `window_sampling` |
| `LearnerConfig` | `learner` |
| `DataConfig` | `data` |
| `GeoDataConfig` | `geo_data` |

## Scene and dataset JSON shape

A serialized `SceneConfig` usually contains:
- `id`
- `raster_source`
- optional `label_source`
- optional `label_store`
- optional `aoi_uris`

A serialized `DatasetConfig` contains:
- `class_config`
- `train_scenes`
- `validation_scenes`
- optional `test_scenes`
- optional `scene_groups`

The `SceneConfig` JSON is the right unit for the bundled scene checker script. It is not the same thing as a full pipeline config.

## Raster input formats

### `RasterioSourceConfig`

Common inputs:
- GeoTIFF
- VRT
- other Rasterio / GDAL-readable imagery

Useful fields:
- `uris`: one URI or a list of URIs
- `channel_order`: subset / reorder bands
- `transformers`: raster transforms such as stats-based normalization
- `bbox`: pixel-space crop
- `allow_streaming`: use remote streaming rather than downloading first

Notes:
- multiple URIs may be mosaicked together
- omitted `channel_order` lets Raster Vision choose the usable non-alpha bands
- `channel_order` values must stay within the raw band count

### Prechipped image datasets

`ImageDataConfig` subclasses expect directory or zip layouts.

**Classification**
- `train/<class_name>/*`
- `valid/<class_name>/*`
- optional `test/<class_name>/*`

**Semantic segmentation**
- `train/img/*`
- `train/labels/*`
- `valid/img/*`
- `valid/labels/*`
- optional `test/img/*`
- optional `test/labels/*`

**Object detection**
- `train/img/*`
- `train/labels.json`
- same pattern for `valid` and optional `test`
- annotations use COCO-style records

## Vector and label formats

### `GeoJSONVectorSourceConfig`

Expected input is GeoJSON, usually a `FeatureCollection`.

Common conventions:
- polygons and multipolygons are the safest geometry types
- `class_id` is required for object detection and chip classification features unless a class-inference transformer fills it in
- points and lines should be buffered into polygons before they reach label sources that expect polygons

### AOIs

AOI URIs should point to GeoJSON polygon / multipolygon files.
They are interpreted in EPSG:4326 and converted to the scene's pixel coordinates during scene construction.

### `RasterizedSourceConfig`

This is the bridge from vector labels to raster labels.
It takes:
- a `vector_source`
- a `rasterizer_config` with `background_class_id` and `all_touched`

It can rasterize polygons into class-id rasters for semantic segmentation workflows.

### Label source conventions

- semantic segmentation can read raster labels or rasterized vector labels
- object detection reads vector labels into boxes
- chip classification can read vectors directly or infer a cell grid from them

## Prediction output formats

### Semantic segmentation

`SemanticSegmentationLabelStore` can write:
- `labels.tif` for discrete class ids
- `scores.tif` for smooth scores
- `pixel_hits.npy` for score accumulation metadata
- `vector_outputs/` for per-class GeoJSON vectorizations

If `rgb=True`, the raster output uses the class colors from `ClassConfig`.

### Object detection and chip classification

Their GeoJSON stores write prediction GeoJSON files, typically one file per scene.

## Common format mismatches

- AOIs supplied in projected coordinates instead of EPSG:4326
- GeoJSON features missing `class_id`
- line / point features passed to polygon-only label flows
- class counts and color counts that do not match
- label rasters with the wrong band count or dtype for the chosen label-store mode
