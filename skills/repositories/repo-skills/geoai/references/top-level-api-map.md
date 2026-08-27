# Top-Level API Map

## Purpose

Read this when you know a GeoAI symbol or module name but need to choose the right sub-skill. The installed package exposes many lazy top-level names through `geoai.__getattr__`; importing `geoai` is intentionally lightweight, while specific modules may require optional dependencies.

## Core package surfaces

| Package surface | Example entry points | Route |
| --- | --- | --- |
| CLI and pipelines | `geoai.cli`, `geoai pipeline show`, `Pipeline`, `FunctionStep`, `GlobStep`, `SemanticSegmentationStep`, `RasterToVectorStep`, `load_pipeline` | `geospatial-data-pipelines` |
| Raster/vector utilities | `get_raster_info`, `get_vector_info`, `export_geotiff_tiles`, `raster_to_vector`, `vector_to_raster`, `mosaic_geotiffs`, `create_geo_dataloader` | `geospatial-data-pipelines` |
| Data acquisition | `download_naip`, `pc_stac_search`, `pc_stac_download`, `get_overture_data`, `download_overture_buildings` | `geospatial-data-pipelines` |
| Semantic and instance segmentation | `semantic_segmentation`, `semantic_segmentation_batch`, `instance_segmentation`, `train_segmentation_model`, `get_smp_model` | `detection-segmentation-inference` for inference; `training-and-finetuning` for training |
| Prompt segmentation and SAM | `GroundedSAM`, `CLIPSegmentation`, `SamGeo`, `BoundingBox`, `DetectionResult` | `detection-segmentation-inference` |
| Object detection | `multiclass_detection`, `batch_multiclass_detection`, `train_multiclass_detector`, `evaluate_multiclass_detector`, `NWPU_VHR10_CLASSES` | `detection-segmentation-inference` for inference; `training-and-finetuning` for training/evaluation |
| RF-DETR and optional detectors | `rfdetr_detect`, `rfdetr_segment`, `rfdetr_train`, `check_rfdetr_available` | `detection-segmentation-inference` |
| Specialized inference tools | `segment_water`, `predict_cloud_mask`, `clean_segmentation_mask`, `super_resolution`, `ONNXGeoModel`, `export_to_onnx` | `detection-segmentation-inference` |
| Training and fine-tuning | `train_timm_classifier`, `train_timm_segmentation_model`, `train_pixel_regressor`, `train_classifier`, `train_image_classifier`, `train_segmentation_landcover` | `training-and-finetuning` |
| Losses and metrics | `DiceLoss`, `FocalLoss`, `LandcoverCrossEntropyLoss`, `TverskyLoss`, `UnifiedFocalLoss`, `calc_iou`, `calc_f1_score`, `calc_segmentation_metrics` | `training-and-finetuning` |
| Foundation-model registry | `list_foundation_models`, `get_foundation_model_info`, `load_foundation_model`, `check_terratorch_available` | `foundation-models-embeddings-vlms` |
| Embeddings | `list_embedding_datasets`, `load_embedding_dataset`, `extract_patch_embeddings`, `extract_pixel_embeddings`, `cluster_embeddings`, `embedding_similarity`, `embedding_to_geotiff` | `foundation-models-embeddings-vlms` |
| DINOv3, Prithvi, UniverSat, TESSERA | `DINOv3GeoProcessor`, `create_similarity_map`, `PrithviProcessor`, `prithvi_inference`, `UniverSatProcessor`, `universat_inference`, `tessera_download`, `tessera_fetch_embeddings` | `foundation-models-embeddings-vlms` |
| VLMs and captioning | `MoondreamGeo`, `moondream_caption`, `moondream_query`, `moondream_detect`, `VLLMGeo`, `vllm_caption`, `vllm_query`, caption helpers | `foundation-models-embeddings-vlms` |
| Interactive maps and widgets | `LeafMap`, `Map`, `create_vector_data`, `edit_vector_data`, `DINOv3GUI`, `moondream_gui` | `geospatial-data-pipelines` for map data operations; `integrations-agents-qgis-mcp` for UI/integration issues |
| Agents and MCP/QGIS integrations | `GeoAgent`, `STACAgent`, `CatalogAgent`, `MapTools`, QGIS plugin panels, GeoAI MCP server tools | `integrations-agents-qgis-mcp` |

## Lazy import behavior

- `import geoai` should be fast because heavy modules are loaded only when a symbol is accessed.
- Top-level access such as `geoai.semantic_segmentation` imports the owning module on demand.
- Missing optional extras often show up as `AttributeError` wrapping an `ImportError` from the underlying module. Route to the owning sub-skill and install only the needed extra.

## CLI surface verified for this skill

The public CLI exposes:

- `geoai info <filepath>` for raster/vector metadata.
- `geoai download naip --bbox minx,miny,maxx,maxy --output path [--year YEAR]` for NAIP imagery.
- `geoai pipeline run <config>` and `geoai pipeline show <config>` for JSON/YAML pipeline definitions.

Use the geospatial-data-pipelines sub-skill for CLI details and config validation.
