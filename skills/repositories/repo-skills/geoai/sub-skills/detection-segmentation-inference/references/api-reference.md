# API reference

This page lists the public entry points that matter for inference routing.

## geoai.auto

**Processor and model wrappers**

- `AutoGeoImageProcessor.from_pretrained(pretrained_model_name_or_path, device=None, use_full_processor=False, **kwargs)`
- `AutoGeoImageProcessor.load_geotiff(source, window=None, bands=None) -> (array, metadata)`
- `AutoGeoImageProcessor.load_image(source, window=None, bands=None) -> (array, metadata|None)`
- `AutoGeoImageProcessor.prepare_for_model(data, normalize=True, to_rgb=True, percentile_clip=True, return_tensors='pt')`
- `AutoGeoImageProcessor.save_geotiff(data, output_path, metadata, dtype=None, compress='lzw', nodata=None)`

- `AutoGeoModel.TASK_MODEL_MAPPING`
  - `semantic-segmentation`
  - `image-segmentation`
  - `universal-segmentation`
  - `depth-estimation`
  - `mask-generation`
  - `object-detection`
  - `zero-shot-object-detection`
  - `classification`
  - `image-classification`

- `AutoGeoModel.from_pretrained(pretrained_model_name_or_path, task=None, device=None, tile_size=1024, overlap=128, **kwargs)`
- `AutoGeoModel.predict(source, output_path=None, output_vector_path=None, window=None, bands=None, threshold=0.5, text=None, labels=None, box_threshold=0.3, text_threshold=0.25, min_object_area=100, simplify_tolerance=1.0, batch_size=1, return_probabilities=False, **kwargs)`
- `AutoGeoModel.mask_to_vector(mask, metadata, threshold=0.5, min_object_area=100, max_object_area=None, simplify_tolerance=1.0)`
- `AutoGeoModel.save_geotiff(data, output_path, metadata, dtype=None, compress='lzw', nodata=None)`
- `AutoGeoModel.save_vector(gdf, output_path, driver=None)`

**Convenience functions**

- `semantic_segmentation(input_path, output_path, model_name='nvidia/segformer-b0-finetuned-ade-512-512', output_vector_path=None, threshold=0.5, tile_size=1024, overlap=128, min_object_area=100, simplify_tolerance=1.0, device=None, **kwargs)`
- `depth_estimation(input_path, output_path, model_name='depth-anything/Depth-Anything-V2-Small-hf', tile_size=1024, overlap=128, device=None, **kwargs)`
- `image_classification(input_path, model_name='google/vit-base-patch16-224', device=None, **kwargs)`
- `object_detection(input_path, text=None, labels=None, model_name='IDEA-Research/grounding-dino-base', output_vector_path=None, box_threshold=0.3, text_threshold=0.25, device=None, **kwargs)`
- `get_hf_tasks() -> list[str]`
- `get_hf_model_config(model_id) -> dict`
- `show_image(...)`
- `show_detections(...)`
- `show_segmentation(...)`
- `show_depth(...)`

**Notes**

- `object_detection()` switches to zero-shot detection for Grounding DINO / OWL-style model names.
- `get_hf_tasks()` reflects the installed Hugging Face pipeline registry.
- `get_hf_model_config()` is a safe way to inspect the model config before loading weights.

## geoai.train inference helpers

**Low-level tiled inference**

- `inference_on_geotiff(model, geotiff_path, output_path, window_size=512, overlap=256, confidence_threshold=0.5, batch_size=4, num_channels=3, device=None, **kwargs) -> (output_path, seconds)`

**Semantic segmentation**

- `semantic_inference_on_geotiff(model, geotiff_path, output_path, window_size=512, overlap=256, batch_size=4, num_channels=3, num_classes=2, device=None, probability_path=None, probability_threshold=None, save_class_probabilities=False, quiet=False, **kwargs) -> (output_path, seconds)`
- `semantic_inference_on_image(model, image_path, output_path, window_size=512, overlap=256, batch_size=4, num_channels=3, num_classes=2, device=None, binary_output=True, probability_path=None, probability_threshold=None, save_class_probabilities=False, quiet=False, **kwargs) -> (output_path, seconds)`
- `semantic_segmentation(input_path, output_path, model_path, architecture='unet', encoder_name='resnet34', num_channels=3, num_classes=2, window_size=512, overlap=256, batch_size=4, device=None, probability_path=None, probability_threshold=None, save_class_probabilities=False, quiet=False, **kwargs) -> dict`

**Instance / object detection**

- `object_detection(input_path, output_path, model_path, window_size=512, overlap=256, confidence_threshold=0.5, batch_size=4, num_channels=3, num_classes=2, model=None, pretrained=True, device=None, **kwargs)`
- `object_detection_batch(input_paths, output_dir, model_path, filenames=None, window_size=512, overlap=256, confidence_threshold=0.5, batch_size=4, model=None, num_channels=3, num_classes=2, pretrained=True, device=None, **kwargs)`
- `instance_segmentation(input_path, output_path, model_path, window_size=512, overlap=256, confidence_threshold=0.5, nms_threshold=0.3, batch_size=4, num_channels=3, num_classes=2, class_names=None, vectorize=False, vector_path=None, use_mask_geometry=True, simplify_tolerance=0.0, device=None, **kwargs)`
- `instance_segmentation_batch(...)`
- `multiclass_detection(input_path, output_path, model_path=None, model_name=None, num_classes=11, class_names=None, window_size=512, overlap=256, confidence_threshold=0.5, nms_threshold=0.3, batch_size=4, num_channels=3, device=None, repo_id=None, **kwargs)`
- `multiclass_detection_inference_on_geotiff(model, geotiff_path, output_path, class_names=None, window_size=512, overlap=256, confidence_threshold=0.5, nms_threshold=0.3, batch_size=4, num_channels=3, device=None, **kwargs) -> (output_path, seconds, detections)`

**Support functions**

- `download_model_from_hf(model_path, repo_id=None) -> str`
- `get_detection_model(model_name='fasterrcnn_resnet50_fpn_v2', num_classes=2, num_channels=3, pretrained=True)`
- `model_has_masks(model_name) -> bool`

**Notes**

- `object_detection_batch` resolves a single file path differently from a directory.
- These helpers can still be remote-backed if `model_path` is missing or if a Hugging Face model ID is used.

## geoai.segment

- `BoundingBox(xmin, ymin, xmax, ymax)`
  - `xyxy` property returns `[xmin, ymin, xmax, ymax]`
- `DetectionResult(score, label, box, mask=None)`
  - `from_dict(detection_dict)` builds the dataclass from a detector output dict.
- `GroundedSAM(detector_id='IDEA-Research/grounding-dino-tiny', segmenter_id='facebook/sam-vit-base', device=None, tile_size=1024, overlap=128, threshold=0.3)`
- `GroundedSAM.segment_image(input_path, output_path, text_prompts, polygon_refinement=False, export_boxes=False, export_polygons=True, smoothing_sigma=1.0, nms_threshold=0.5, min_polygon_area=50, simplify_tolerance=2.0)`
- `GroundedSAM.segment_image_batch(input_paths, output_dir, text_prompts, ...)`
- `CLIPSegmentation(model_name='CIDAS/clipseg-rd64-refined', device=None, tile_size=512, overlap=32)`
- `CLIPSegmentation.segment_image(input_path, output_path, text_prompt, threshold=0.5, smoothing_sigma=1.0)`
- `CLIPSegmentation.segment_image_batch(input_paths, output_dir, text_prompt, ...)`

**Notes**

- `GroundedSAM` combines Grounding DINO detections with SAM masks.
- `CLIPSegmentation` is the text-prompt-only segmentation route.

## geoai.sam.SamGeo

- `SamGeo(model='facebook/sam-vit-huge', automatic=True, device=None, sam_kwargs=None, **kwargs)`
- `generate(source, output=None, foreground=True, erosion_kernel=None, mask_multiplier=255, unique=True, min_size=0, max_size=None, output_args=None, **kwargs)`
- `generate_batch(inputs, output_dir=None, suffix='_masks', foreground=True, erosion_kernel=None, mask_multiplier=255, unique=True, min_size=0, max_size=None, output_args=None, **kwargs)`
- `set_image(image, **kwargs)`
- `save_prediction(output, index=None, mask_multiplier=255, dtype=np.float32, vector=None, simplify_tolerance=None, **kwargs)`
- `predict(point_coords=None, point_labels=None, boxes=None, point_crs=None, mask_input=None, multimask_output=True, return_logits=False, output=None, index=None, mask_multiplier=255, dtype='float32', return_results=False, **kwargs)`
- `tensor_to_numpy(index=None, output=None, mask_multiplier=255, dtype='uint8', save_args=None)`

**Notes**

- `automatic=True` uses SAM mask generation.
- `automatic=False` switches to prompt mode after `set_image()`.
- `predict()` accepts point prompts, boxes, GeoJSON/vector inputs, and CRS-aware coordinates.

## geoai.object_detect

- `multiclass_detection(...)`
- `batch_multiclass_detection(...)`
- `multiclass_detection_inference_on_geotiff(...)`
- `predict_detector_from_hub(...)`
- `visualize_multiclass_detections(...)`
- `detections_to_geodataframe(...)`
- `download_nwpu_vhr10_model(...)`

**Notes**

- `multiclass_detection` and `batch_multiclass_detection` are the main inference routes for detector checkpoints.
- `predict_detector_from_hub` and `download_nwpu_vhr10_model` are remote-backed and may require network/cache access.
- Keep NWPU dataset prep and detector training out of this sub-skill.

## geoai.rfdetr

- `RFDETR_MODELS` registry for `base`, `nano`, `small`, `medium`, `large`, `seg-nano`, `seg-small`, `seg-medium`, `seg-large`, `seg-xlarge`, `seg-2xlarge`
- `check_rfdetr_available()`
- `list_rfdetr_models() -> dict[str, str]`
- `rfdetr_detect(input_path, output_path=None, model_variant='base', pretrain_weights=None, confidence_threshold=0.5, nms_threshold=0.3, window_size=None, overlap=None, batch_size=4, class_names=None, use_mask_geometry=None, simplify_tolerance=0.0, device=None, **kwargs)`
- `rfdetr_segment(input_path, output_path=None, model_variant='seg-medium', pretrain_weights=None, confidence_threshold=0.5, nms_threshold=0.3, window_size=None, overlap=None, batch_size=4, class_names=None, simplify_tolerance=0.0, device=None, **kwargs)`
- `rfdetr_detect_batch(...)`
- `rfdetr_detect_from_hub(...)`
- `rfdetr_train(...)`
- `push_rfdetr_to_hub(...)`
- `prepare_nwpu_for_rfdetr(...)`
- `plot_rfdetr_metrics(...)`

**Notes**

- `seg-*` variants can emit mask geometry and `area_pixels`.
- `check_rfdetr_available()` should be used before any RF-DETR route.
- Training and dataset-preparation helpers are outside the inference sub-skill.

## geoai.water

- `BAND_ORDER_PRESETS = {'naip': [1, 2, 3, 4], 'sentinel2': [3, 2, 1, 4], 'landsat': [4, 3, 2, 5]}`
- `segment_water(input_path, band_order='naip', output_raster=None, output_vector=None, batch_size=4, device=None, dtype='float32', no_data_value=0, patch_size=1000, overlap_size=300, use_osm_water=True, use_osm_building=True, use_osm_roads=True, cache_dir=None, model_dir=None, overwrite=True, min_size=10, smooth=True, smooth_iterations=3, verbose=True, **kwargs)`

**Notes**

- `segment_water` returns a raster path or GeoDataFrame depending on `output_vector`.
- `band_order` can be a preset name or a 4-element index list.

## geoai.tools.cloudmask

- `check_omnicloudmask_available()`
- `predict_cloud_mask(image, batch_size=1, inference_device=None, inference_dtype='fp32', patch_size=1000, export_confidence=False, model_version=None)`
- `predict_cloud_mask_from_raster(input_path, output_path, red_band=1, green_band=2, nir_band=3, batch_size=1, inference_device=None, inference_dtype='fp32', patch_size=1000, export_confidence=False, model_version=None)`
- `predict_cloud_mask_batch(input_paths, output_dir, red_band=1, green_band=2, nir_band=3, batch_size=1, inference_device='cpu', inference_dtype='fp32', patch_size=1000, export_confidence=False, model_version=3, suffix='_cloudmask', verbose=True)`
- `calculate_cloud_statistics(mask)`
- `create_cloud_free_mask(mask, include_thin_clouds=False, include_shadows=False)`

**Notes**

- `predict_cloud_mask` expects a 3-channel R/G/NIR image in CHW or HWC layout.
- Outputs use class codes 0-3 for clear, thick cloud, thin cloud, and cloud shadow.

## geoai.tools.multiclean

- `check_multiclean_available()`
- `clean_segmentation_mask(mask, class_values=None, smooth_edge_size=2, min_island_size=100, connectivity=8, max_workers=None, fill_nan=False)`
- `clean_raster(input_path, output_path, class_values=None, smooth_edge_size=2, min_island_size=100, connectivity=8, max_workers=None, fill_nan=False, band=1, nodata=None)`
- `clean_raster_batch(input_paths, output_dir, class_values=None, smooth_edge_size=2, min_island_size=100, connectivity=8, max_workers=None, fill_nan=False, band=1, suffix='_cleaned', verbose=True)`
- `compare_masks(original, cleaned) -> (removed_pixels, kept_pixels, change_ratio)`

**Notes**

- `clean_segmentation_mask` expects a 2D array.
- `connectivity` must be 4 or 8.
- `clean_raster` preserves geospatial metadata and nodata where possible.

## geoai.tools.sr

- `load_image_tensor(image_path, device, bands, window=None, scale_factor=10000.0)`
- `super_resolution(input_lr_path, output_sr_path, output_uncertainty_path=None, rgb_nir_bands=[1, 2, 3, 4], sampling_steps=100, n_variations=25, scale=4, compute_uncertainty=False, window=None, scale_factor=10000.0, patch_size=128, overlap=16)`
- `save_geotiff(data, reference_profile, output_path, scale=4)`
- `plot_sr_comparison(lr_path, sr_path, bands=[1, 2, 3], lr_vmax=None, sr_vmax=None, figsize=(14, 7), **kwargs)`
- `plot_sr_uncertainty(uncertainty_path, cmap='RdYlGn_r', normalize=True, figsize=(8, 8), **kwargs)`

**Notes**

- `rgb_nir_bands` must contain exactly four integers.
- `compute_uncertainty=True` requires `output_uncertainty_path`.
- `n_variations` must be greater than 3 when uncertainty is requested.
- `patch_size > 0` and `0 <= overlap < patch_size`.
- The workflow uses the OpenSR latent diffusion backend and may fetch weights when actually run.

## geoai.onnx

- `_check_onnx_deps()`
- `export_to_onnx(model_name_or_path, output_path, task=None, input_height=512, input_width=512, input_channels=3, opset_version=17, dynamic_axes=None, simplify=True, device=None, **kwargs)`
- `ONNXGeoModel(model_path, task=None, providers=None, tile_size=1024, overlap=128, metadata=None)`
- `onnx_semantic_segmentation(input_path, output_path, model_path, output_vector_path=None, threshold=0.5, tile_size=1024, overlap=128, min_object_area=100, simplify_tolerance=1.0, providers=None, **kwargs)`
- `onnx_image_classification(input_path, model_path, providers=None, **kwargs)`
- `ONNXGeoModel.load_geotiff(...)`
- `ONNXGeoModel.load_image(...)`
- `ONNXGeoModel.predict(...)`
- `ONNXGeoModel.mask_to_vector(...)`
- `ONNXGeoModel.save_vector(...)`

**Notes**

- `export_to_onnx` writes a JSON sidecar with task and label metadata.
- `ONNXGeoModel` supports semantic segmentation, image classification, object detection, and depth estimation.
