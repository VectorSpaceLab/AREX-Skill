# Model and embedding workflows

This reference is the operating guide for GeoAI foundation-model, embedding, DINOv3, Prithvi, UniverSat, TESSERA, AlphaEarth, Moondream, vLLM, and caption workflows. It is based on GeoAI source modules, installed API inspection, native behavior tests, registry smoke evidence, and public example notebook names captured during construction. It intentionally does not require the original repository docs, tests, scripts, or notebooks at runtime.

## Decision sequence

1. **Classify the request.** Decide whether the user needs metadata, existing embeddings, model inference, VLM inference, or training/fine-tuning.
2. **Stay no-download when possible.** Registry lookup, optional dependency checks, existing embedding clustering/classification, and GeoTIFF export do not need model weights or network access.
3. **Normalize the name.** GeoAI foundation registry keys are lower-case identifiers; individual loaders may use Hugging Face IDs or model-family names.
4. **Check optional dependencies.** TerraTorch, TorchGeo, GeoTessera, vLLM, spaCy, transformers, and GPU support are workflow-specific, not required for registry metadata.
5. **Route away when needed.** Generic training and broad fine-tuning go to `training-and-finetuning`; segmentation/detection inference products go to `detection-segmentation-inference`; STAC/download/tiling prep goes to `geospatial-data-pipelines`.

## Name and key normalization

| User-provided form | Use it as | GeoAI action |
| --- | --- | --- |
| `prithvi-eo-2.0-300m` | Foundation registry key | Use with `get_foundation_model_info()` or `load_foundation_model()` if TerraTorch is available. |
| `ibm-nasa-geospatial/Prithvi-EO-2.0-300M` | Hugging Face repository ID | Normalize to `prithvi-eo-2.0-300m` for registry metadata; use module-specific Prithvi names for `geoai.prithvi`. |
| `Prithvi-EO-2.0-300M-TL` | Prithvi loader model name | Use with `load_prithvi_model()` or `PrithviProcessor`; this is not a `FOUNDATION_MODELS` key. |
| `google_satellite` | Embedding dataset key | Use as the GeoAI key for Google/AlphaEarth 64-D annual satellite embeddings. |
| `tessera` | Embedding dataset key and TESSERA workflow family | Use embedding-dataset functions for existing files; use `tessera_*` functions only when GeoTessera and downloads are acceptable. |
| `vikhyatk/moondream2` | Moondream model ID | Use with `MoondreamGeo` and `moondream_*` convenience functions. |
| `Qwen/Qwen2-VL-7B-Instruct` | vLLM-served VLM model ID | Use with `VLLMGeo(model_id=..., base_url=...)`. |

Use `scripts/list_geoai_models.py --query <name-or-id>` to find registry matches without loading weights.

## Foundation model registry workflow

Use `geoai.foundation_models` when the user asks which remote-sensing foundation model to choose, what tasks/modalities are supported, or whether a backbone can be loaded through TerraTorch.

Safe metadata path:

1. Call `list_foundation_models(verbose=False, as_dataframe=False)` or use the bundled registry reporter.
2. Filter with `category`, `modality`, `task`, `terratorch_only`, or `huggingface_only`.
3. Call `get_foundation_model_info(key)` for one key. The function returns a copy of metadata.
4. Only call `load_foundation_model(key, pretrained=True, **kwargs)` after confirming `terratorch_supported=True` and TerraTorch is installed.

Registry keys confirmed during construction: `prithvi-eo-2.0-300m`, `prithvi-eo-2.0-600m`, `clay-v1`, `dofa-large`, `satmae-base`, `scale-mae-large`, `ringmo`, `rvsa`, `satlas-pretrain`, `croma`, `ssl4eo-s12`, `spectral-gpt`, `hypersigma`, `presto`, `panopticon`, `dynamicvis`, `fomo`, `mmearth`, `universat`, `skysense`, `georsam`.

Example notebook name captured as source evidence: `foundation_models.ipynb`.

## Existing embedding dataset workflow

Use `geoai.embeddings` when the user has or wants precomputed embedding datasets. Distinguish patch embeddings from pixel/raster embeddings before planning work.

Dataset keys:

- Patch/GeoParquet-style: `clay`, `major_tom`, `earth_index`, `earth_embeddings`.
- Pixel/RasterDataset-style: `copernicus_embed`, `presto`, `tessera`, `google_satellite`, `embedded_seamless`.

No-download analysis path for existing embeddings:

1. If the user has a dataset object, call `extract_patch_embeddings()` or `extract_pixel_embeddings()`.
2. If the user already has NumPy arrays, skip model/dataset loading and call `cluster_embeddings()`, `embedding_similarity()`, `compare_embeddings()`, or `train_embedding_classifier()` directly.
3. Export dense embedding rasters with `embedding_to_geotiff(embeddings, bounds, output_path, crs="EPSG:4326")` when the embedding array shape and bounds are known.
4. Use `plot_embedding_vector()`, `plot_embedding_raster()`, or `visualize_embeddings()` only when plotting is requested and a display/save path is appropriate.

Download path, only when requested:

- `download_google_satellite_embedding()` fetches Google/AlphaEarth annual 64-band embedding tiles for years 2017-2025 and can write GeoTIFFs. This is network and I/O work, so it is not part of safe default probing.

Example notebook names captured as source evidence: `torchgeo_embeddings.ipynb`, `google_satellite_embedding.ipynb`, `AlphaEarth.ipynb`.

## DINOv3 similarity workflow

Use `geoai.dinov3` for patch-similarity maps and DINOv3 feature visualization on imagery.

Typical path:

1. Confirm the user has an input image/GeoTIFF and query point(s).
2. Prefer a local/cached `weights_path` if the user wants an offline run.
3. Instantiate `DINOv3GeoProcessor(model_name="dinov3_vitl16", weights_path=..., device=...)` or use wrappers such as `create_similarity_map()` and `analyze_image_patches()`.
4. Use `coord_crs` when query coordinates are not in the raster CRS, and keep `target_size` patch-aligned.
5. Save only to user-approved output directories.

Routing boundary:

- `geoai.dinov3_finetune` exposes `DINOv3Segmenter`, `DINOv3SegmentationDataset`, `train_dinov3_segmentation()`, and `dinov3_segment_geotiff()`. Full training/fine-tuning planning belongs to `training-and-finetuning`. Segmentation output interpretation belongs to `detection-segmentation-inference`.

Example notebook names captured as source evidence: `DINOv3.ipynb`, `DINOv3_visualization.ipynb`, `DINOv3_wetlands.ipynb`, `dinov3_finetune_segmentation.ipynb`.

## Prithvi workflow

Use `geoai.prithvi` for NASA-IBM Prithvi EO 2.0 masked-autoencoder processing and feature extraction on multi-temporal satellite imagery.

Workflow:

1. Use `get_available_prithvi_models()` to list exact loader model names.
2. If the user gives a full Hugging Face ID, strip the owner prefix for `geoai.prithvi` loader names and use lower-case registry keys only for `geoai.foundation_models` metadata.
3. Use `load_prithvi_model(model_name="Prithvi-EO-2.0-300M-TL", device=..., cache_dir=...)` or instantiate `PrithviProcessor` directly.
4. Pass local `config_path` and `checkpoint_path` when available to avoid downloads.
5. Use `prithvi_inference(file_paths, output_dir=..., mask_ratio=..., device=...)` only after output paths and model-weight access are approved.

Supported loader names include `Prithvi-EO-2.0-tiny-TL`, `Prithvi-EO-2.0-100M-TL`, `Prithvi-EO-2.0-300M`, `Prithvi-EO-2.0-300M-TL`, `Prithvi-EO-2.0-600M`, and `Prithvi-EO-2.0-600M-TL`.

Example notebook name captured as source evidence: `prithvi.ipynb`.

## UniverSat workflow

Use `geoai.universat` for UniverSat multimodal tile embeddings.

Workflow:

1. Confirm the user has imagery/samples organized by modality key such as `spot` or `s2`.
2. Use `UniverSatProcessor(...).format_batch()` and `.encode_raster()` or wrapper `universat_inference()`.
3. Use `get_tile_embedding(tokens)` to average token embeddings into a tile vector.
4. Use `get_pca_rgb(tokens, is_batch=...)` for RGB visualization of token grids. Set `is_batch` when a 3D tensor shape is ambiguous.
5. Route `universat_train()` and any experiment override planning to `training-and-finetuning`.

Example notebook name captured as source evidence: `universat.ipynb`.

## TESSERA and AlphaEarth workflows

TESSERA:

- Use `geoai.tessera` when the user wants TESSERA 128-channel temporal-spectral embeddings.
- `tessera_available_years()`, `tessera_tile_count()`, and `tessera_coverage()` are planning/preflight helpers.
- `tessera_download()`, `tessera_fetch_embeddings()`, and `tessera_sample_points()` require the optional GeoTessera dependency and may perform network/data access.
- `tessera_visualize_rgb()` works on existing TESSERA GeoTIFF files.

AlphaEarth / Google satellite embeddings:

- The embedding dataset key is `google_satellite`.
- Existing `google_satellite` GeoTIFF directories can be loaded through `load_embedding_dataset(name="google_satellite", paths=...)` when TorchGeo embedding datasets are installed.
- Use `download_google_satellite_embedding()` only when the user explicitly requests download/prep and accepts network/I/O cost.

Example notebook names captured as source evidence: `tessera.ipynb`, `google_satellite_embedding.ipynb`, `AlphaEarth.ipynb`.

## Moondream VLM workflow

Use `geoai.moondream` when the user wants local/Hugging Face Moondream geospatial VLM captioning, VQA, object grounding, point selection, or sliding-window analysis.

Workflow:

1. Choose `model_name="vikhyatk/moondream2"` for the default path, or `model_name="moondream/moondream3-preview"` when the user requests Moondream 3 behavior.
2. Choose `device="cuda"`, `"mps"`, or `"cpu"` explicitly when runtime constraints matter.
3. For GeoTIFFs with more than three bands, pass `bands=[...]` to choose RGB-like bands.
4. Use single-image wrappers (`moondream_caption`, `moondream_query`, `moondream_detect`, `moondream_point`) for small inputs.
5. Use sliding-window wrappers for large rasters, with explicit `window_size`, `overlap`, and `show_progress` choices.

Example notebook names captured as source evidence: `moondream.ipynb`, `moondream_gui.ipynb`, `moondream_sliding_window.ipynb`.

## vLLM geospatial VLM workflow

Use `geoai.vllm_geo` when the user has or will run an OpenAI-compatible vLLM vision-language endpoint, or explicitly asks for in-process vLLM.

Server mode path:

1. Confirm the server exists and exposes a base URL ending in `/v1`, commonly `http://localhost:8000/v1`.
2. Instantiate `VLLMGeo(model_id="Qwen/Qwen2-VL-7B-Instruct", base_url=..., api_key=..., offline=False)`.
3. Use `.caption()`, `.query()`, `.detect()`, or sliding-window methods. `vllm_detect()` expects JSON-like normalized boxes from the model and georeferences them when metadata is available.

Offline mode path:

- `offline=True` requires the optional `vllm` package and enough local accelerator memory for the chosen model. Prefer server mode for operations where the model is already hosted.

## BLIP/spaCy caption workflow

Use `geoai.caption` when the user asks for classic image captioning plus aerial-feature extraction instead of Moondream/vLLM VQA.

Workflow:

1. Use `ImageCaptioner(blip_model_name="Salesforce/blip-image-captioning-base", spacy_model_name="en_core_web_sm", device=..., auto_download=False)` when avoiding automatic spaCy downloads.
2. Use `.generate_caption(image_source)` to produce a caption.
3. Use `.extract_features(caption, include_features=..., exclude_features=...)` to extract feature terms.
4. Use `blip_analyze_image()` only when the BLIP model and spaCy model are available or downloads are acceptable.
5. Use `extract_features_from_caption()` when the caption is already known and no image/model inference is needed.

Example notebook name captured as source evidence: `image_captioning.ipynb`.
