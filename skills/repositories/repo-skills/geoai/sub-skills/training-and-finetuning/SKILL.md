---
name: training-and-finetuning
description: "Route GeoAI training, fine-tuning, evaluation, and safe Hub publishing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training and Finetuning

Use this sub-skill when the task is to prepare training data layouts, select a
GeoAI training API, fit or fine-tune a model, inspect losses or metrics, or
publish a trained checkpoint to Hugging Face Hub.

If the request is inference-only, route it to the detection-segmentation-inference
path instead. If the work still needs image download, raster/vector tiling, or
format conversion before training, hand that preparation to the
geospatial-data-pipelines path first. If the task is about foundation-model
processors, embeddings, or VLMs, route it to the foundation-models-embeddings-vlms
path.

## What this sub-skill covers

- `geoai.segmentation` for SegFormer-style paired image/mask training.
- `geoai.train` for semantic segmentation, instance segmentation, object detection,
  validation, and training-path checks.
- `geoai.timm_train`, `geoai.timm_segment`, and `geoai.timm_regress` for timm-based
  classification, segmentation, and pixel regression.
- `geoai.classify` and `geoai.recognize` for geospatial classification workflows.
- `geoai.landcover_train` and `geoai.landcover_utils` for landcover losses,
  sparse-label metrics, class weights, and tile export.
- `geoai.object_detect` for multi-class detector preparation, evaluation, and
  publish-time helpers.

## Start here

1. Read [`references/training-recipes.md`](references/training-recipes.md) for the
   safest recipe match.
2. Read [`references/api-reference.md`](references/api-reference.md) for verified
   callable names, signatures, and return shapes.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) when the
   layout, channels, labels, checkpoint, or dependency story is unclear.
4. Run [`scripts/check_training_layout.py`](scripts/check_training_layout.py) to
   validate a candidate training layout before choosing a trainer.

## Guardrails

- Do not start training, data downloads, or Hub pushes from this router text.
- Keep `push_*_to_hub` calls credential-aware and explicit; they create or update
  remote repositories.
- Keep layout validation local and read-only.
- Prefer the smallest trainer that matches the data layout and label semantics.
