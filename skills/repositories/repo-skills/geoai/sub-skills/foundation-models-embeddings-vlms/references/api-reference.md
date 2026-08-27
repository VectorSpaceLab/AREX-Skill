# API reference

API shapes below were confirmed from GeoAI source, the installed API inspection snapshot, and native tests. They are grouped by workflow family and trimmed to the entry points this sub-skill should route or explain.

## Foundation model registry

| Callable | Signature | Notes |
| --- | --- | --- |
| `list_foundation_models` | `list_foundation_models(category=None, modality=None, task=None, terratorch_only=False, huggingface_only=False, as_dataframe=True, verbose=True)` | Returns a DataFrame by default. Use for discovery, filtering, and registry browsing. |
| `get_foundation_model_info` | `get_foundation_model_info(name)` | Returns a copy of one registry entry. Use the lower-case GeoAI key. |
| `check_terratorch_available` | `check_terratorch_available()` | Strict boolean probe for the TerraTorch optional dependency. |
| `load_foundation_model` | `load_foundation_model(name, pretrained=True, **kwargs)` | Loads a TerraTorch backbone only when the registry entry supports it. Raises if TerraTorch is missing or the model is unsupported. |

Registry metadata fields include `name`, `abbreviation`, `category`, `modality`, `tasks`, `backbone`, `publication`, `year`, `paper_url`, `code_url`, `huggingface_id`, `license`, `terratorch_supported`, `terratorch_key`, and `description`.

## Embedding datasets and operations

| Callable | Signature | Notes |
| --- | --- | --- |
| `list_embedding_datasets` | `list_embedding_datasets(kind=None, as_dataframe=True, verbose=True)` | Filters patch or pixel datasets. |
| `load_embedding_dataset` | `load_embedding_dataset(name, root=None, paths=None, transforms=None, **kwargs)` | Patch datasets want `root`; pixel datasets want `paths`. |
| `get_embedding_info` | `get_embedding_info(name)` | Returns dataset metadata copy. |
| `extract_patch_embeddings` | `extract_patch_embeddings(dataset, max_samples=None, device=None)` | Returns embeddings plus optional `x`, `y`, `t` arrays. |
| `extract_pixel_embeddings` | `extract_pixel_embeddings(dataset, sampler=None, num_samples=100, size=256, flatten=True)` | Uses a TorchGeo sampler for pixel datasets. |
| `visualize_embeddings` | `visualize_embeddings(embeddings, labels=None, label_names=None, method='pca', n_components=2, figsize=(8, 8), cmap='tab10', alpha=0.6, s=5, title=None, save_path=None, **kwargs)` | 2D visualization for existing embeddings. |
| `plot_embedding_vector` | `plot_embedding_vector(embedding, title='Embedding Vector', figsize=(10, 3), save_path=None)` | One vector at a time. |
| `plot_embedding_raster` | `plot_embedding_raster(image, method='pca', figsize=(8, 8), title='Embedding Visualization', save_path=None)` | Raster embedding visualization helper. |
| `cluster_embeddings` | `cluster_embeddings(embeddings, n_clusters=10, method='kmeans', random_state=42, **kwargs)` | No model weights needed; works on arrays. |
| `embedding_similarity` | `embedding_similarity(query, embeddings, metric='cosine', top_k=10)` | Ranking-style nearest-neighbor lookup. |
| `train_embedding_classifier` | `train_embedding_classifier(train_embeddings, train_labels, val_embeddings=None, val_labels=None, method='knn', label_names=None, verbose=True, **kwargs)` | Lightweight baseline on precomputed features. |
| `compare_embeddings` | `compare_embeddings(embeddings_a, embeddings_b, metric='cosine')` | Pairwise comparison between two equally shaped embedding sets. |
| `embedding_to_geotiff` | `embedding_to_geotiff(embeddings, bounds, output_path, crs='EPSG:4326')` | Exports dense features as a multi-band GeoTIFF. |
| `download_google_satellite_embedding` | `download_google_satellite_embedding(bbox, output_dir='.', years=None, bands=None, resolution=10.0, crs='EPSG:4326', dequantize=True, overwrite=False)` | Networked AlphaEarth/Google satellite embedding download; not a safe default action. |

Embedding dataset keys confirmed in construction: `clay`, `major_tom`, `earth_index`, `earth_embeddings`, `copernicus_embed`, `presto`, `tessera`, `google_satellite`, `embedded_seamless`.

## DINOv3 and DINOv3 fine-tune boundary

| Callable | Signature | Notes |
| --- | --- | --- |
| `DINOv3GeoProcessor` | `DINOv3GeoProcessor(model_name='dinov3_vitl16', weights_path=None, device=None)` | Similarity-analysis processor. `weights_path` keeps offline or cached workflows explicit. |
| `create_similarity_map` | `create_similarity_map(input_image, query_coords, output_dir, model_name='dinov3_vitl16', weights_path=None, window=None, bands=None, target_size=896, save_features=False, coord_crs=None, use_interpolation=True)` | Primary similarity-map wrapper. |
| `analyze_image_patches` | `analyze_image_patches(input_image, query_points, output_dir, model_name='dinov3_vitl16', weights_path=None)` | Batch patch analysis wrapper. |
| `visualize_similarity_results` | `visualize_similarity_results(input_image, query_coords, output_dir=None, model_name='dinov3_vitl16', weights_path=None, figsize=(15, 6), colormap='turbo', alpha=0.7, save_path=None, show_query_point=True, overlay=False, target_size=896, coord_crs=None, use_interpolation=True)` | Render overlay/result images. |
| `coords_to_xy` | `coords_to_xy(src_fp, coords, coord_crs='epsg:4326', return_out_of_bounds=False, **kwargs)` | Utility for coordinate conversion. |
| `get_device` | `get_device()` | Shared device selector used by several modules. |

DINOv3 fine-tuning surfaces are exposed by `geoai.dinov3_finetune`:

- `DINOv3SegmentationDataset(image_paths, mask_paths, patch_size=16, target_size=None, num_channels=3, transform=None)`
- `DINOv3Segmenter(model_name='dinov3_vitl16', weights_path=None, num_classes=2, decoder_features=256, learning_rate=0.0001, weight_decay=0.0001, freeze_backbone=True, use_lora=False, lora_rank=4, lora_alpha=None, loss_fn=None, class_weights=None, ignore_index=255, num_channels=3, normalize_input=True)`
- `train_dinov3_segmentation(...)`
- `dinov3_segment_geotiff(...)`

Treat those as a handoff boundary to the training sub-skill when the user wants fit/evaluate workflows instead of similarity inference.

## Prithvi EO 2.0

| Callable | Signature | Notes |
| --- | --- | --- |
| `AVAILABLE_MODELS` | list of loader names | Includes the six Prithvi EO 2.0 family names. |
| `get_available_prithvi_models` | `get_available_prithvi_models()` | Returns a copy of `AVAILABLE_MODELS`. |
| `load_prithvi_model` | `load_prithvi_model(model_name='Prithvi-EO-2.0-300M-TL', device=None, cache_dir=None)` | Returns a `PrithviProcessor`. Downloads config/checkpoint unless paths are supplied. |
| `prithvi_inference` | `prithvi_inference(file_paths, output_dir='output', model_name='Prithvi-EO-2.0-300M-TL', mask_ratio=None, device=None)` | Convenience wrapper for multi-file inference. |
| `PrithviProcessor` | `PrithviProcessor(model_name='Prithvi-EO-2.0-300M-TL', config_path=None, checkpoint_path=None, device=None, cache_dir=None)` | Loads `config.json` and a checkpoint file. |

Important methods on `PrithviProcessor`:

- `download_model(model_name='Prithvi-EO-2.0-300M-TL', cache_dir=None) -> (config_path, checkpoint_path)`
- `read_geotiff(file_path) -> (image, meta, coords)`
- `preprocess_image(img, indices=None)`
- `load_images(file_paths, indices=None)`
- `process_images(file_paths, mask_ratio=None, indices=None)`
- `run_inference(input_data, temporal_coords=None, location_coords=None, mask_ratio=None)`
- `process_files(file_paths, output_dir, mask_ratio=None, indices=None)`

## UniverSat

| Callable | Signature | Notes |
| --- | --- | --- |
| `load_universat_model` | `load_universat_model(pretrained=True, size='base', device=None, eval_mode=True, model_name_or_path='g-astruc/UniverSat', **kwargs)` | Loads the UniverSat backbone. |
| `UniverSatProcessor` | `UniverSatProcessor(model=None, model_name_or_path='g-astruc/UniverSat', device=None, eval_mode=True, pretrained=True, size='base')` | GeoTIFF and modality-aware processor. |
| `universat_inference` | `universat_inference(samples, patch_size=40.0, output_grid=None, device=None, **kwargs)` | Wrapper around processor encoding. |
| `get_tile_embedding` | `get_tile_embedding(tokens)` | Mean-pools tokens into one tile vector. |
| `get_pca_rgb` | `get_pca_rgb(tokens, is_batch=None)` | Projects token grids to RGB for inspection. |
| `universat_train` | `universat_train(experiment, overrides=None, project_root=None)` | Direct training handoff; not a generic runtime helper. |

`UniverSatProcessor` methods of interest:

- `read_geotiff(file_path)`
- `preprocess_image(img, mod, scale=None)`
- `format_batch(samples, scales=None)`
- `encode_raster(samples, patch_size=40.0, output_grid=None, normalize_scales=None, **kwargs)`

## TESSERA and AlphaEarth

| Callable | Signature | Notes |
| --- | --- | --- |
| `TESSERA_EMBEDDING_DIM` | `128` | TESSERA output channel count. |
| `_check_geotessera` | `_check_geotessera()` | Raises an informative error if `geotessera` is missing. |
| `tessera_download` | `tessera_download(bbox=None, lon=None, lat=None, year=2024, output_dir='./tessera_output', output_format='tiff', bands=None, compress='lzw', region_file=None, dataset_version='v1', **kwargs)` | Networked download/export helper. |
| `tessera_fetch_embeddings` | `tessera_fetch_embeddings(bbox, year=2024, bands=None, dataset_version='v1', **kwargs)` | Returns embeddings in memory. |
| `tessera_coverage` | `tessera_coverage(year=None, output_path='tessera_coverage.png', region_bbox=None, region_file=None, tile_color='red', tile_alpha=0.6, width_pixels=2000, show_countries=True, dataset_version='v1', **kwargs)` | Coverage planning helper. |
| `tessera_visualize_rgb` | `tessera_visualize_rgb(geotiff_dir, bands=(0, 1, 2), output_path=None, normalize=True, figsize=(12, 8), title=None, **kwargs)` | Visualizes existing GeoTIFFs. |
| `tessera_tile_count` | `tessera_tile_count(bbox, year=2024, dataset_version='v1', **kwargs)` | Quick size estimate. |
| `tessera_available_years` | `tessera_available_years(dataset_version='v1', **kwargs)` | Lists available years. |
| `tessera_sample_points` | `tessera_sample_points(points, year=2024, embeddings_dir=None, auto_download=True, dataset_version='v1', **kwargs)` | Samples point locations from existing or downloaded embeddings. |

AlphaEarth/Google satellite embeddings are exposed through `download_google_satellite_embedding()` and the `google_satellite` embedding dataset.

## Moondream

| Callable | Signature | Notes |
| --- | --- | --- |
| `MoondreamGeo` | `MoondreamGeo(model_name='vikhyatk/moondream2', revision=None, device=None, compile_model=False, **kwargs)` | Main geospatial VLM wrapper. |
| `moondream_caption` | `moondream_caption(source, model_name='vikhyatk/moondream2', revision=None, length='normal', bands=None, device=None, **kwargs)` | Captioning wrapper. |
| `moondream_query` | `moondream_query(question, source=None, model_name='vikhyatk/moondream2', revision=None, reasoning=None, bands=None, device=None, **kwargs)` | VQA wrapper. |
| `moondream_detect` | `moondream_detect(source, object_type, model_name='vikhyatk/moondream2', revision=None, output_path=None, bands=None, device=None, **kwargs)` | Object grounding wrapper. |
| `moondream_point` | `moondream_point(source, object_description, model_name='vikhyatk/moondream2', revision=None, output_path=None, bands=None, device=None, **kwargs)` | Point grounding wrapper. |
| `moondream_caption_sliding_window` | `moondream_caption_sliding_window(source, window_size=512, overlap=64, length='normal', model_name='vikhyatk/moondream2', revision=None, bands=None, device=None, show_progress=True, combine_strategy='concatenate', **kwargs)` | Large-raster captioning. |
| `moondream_query_sliding_window` | `moondream_query_sliding_window(question, source, window_size=512, overlap=64, model_name='vikhyatk/moondream2', revision=None, reasoning=None, bands=None, device=None, show_progress=True, combine_strategy='concatenate', **kwargs)` | Large-raster VQA. |
| `moondream_detect_sliding_window` | `moondream_detect_sliding_window(source, object_type, window_size=512, overlap=64, iou_threshold=0.5, model_name='vikhyatk/moondream2', revision=None, output_path=None, bands=None, device=None, show_progress=True, **kwargs)` | Large-raster object grounding. |
| `moondream_point_sliding_window` | `moondream_point_sliding_window(source, object_description, window_size=512, overlap=64, model_name='vikhyatk/moondream2', revision=None, output_path=None, bands=None, device=None, show_progress=True, **kwargs)` | Large-raster point grounding. |

`MoondreamGeo` supports `caption`, `query`, `detect`, `point`, and the corresponding sliding-window methods plus image/GeoTIFF loading helpers.

## vLLM geospatial VLMs

| Callable | Signature | Notes |
| --- | --- | --- |
| `check_vllm_available` | `check_vllm_available()` | Strict boolean probe for the optional `vllm` package. |
| `VLLMGeo` | `VLLMGeo(model_id='Qwen/Qwen2-VL-7B-Instruct', base_url='http://localhost:8000/v1', api_key='EMPTY', offline=False, timeout=120, max_tokens=512, temperature=0.0, **kwargs)` | Server mode by default; offline mode requires local vLLM. |
| `vllm_caption` | `vllm_caption(source, model_id='Qwen/Qwen2-VL-7B-Instruct', base_url='http://localhost:8000/v1', length='normal', bands=None, **kwargs)` | Captioning wrapper. |
| `vllm_query` | `vllm_query(question, source=None, model_id='Qwen/Qwen2-VL-7B-Instruct', base_url='http://localhost:8000/v1', bands=None, **kwargs)` | VQA wrapper. |
| `vllm_detect` | `vllm_detect(source, object_type, model_id='Qwen/Qwen2-VL-7B-Instruct', base_url='http://localhost:8000/v1', output_path=None, bands=None, **kwargs)` | Prompt-based object detection wrapper. |

`VLLMGeo` adds sliding-window caption/query/detect methods, GeoTIFF loading helpers, and georeferenced output parsing.

## Captioning and feature extraction

| Callable | Signature | Notes |
| --- | --- | --- |
| `ImageCaptioner` | `ImageCaptioner(blip_model_name='Salesforce/blip-image-captioning-base', spacy_model_name='en_core_web_sm', device=None, auto_download=True)` | BLIP + spaCy caption/feature pipeline. |
| `ensure_spacy_model` | `ensure_spacy_model(model_name='en_core_web_sm', auto_download=True)` | Downloads the spaCy model only if missing and allowed. |
| `load_aerial_feature_vocab` | `load_aerial_feature_vocab(url=AERIAL_FEATURES_URL)` | Loads the aerial feature vocabulary JSON. |
| `load_image` | `load_image(source)` | Shared image loader used by the caption module. |
| `extract_features_from_caption` | `extract_features_from_caption(caption, include_features=None, exclude_features=None)` | Caption-only feature extraction. |
| `blip_analyze_image` | `blip_analyze_image(image_source, include_features=None, exclude_features=None, blip_model_name=None, spacy_model_name=None)` | Full BLIP + spaCy pipeline. |

`ImageCaptioner` key methods:

- `generate_caption(image_source)`
- `extract_features(caption, include_features=None, exclude_features=None)`
- `analyze(image_source, include_features=None, exclude_features=None)`

## Practical selection hints

- **Need only metadata?** Use the registry and dataset listing functions.
- **Already have embeddings?** Use `cluster_embeddings()`, `train_embedding_classifier()`, `compare_embeddings()`, or `embedding_to_geotiff()` without loading a model.
- **Need similarity maps?** Use DINOv3.
- **Need multispectral foundation-model inference?** Use Prithvi, UniverSat, or TESSERA depending on the sensor and workflow.
- **Need geospatial VQA or captioning?** Use Moondream or vLLM for VLM-style workflows, or BLIP/spaCy captioning for lighter text extraction.
- **Need to fine-tune or train a model?** Hand off to the training sub-skill.
