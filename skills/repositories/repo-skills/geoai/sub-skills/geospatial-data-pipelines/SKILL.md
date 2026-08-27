---
name: geospatial-data-pipelines
description: "Operate GeoAI geospatial data inspection, downloads, raster/vector
  conversion, JSON/YAML batch pipelines, and geospatial I/O troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Geospatial Data Pipelines

Use this sub-skill when the task is about preparing or validating geospatial data for GeoAI: inspecting raster/vector files, obtaining STAC/NAIP/Overture data, checking CRS/bounds/bands, clipping or tiling rasters, vectorizing masks, rasterizing vectors, and validating or running GeoAI batch pipelines from JSON/YAML.

## Route here for

- `geoai info` and Python inspection helpers for raster/vector metadata, band statistics, CRS, bounds, feature counts, attributes, and supported formats.
- `geoai.download` workflows for Planetary Computer STAC searches/downloads, NAIP imagery, Overture Maps features, asset listing/reading, vector conversion, and bounded download validation.
- `geoai.pipeline` batch jobs: `Pipeline`, `FunctionStep`, `GlobStep`, `SemanticSegmentationStep`, `RasterToVectorStep`, JSON/YAML config loading, checkpoint semantics, and `on_error` policy.
- `geoai.utils` raster/vector/sampling/visualization helpers for local GeoTIFF/GeoJSON/GeoPackage work, raster-to-vector and vector-to-raster conversion, TorchGeo-style sampling setup, map/plot inspection, and output QA.
- Repairing hard I/O cases such as an unknown pipeline step or a CRS mismatch before tiling/vectorizing.

## Route away from this sub-skill

- Model inference details, checkpoint/model selection, RF-DETR/SAM/semantic segmentation tuning: route to `detection-segmentation-inference`.
- Training, label schema design, dataset splits, augmentation, metrics, and model fine-tuning: route to `training-and-finetuning`.
- Foundation model embeddings, DINOv3/Prithvi/TESSERA/UniverSat, VLMs, and model registry loading: route to `foundation-models-embeddings-vlms`.
- QGIS plugin, MCP server, provider credentials, and agent integrations: route to `integrations-agents-qgis-mcp`.

## Start sequence

1. Identify the data object and operation: inspect, download, clip, rasterize, vectorize, sample, visualize, or run a batch config.
2. Validate inputs before mutation: file exists, extension is supported, CRS is present, bbox order is correct, output directories are intentional, and network/model/training side effects are acceptable.
3. Use the self-contained references:
   - [Data and pipeline workflows](references/data-and-pipeline-workflows.md)
   - [API reference](references/api-reference.md)
   - [Troubleshooting](references/troubleshooting.md)
4. Use bundled helpers when useful:
   - [scripts/validate_pipeline_config.py](scripts/validate_pipeline_config.py) validates JSON/YAML pipeline configs, shows registered step types, and checks checkpoint config hashes without running a pipeline.
   - [scripts/geospatial_io_smoke.py](scripts/geospatial_io_smoke.py) creates tiny local fixtures or inspects provided files to smoke-test raster/vector I/O and CRS compatibility.
5. Run model inference only after the geospatial data and config are validated; then hand off to the inference sub-skill if the task becomes model-centric.

## Safety defaults

- Do not download from the network, start training, load model weights, or overwrite user data unless the user explicitly requested that side effect.
- If the user asks for a validation plan before any download or model run, present the plan and stop before any network, download, or inference side effect until the user explicitly approves it.
- Treat CLI `download` as a thin convenience wrapper. Prefer the Python APIs in `geoai.download` when precise output-directory handling, STAC asset control, or robust error recovery matters.
- Treat `geoai pipeline show` and the bundled validator as safe config checks; `geoai pipeline run` may create outputs, checkpoint files, and run model steps.
- For every raster/vector conversion, compare CRS and bounds first. If CRS differs, reproject the vector or bbox into the raster CRS before clipping, rasterizing, or vectorizing.
