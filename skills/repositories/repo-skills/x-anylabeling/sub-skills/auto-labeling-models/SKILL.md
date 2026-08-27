---
name: auto-labeling-models
description: "Use and troubleshoot X-AnyLabeling AI-assisted model configs,
  registry, custom models, downloads, and optional inference backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Auto-labeling Models

Use this sub-skill when the task involves X-AnyLabeling's AI-assisted model
registry, built-in model configuration YAMLs, custom model loading, download
source selection, remote inference hooks, or CPU/GPU/TensorRT backend choices.

## Start here

1. Identify the target model family in
   [references/model-overview.md](references/model-overview.md). Confirm whether
   the user needs a local built-in/adapted model, a remote server/API model, or a
   code-level adapter for an unadapted model.
2. For built-in or adapted custom models, use
   [references/custom-models.md](references/custom-models.md) to check the YAML
   schema, required fields, custom-name rules, and model-specific config fields.
3. For downloads, cache layout, ModelScope selection, ONNX Runtime, GPU extras,
   or TensorRT, use
   [references/backend-and-downloads.md](references/backend-and-downloads.md).
4. If loading fails, route by symptom through
   [references/troubleshooting.md](references/troubleshooting.md).
5. For safe registry inspection without model downloads or weight loading, run
   the bundled helper:

   ```bash
   python sub-skills/auto-labeling-models/scripts/inspect_model_configs.py --show-types
   python sub-skills/auto-labeling-models/scripts/inspect_model_configs.py --custom-config <config.yaml> --json
   ```

## What this sub-skill owns

- Built-in model family selection for classification, detection, segmentation,
  pose/face, tracking, OBB, depth, SAM, matting, RAM/tagging,
  OCR/layout/document parsing, VLM, grounding, counting, and lane workflows.
- Loading built-in model configs and adapted custom configs through the UI's
  model selector / custom model loader.
- Model cache and work-directory behavior, including default download locations
  and ModelScope-vs-default URL routing.
- YAML config schema: `type`, `name`, `display_name`, model path fields,
  `classes`, thresholds, `provider`, `config_file`, and YOLO-family `engine`
  values `ort`, `dnn`, and `trt`.
- ModelManager registry behavior: 204 built-in configs in the verified package
  environment, custom-name validation, five-custom-model limit, and `_custom_`
  prefixing.
- Backend selection and troubleshooting for verified CPU ONNX Runtime, optional
  unverified CUDA/GPU extras, optional TensorRT, remote-server tokens, and API
  tokens.
- Code-level integration checklist for unadapted models: config entry, model
  registry branch, UI model-type lists, and a `Model` subclass implementing
  `predict_shapes` and `unload`.

## Route elsewhere

- Manual annotation editing, shape semantics, XLABEL JSON schema, GUI review, or
  image/video/classifier panel operations: use `../annotation-ui/SKILL.md`.
- Dataset import/export and `xanylabeling convert` tasks: use
  `../conversion-cli/SKILL.md`.
- Training new models, exporting checkpoints, PyInstaller builds, localization,
  or maintainer workflows: use `../developer-workflows/SKILL.md`.

## Verified limits to preserve

The generated skill is grounded in package `x-anylabeling-cvhub` 4.0.2,
Python >=3.11 with Python 3.12 recommended, and a CPU inspection environment
where ONNX Runtime's CPU provider was verified. CUDA, TensorRT, remote server
operation, model downloads, and training/export workflows were documented from
repo evidence but were not executed during construction.
