---
name: auto-labeling-models
description: "Operate AnyLabeling model-backed auto-labeling: catalogs, custom
  configs, registry extensions, YOLO detectors, SAM-family segmentation,
  prompts, caches, and diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Auto-labeling models

Use this sub-skill when the task concerns AnyLabeling's model-backed auto-labeling system rather than manual drawing, label-file export, packaging, or release automation.

## Load this when

- Inspecting the built-in auto-labeling model catalog or a user-provided custom model `config.yaml`.
- Diagnosing model selection, download/cache state, unknown model types, missing model files, or Hugging Face/network download failures.
- Working with `ModelRegistry`, `ModelManager`, threaded model loading/inference, or registry import side effects.
- Configuring or troubleshooting YOLOv5/YOLOv8 rectangle detection models.
- Configuring or troubleshooting Segment Anything, MobileSAM, SAM2, SAM3, SAM3 text prompts, prompt marks, mask post-processing, output modes, or the macOS CoreML SAM2 branch.

## Do not use this for

- Manual annotation editing, shape list behavior, label-file schemas, dataset export/import, or result insertion details after `AutoLabelingResult` reaches the UI. Route those to `annotation-ui-and-data`.
- PyPI packaging, CPU/GPU wheel selection, CI, publishing, or standalone executable builds. Route those to `packaging-release`.

## Reference map

- [Model catalog and configs](references/model-catalog-and-configs.md): built-in catalog behavior, custom config contracts, registry keys, download/cache semantics, and extension checklist.
- [Auto-labeling workflows](references/auto-labeling-workflows.md): UI-to-manager workflow, prompt modes, YOLO outputs, SAM-family variants, SAM3 text prompts, caches, and optional real-inference playbook.
- [Troubleshooting](references/troubleshooting.md): unknown model types, invalid configs, missing files, downloads, BOM YAML, SAM3 text mode, thresholds, mask dtype, variant detection, CUDA/CoreML confusion.

## Bundled safe diagnostics

The scripts are read-only and perform no downloads:

- `scripts/inspect_model_catalog.py` summarizes a catalog file or an installed package catalog, optionally merging already-present cache `config.yaml` files.
- `scripts/check_custom_model_config.py` validates a custom model config, resolves referenced local/cache files, and optionally inspects a present ONNX decoder to catch SAM2/SAM3/SAM1 variant mismatches.

Run each script with `--help` before use.
