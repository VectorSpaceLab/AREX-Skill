---
name: model-inference
description: "Plan and validate TIAToolbox model inference with PatchPredictor,
  DeepFeatureExtractor, semantic segmentation, nucleus detection, and multitask
  segmentation engines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Model Inference

Use this sub-skill when a task needs TIAToolbox model engines, pretrained model selection, custom weights, device planning, IO config construction, output format decisions, or migration from deprecated nucleus instance segmentation APIs.

## Start Here

- For engine/API signatures and run-parameter contracts, read `references/api-reference.md`.
- For pretrained model key selection without downloading weights, read `references/model-registry.md` and use `scripts/model_registry_probe.py`.
- For end-to-end planning patterns, read `references/workflows.md`.
- For common inference failures and safe mitigations, read `references/troubleshooting.md`.

## Owned Capabilities

- Patch classification with `PatchPredictor` and deep embedding extraction with `DeepFeatureExtractor`.
- Semantic segmentation with `SemanticSegmentor` and nucleus detection with `NucleusDetector`.
- Multitask and nucleus instance segmentation with `MultiTaskSegmentor`, including migration away from deprecated `NucleusInstanceSegmentor`.
- Model zoo key validation, custom weight routing, CPU/GPU/MPS device choices, IO config validation, and output type planning.
- Inference CLI plan review for `patch-predictor`, `deep-feature-extractor`, `semantic-segmentor`, `nucleus-detector`, `nucleus-instance-segment`, and `multitask-segmentor`.

## Boundaries

- For mask creation, tile selection, stain normalization, and patch extraction fundamentals, route to `../image-preprocessing/`.
- For WSI reader metadata, resolution semantics, and `WSIReader` behavior, route to `../wsi-io/`.
- For viewing or editing generated `AnnotationStore` outputs, route to `../annotation-visualization/`.
- For an exhaustive CLI option catalog and project-level configuration conventions, route to `../cli-and-configuration/`.

## Safety Rules

- Do not imply pretrained weights are available locally; model-string construction may download weights unless `weights` points to local compatible weights.
- Prefer `device="cpu"` unless the user or environment explicitly confirms `cuda` or `mps` availability.
- Validate model keys with the bundled registry probe before constructing a pretrained engine.
- In WSI mode, require a save directory for file-backed outputs and verify `output_type` matches the engine capability.
