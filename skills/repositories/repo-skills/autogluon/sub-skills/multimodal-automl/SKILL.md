---
name: multimodal-automl
description: "Use AutoGluon MultiModalPredictor for text, image,
  tabular+text/image, document, NER, semantic matching, object detection,
  semantic segmentation, feature extraction, zero-shot, and deployment
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MultiModal AutoML

Use this sub-skill when the user needs AutoGluon AutoMM or `MultiModalPredictor` for text, image, mixed tabular+text/image, document, NER, semantic matching, object detection, semantic segmentation, feature extraction, zero-shot inference, or multimodal deployment/export tasks.

Route structured-only supervised learning to `../tabular-ml/` and forecasting to `../time-series-forecasting/`. Do not treat external dataset downloads, competition submissions, or raw repository CI examples as runtime requirements; distill the needed data/API pattern and work with the user's local files.

## Start Here

- For constructor and method signatures, problem types, metrics, and model config knobs, read `references/api-reference.md`.
- For end-to-end task recipes, including semantic matching and save/load, read `references/workflows.md`.
- For DataFrame, image, document, NER, matching, segmentation, and local path expectations, read `references/data-formats.md`.
- For COCO/VOC/DataFrame object detection handling, read `references/object-detection.md`.
- For ONNX, TensorRT, embedding extraction, and offline packaging, read `references/deployment.md`.
- For dependency, backend, schema, and checkpoint failure modes, read `references/troubleshooting.md`.

## Safe Bundled Helpers

- Use `scripts/inspect_multimodal_inputs.py --help` to validate local CSV/JSON data, image/document paths, matching identifiers, COCO metadata, or VOC-style annotations without training or downloading.
- Use `scripts/multimodal_smoke.py --help` to check installed AutoGluon multimodal imports, API signatures, problem types, and optional backend versions without training by default.

## Routing Guide

| User request | Read first | Key API |
| --- | --- | --- |
| Text/image/mixed classification or regression | `references/workflows.md` | `MultiModalPredictor(label=..., problem_type=...)` |
| Document image/PDF classification | `references/data-formats.md` | `column_types={...: "document"}` or inferred document columns |
| NER/entity extraction | `references/data-formats.md` | `problem_type="ner"`, `column_types={text_col: "text_ner"}` |
| Text/image/image-text similarity or retrieval | `references/workflows.md` | `query=...`, `response=...`, `match_label=...`, `candidate_data`, `id_mappings` |
| Object detection | `references/object-detection.md` | `problem_type="object_detection"`, COCO/VOC/DataFrame data |
| Semantic segmentation | `references/data-formats.md` | `problem_type="semantic_segmentation"`, image and mask columns |
| Feature extraction or zero-shot image classification | `references/workflows.md` | `problem_type="feature_extraction"` or `"zero_shot_image_classification"` |
| ONNX/TensorRT/export/offline deployment | `references/deployment.md` | `save`, `load`, `export_onnx`, `optimize_for_inference` |

## Default Agent Approach

1. Identify the task family and route away if it is structured-only tabular or time-series.
2. Confirm data shape before code: label/query/response columns, local image/document paths, object-detection annotation format, segmentation mask availability, and optional backend constraints.
3. Prefer CPU-safe, no-download validation first with the bundled scripts; only propose training/export after local data and dependencies are plausible.
4. Keep `path`/`save_path` explicit for real training, use short `time_limit` only for smoke examples, and set backend hyperparameters intentionally for CPU/GPU.
5. For matching/retrieval, distinguish row-pair prediction from candidate search: `predict(data, candidate_data=...)`, `evaluate(query_data=..., response_data=...)`, or embedding-based search.
6. For deployment, call out pickle trust for `load`, optional `standalone=True` packaging, and ONNXRuntime/TensorRT dependency requirements.
