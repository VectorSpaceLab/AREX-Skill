# Inference workflows

Use this guide to choose the smallest GeoAI API that matches the task.

## Quick chooser

| Situation | Start with | Why |
| --- | --- | --- |
| Unknown HF-style image task | `geoai.auto` | One entry point with geospatial I/O and task-aware model loading. |
| Local semantic-segmentation checkpoint | `geoai.train.semantic_segmentation` or `semantic_inference_on_geotiff` | Uses a local checkpoint and exposes tiled inference, thresholds, and vector output. |
| Local Mask R-CNN or detector checkpoint | `geoai.train.object_detection`, `object_detection_batch`, `instance_segmentation`, or `geoai.object_detect.multiclass_detection` | Best for local weights, batched rasters, and georeferenced box or mask outputs. |
| Text prompt segmentation | `geoai.segment.GroundedSAM`, `CLIPSegmentation`, or `geoai.sam.SamGeo` | Best when the prompt, not a labeled training set, defines the target. |
| RF-DETR | `geoai.rfdetr.rfdetr_detect` or `rfdetr_segment` | Native variant handling, tile stitching, and mask geometry for segmentation variants. |
| Water / cloud / cleanup / SR | `geoai.water.segment_water`, `geoai.tools.cloudmask.*`, `geoai.tools.multiclean.*`, `geoai.tools.sr.super_resolution` | Specialized geospatial inference backends with band-order and post-processing rules. |
| ONNX export or runtime | `geoai.onnx.export_to_onnx`, `ONNXGeoModel`, `onnx_semantic_segmentation`, `onnx_image_classification` | Good for deployment and CPU-only or lightweight environments. |

## 1) Auto HF-style image tasks

Use `geoai.auto` when the model is a Hugging Face ID or local HF checkpoint and you want the package to choose the model class.

Recommended path:

- `AutoGeoModel.from_pretrained(model_id, task=..., tile_size=..., overlap=...)`
- `AutoGeoImageProcessor.from_pretrained(model_id, use_full_processor=True)` for text+image models.
- `AutoGeoModel.predict(...)` for geospatial inference.

Supported task routes in `AutoGeoModel.from_pretrained` include:

- `semantic-segmentation`
- `image-segmentation`
- `universal-segmentation`
- `depth-estimation`
- `mask-generation`
- `object-detection`
- `zero-shot-object-detection`
- `classification`
- `image-classification`

Notes:

- `labels=[...]` is converted to a text prompt automatically for zero-shot detection.
- `AutoGeoModel.predict` tiles large rasters automatically unless the task is classification.
- `output_vector_path` is only useful when the source has CRS/transform metadata.
- `get_hf_tasks()` mirrors the installed Hugging Face pipeline task registry.
- `get_hf_model_config(model_id)` is a safe way to inspect `model_type`, `architectures`, `id2label`, and `num_labels` before loading.

## 2) Local semantic-segmentation checkpoints

Use `geoai.train.semantic_segmentation` when you already have a local checkpoint and want a GeoTIFF mask.

Suggested sequence:

1. Choose `num_channels` to match the checkpoint and source imagery.
2. Keep `window_size > overlap` and start with modest tiles such as `512/128` or `1024/128`.
3. Set `output_vector_path` when you want polygons after raster prediction.
4. Use `probability_path` and `save_class_probabilities=True` when you need threshold debugging.

Helpful wrappers:

- `semantic_inference_on_geotiff(model, ...)` when you already have a model object.
- `semantic_inference_on_image(model, ...)` for non-georeferenced images.
- `inference_on_geotiff(model, ...)` for the lower-level sliding-window helper used by the package.

## 3) Instance / object detection checkpoints

Use `geoai.train.object_detection`, `object_detection_batch`, `instance_segmentation`, `instance_segmentation_batch`, or `geoai.object_detect.multiclass_detection` when the checkpoint is detector-like and the output should be boxes or instance masks.

Tips:

- `num_channels` must match the checkpoint head and source imagery.
- `num_classes` must match the prediction head.
- `object_detection_batch` treats a single `.tif` or `.tiff` file as a file, not a directory.
- `multiclass_detection` and `batch_multiclass_detection` are the preferred route for NWPU-style multi-class detector checkpoints.
- Use `vectorize=True` or `use_mask_geometry=True` when you need georeferenced polygons rather than box outlines.

## 4) Prompt segmentation

Use `geoai.segment` or `geoai.sam.SamGeo` when the prompt defines the target.

Choose the backend like this:

- `GroundedSAM` when you want text prompts plus Grounding DINO boxes and SAM masks.
- `CLIPSegmentation` when a text prompt should produce a raster mask with the lightest prompt-segmentation path.
- `SamGeo` when you want SAM automatic masks or prompt-based point/box workflows.

Notes:

- `GroundedSAM` uses tiled inference, non-maximum suppression, and optional polygon refinement.
- `CLIPSegmentation` is the simpler text-guided mask route.
- `SamGeo(automatic=True)` is for full-image masks; `automatic=False` switches to prompt mode after `set_image()`.
- Geospatial prompts can be supplied as pixel coordinates, vectors, GeoJSON, or coordinates with a source CRS.

## 5) RF-DETR

Use `geoai.rfdetr` when the user explicitly wants RF-DETR detections or RF-DETR-Seg masks.

Recommended sequence:

1. Call `list_rfdetr_models()` to choose between detection and `seg-*` variants.
2. Use `rfdetr_detect` for detection variants and `rfdetr_segment` for segmentation variants.
3. Let `use_mask_geometry` default to `True` on `seg-*` variants unless the user wants box geometry.
4. Keep `overlap < window_size`.

Important:

- If `check_rfdetr_available()` fails, stop and report the missing optional package.
- Do not silently switch to a different detector family; RF-DETR detection and segmentation geometry are not interchangeable.
- `rfdetr_detect` returns a GeoDataFrame with geometry, class ID, class name, and confidence.
- `rfdetr_segment` can emit mask polygons and `area_pixels` for seg variants.

## 6) Water, cloud, cleanup, and super-resolution

Use specialized helpers instead of generic segmentation when the task is sensor-specific.

- `geoai.water.segment_water` for water bodies and optional vector polygons.
- `geoai.tools.cloudmask.predict_cloud_mask_from_raster` or `predict_cloud_mask_batch` for cloud and cloud-shadow masks.
- `geoai.tools.multiclean.clean_segmentation_mask` or `clean_raster` for mask cleanup before vectorization.
- `geoai.tools.sr.super_resolution` for four-band RGB+NIR super-resolution.

Band-order reminders:

- Water presets: `naip`, `sentinel2`, and `landsat`.
- Cloud masks expect explicit red, green, and NIR bands.
- Super-resolution expects exactly four bands in RGB+NIR order.

Notes:

- `super_resolution` may fetch the OpenSR config and checkpoint when run; the preflight helper only reports that requirement.
- `clean_raster` preserves geospatial metadata and is useful before vectorization.

## 7) ONNX export and runtime

Use `geoai.onnx` when you need exportable or runtime-only inference.

- `export_to_onnx` converts a local PyTorch or Hugging Face model to `.onnx` and writes a JSON sidecar.
- `ONNXGeoModel` runs inference without the original training stack.
- `onnx_semantic_segmentation` and `onnx_image_classification` are the direct convenience wrappers.

Notes:

- Keep `providers` in priority order if you want GPU first and CPU fallback second.
- The ONNX runtime path is the right choice for edge deployments or environments that cannot load the original PyTorch stack.

## Safe preflight sequence

1. Run `scripts/inference_input_check.py --help`.
2. Check the local input raster, band count, and output extension.
3. Confirm the model path or model ID, device, and optional dependency status.
4. Only then run the chosen workflow.

## Two difficult cases to rehearse

- 4-band NAIP GeoTIFF + local Mask R-CNN checkpoint: validate `num_channels=4`, local checkpoint presence, `window_size/overlap`, and a georeferenced vector output path.
- RF-DETR `seg-medium` request when the `rfdetr` extra is missing: preflight should stop at the missing package instead of trying to fall back to another detector family.
