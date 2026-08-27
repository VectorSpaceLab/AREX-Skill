---
name: model-integrations
description: "Route SAHI model loading across supported detector and segmenter
  frameworks and optional dependencies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# model-integrations

Use this sub-skill when a task needs to choose, configure, or debug a SAHI detection model wrapper before prediction. It covers `AutoDetectionModel.from_pretrained(...)`, framework-specific model loading, optional dependency gates, device selection, category mapping, preloaded models, and credential/local-weight distinctions.

## Route here when

- Selecting a `model_type` for Ultralytics/YOLO, YOLOE, YOLO-World, YOLOv5, RT-DETR, HuggingFace detection or segmentation, TorchVision, MMDetection, Detectron2, Roboflow Universe, or local RF-DETR.
- Explaining `model_path`, `config_path`, `model`, `device`, `image_size`, `category_mapping`, `category_remapping`, HuggingFace text labels/tokens, or Roboflow API-key behavior.
- Diagnosing import failures for optional detector frameworks before running inference.
- Deciding between open-vocabulary routes such as YOLOE, YOLO-World, and HuggingFace GroundingDINO.

## Do not handle here

- Generic `get_prediction`, `get_sliced_prediction`, CLI prediction, slice sizes, overlap, or export calls: route to `sliced-inference`.
- NMS/NMM/GreedyNMM backend selection and postprocess acceleration: route to `postprocess-backends`.
- COCO conversion, dataset slicing/merging, evaluation, and dataset utilities: route to `dataset-tools`.

## Operating steps

1. Identify the detector family and desired source of weights: local file, framework model name, hosted Hub/Universe id, or a preloaded Python model object.
2. Open [references/model-matrix.md](references/model-matrix.md) to map the family to `model_type`, required arguments, source-backed caveats, and category mapping rules.
3. Open [references/optional-dependencies.md](references/optional-dependencies.md) before installing or importing optional frameworks. Treat optional wrappers as source-backed unless checked in the target runtime.
4. Run the safe checker when you only need dependency visibility:

   ```bash
   python scripts/check_model_dependencies.py
   ```

   The checker uses metadata and import-spec probes only; it does not load models or contact remote services.
5. If loading still fails, use [references/troubleshooting.md](references/troubleshooting.md) to separate missing optional packages, missing model weights, credential problems, model/config mismatches, device issues, and category-id mapping mistakes.

## Credential and network stance

- Prefer local weight/config paths for reproducible offline work.
- HuggingFace private or gated models use a `token` argument or `HF_TOKEN` at runtime.
- Roboflow Universe model ids use an `api_key` argument or `ROBOFLOW_API_KEY` at runtime.
- Do not bake tokens, API keys, or machine-specific paths into scripts, notebooks, or generated examples.

## Verification stance

Core SAHI source, model wrappers, docs, tests, and demo notebooks were inspected. Optional detector frameworks were not all installed in the construction environment, so framework-specific runtime behavior should be treated as source-backed until the checker and a minimal model load are run in the target environment.
