---
name: detection-segmentation-inference
description: "Choose and run GeoAI inference APIs for segmentation, detection,
  prompt segmentation, RF-DETR, water/cloud/super-resolution, ONNX, and
  automatic HF-style image tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Detection and Segmentation Inference

Use this sub-skill when the task is about running GeoAI inference on existing imagery, checkpoints, or model IDs.
Do not use it for dataset creation, model training, or data preparation.

## Start here

- Read [Inference workflows](references/inference-workflows.md) to choose the API family.
- Read [API reference](references/api-reference.md) for the exact entry points, defaults, and outputs.
- Read [Troubleshooting](references/troubleshooting.md) when imports, model metadata, band order, overlap, device, or output format fail.
- Run [inference_input_check.py](scripts/inference_input_check.py) for a read-only preflight before large rasters, offline models, or mixed-band inputs.
- If the user explicitly wants a validation plan before any model run, present the plan and wait for approval before loading weights, starting inference, or writing outputs.

## Choose the route

- `geoai.auto` for HF-style image tasks, task auto-detection, and one-shot geospatial inference.
- `geoai.train` inference wrappers for local semantic segmentation, instance segmentation, and detector checkpoints.
- `geoai.segment` and `geoai.sam.SamGeo` for text prompts, boxes, clicks, and SAM-backed segmentation.
- `geoai.object_detect` for multi-class detector workflows and batch detection.
- `geoai.rfdetr` for RF-DETR detection and segmentation variants.
- `geoai.water`, `geoai.tools.cloudmask`, `geoai.tools.multiclean`, and `geoai.tools.sr` for water, cloud, cleanup, and super-resolution workflows.
- `geoai.onnx` for export and ONNXRuntime inference.

## Keep out of scope

- Training dataset creation and model training.
- Data download, tiling, clipping, or raster/vector preparation workflows.
- Foundation-model feature extraction or VLM deep detail unless the VLM is the inference backend being run.
- NWPU training/reference scripts; use the safe preflight helper instead.

## Common outputs

- GeoTIFF masks, probability maps, depth maps, and super-resolution rasters.
- GeoJSON, GPKG, Shapefile, FlatGeobuf, or Parquet vector outputs.
- Detection GeoDataFrames and class-score summaries.
- ONNX files with JSON sidecar metadata.
