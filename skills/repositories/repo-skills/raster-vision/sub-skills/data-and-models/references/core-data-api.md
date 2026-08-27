# Core data API

This reference covers Raster Vision's low-level geospatial data objects and the config-to-runtime path they follow.

## Mental model

- `Config` objects are pydantic-backed, typed, serializable, and validatable.
- Most configs also implement `update()` and `build()`.
- `Scene` is the runtime object that combines imagery, labels, optional prediction storage, and AOIs.
- `SceneConfig.build(class_config, tmp_dir)` is the usual bridge from serialized config to runtime scene.

## Object map

| Config / object | What it does | Common pitfalls |
| --- | --- | --- |
| `ClassConfig` | Defines class names, colors, and optional `null_class`. | `names` and `colors` must match in length; `null_class` must appear in `names`; `ensure_null_class()` adds a null class when needed. |
| `DatasetConfig` | Holds train / validation / test `SceneConfig` lists plus optional `scene_groups`. | Scene ids must be unique across splits; `scene_groups` may only contain ids that exist in the dataset. |
| `SceneConfig` | Describes one scene: `raster_source`, optional `label_source`, optional `label_store`, and optional `aoi_uris`. | AOIs must be Polygon / MultiPolygon GeoJSON in EPSG:4326; label objects are matched to the raster bbox during scene construction. |
| `RasterioSourceConfig` | Reads GeoTIFFs, VRTs, or other Rasterio/GDAL-readable imagery. | `channel_order` must stay within the raw band count; multiple URIs may be mosaicked; alpha bands are skipped automatically when no order is given. |
| `GeoJSONVectorSourceConfig` | Reads vector labels from GeoJSON and applies vector transformers. | GeoJSON should already be in map coords; task-specific label configs often need `class_id` on features. |
| `RasterizedSourceConfig` | Converts a vector source into a raster label source. | It auto-inserts class-inference and line/point buffer transformers when they are absent. |
| `SemanticSegmentationLabelSourceConfig` | Wraps a raster or rasterized source as segmentation labels. | Use raster labels or rasterized vectors; the null class fills off-edge gaps. |
| `ObjectDetectionLabelSourceConfig` | Wraps a vector source as detection boxes. | Expects label features with `class_id`; points and lines must be buffered into polygons. |
| `ChipClassificationLabelSourceConfig` | Reads or infers chip-level class labels from vectors. | `infer_cells=True` requires `background_class_id`; `cell_sz` is often filled from pipeline chip options. |
| `SemanticSegmentationLabelStoreConfig` | Stores segmentation predictions on disk. | Can emit `labels.tif`, `scores.tif`, `pixel_hits.npy`, and vector outputs; incompatible pre-existing score files raise errors. |
| `ObjectDetectionGeoJSONStoreConfig` / `ChipClassificationGeoJSONStoreConfig` | Stores predicted detections or chip labels as GeoJSON. | `uri` is usually auto-generated inside a pipeline, but manual use must supply a writable path. |

## Transformers and label adapters

### Raster transformers

Common raster-side transformers include:
- `StatsTransformer` for dataset statistics-driven normalization
- `MinMaxTransformer` for scaling to a range useful for Albumentations
- `CastTransformer` for dtype conversion
- `NanTransformer`, `ReclassTransformer`, and `RGBClassTransformer` for specialized preprocessing

A practical rule: if an Albumentations transform expects `uint8`, add a raster transformer that makes the image compatible before the dataset sees it.

### Vector transformers

Common vector-side transformers include:
- `ClassInferenceTransformer` for filling missing `class_id` values
- `BufferTransformer` for turning points or lines into polygons
- `ShiftTransformer` for coordinate shifts

`RasterizedSourceConfig`, `ObjectDetectionLabelSourceConfig`, and `ChipClassificationLabelSourceConfig` all rely on these transformers to adapt GeoJSON into task-ready labels.

## Runtime workflow

1. Build a `ClassConfig`.
2. Build a `SceneConfig`.
3. Call `SceneConfig.build(class_config, tmp_dir)` to get a runtime `Scene`.
4. Assemble a `DatasetConfig` from `SceneConfig` objects when training or evaluation needs train/valid/test splits.
5. Feed the runtime scene into `GeoDataset`, `Learner`, or `ScenePredictor` / `Predictor` depending on the task.

## Convenience scene builders

When an agent only needs a common task scene and does not need every low-level config, the source library also exposes convenience builders that assemble scenes from URIs and configs:
- `make_ss_scene`
- `make_cc_scene`
- `make_od_scene`

Use the manual config path when the task needs explicit control over AOIs, transformers, rasterization, or label storage.

## Bundle-backed prediction

- `Predictor(model_bundle_uri, tmp_dir, update_stats=False, channel_order=None, scene_group=None)` is the low-level batch predictor for one bundle and many image URIs.
- `ScenePredictor(model_bundle_uri, predict_options=None, tmp_dir=None)` takes a `SceneConfig`, builds a `Scene`, and writes predictions into the scene's label store.
- Model bundles keep the training-time scene stats, raster transforms, and band order. Override `channel_order` when the target imagery does not match the bundle's original assumptions.

## Evaluators and analyzers

- Analyzers gather dataset-level statistics for downstream use.
- Evaluators compare validation labels against predictions and emit task metrics.
- They are usually pipeline-owned; for direct library work, keep them in mind as downstream consumers of the scene and label stack.
