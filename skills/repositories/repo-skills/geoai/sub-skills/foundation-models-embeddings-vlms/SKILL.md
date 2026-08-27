---
name: foundation-models-embeddings-vlms
description: "Route GeoAI foundation models, embeddings, DINOv3, Prithvi,
  UniverSat, TESSERA, Moondream, vLLM, and caption workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Foundation models, embeddings, and VLMs

Use this sub-skill when the task centers on GeoAI foundation-model registry lookup, precomputed embeddings, DINOv3 similarity, Prithvi, UniverSat, TESSERA, AlphaEarth/Google satellite embeddings, Moondream, vLLM geospatial VLMs, or BLIP/spaCy captioning.

## Route here

- Foundation model discovery, registry filtering, TerraTorch-backed model loading decisions, or model-name normalization.
- Existing embedding dataset analysis, clustering, similarity search, lightweight classifiers, or embedding GeoTIFF export.
- DINOv3 patch similarity, feature-map visualization, and DINOv3 workflow selection.
- Prithvi, UniverSat, TESSERA, AlphaEarth, Moondream, vLLM, and captioning API choice and preflight.

## Route away

- Generic training, broad fine-tuning, dataset layout validation, or DINOv3 segmentation training details: route to `training-and-finetuning`.
- Segmentation/object-detection inference products and vectorized mask outputs: route to `detection-segmentation-inference`.
- STAC search, NAIP/Overture downloads, raster tiling, CRS repair, or pipeline config prep: route to `geospatial-data-pipelines`.

## Start points

- [Model and embedding workflows](references/model-and-embedding-workflows.md)
- [API reference](references/api-reference.md)
- [Troubleshooting](references/troubleshooting.md)
- [No-download registry reporter](scripts/list_geoai_models.py)

Prefer metadata, optional-dependency probes, and existing embeddings first. Only load model weights, call Hugging Face, download embedding tiles, start a vLLM service, or run long inference when the user explicitly accepts those runtime costs.
