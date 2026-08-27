---
name: model-api
description: "Inspect and extend MMYOLO registries, model components, datasets,
  plugins, and deploy-mode modules safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# MMYOLO model API and extension router

Use this sub-skill when the task is to inspect MMYOLO registries, understand public model/dataset component APIs, register custom modules, add project-local extensions, reason about plugins, or decide whether a model can be switched to deploy mode.

## Read first

1. Read [API reference](references/api-reference.md) for registry names, default-scope behavior, public component families, and installed signature facts.
2. Read [extension patterns](references/extension-patterns.md) before creating or modifying any custom model, backbone, head, loss, assigner, transform, visualizer, or project module.
3. Read [troubleshooting](references/troubleshooting.md) when registry lookup, custom imports, channel dimensions, plugins, data preprocessors, or deploy-mode conversion fail.
4. Use [inspect_mmyolo_registry.py](scripts/inspect_mmyolo_registry.py) for safe registry/module discovery. It imports/registers modules and reports registry contents; it does not build models, load datasets, train, download, or run inference.

## Route elsewhere

- Config-family selection, `_base_` inheritance edits, model zoo config choice, and `--cfg-options` belong to `config-customization`.
- Training, testing, distributed launch, resume, AMP, and evaluation CLI behavior belong to `training-evaluation`.
- End-user image/video/folder inference and visualization demos belong to `inference-visualization`.
- ONNX/TensorRT/RKNN/MMDeploy/EasyDeploy export or checkpoint conversion belongs to `deployment-conversion`.
- Dataset layout/conversion/statistics workflows belong to `data-tools`; this sub-skill covers only dataset and transform extension APIs.

## Safe operating posture

- Prefer `mmyolo.utils.register_all_modules()` before direct `MODELS.build`, `DATASETS.build`, `TRANSFORMS.build`, or `TASK_UTILS.build` use in standalone scripts.
- In reusable library modules, do not change the global MMEngine default scope at import time. Register classes with decorators and let the calling config/script handle `custom_imports` and default scope.
- Keep custom module imports explicit with `custom_imports` or a deliberate import in the caller; a class is not discoverable by registry name until its module has been imported.
- Treat `switch_to_deploy(model)` as a destructive inference/export preparation step for modules containing MMYOLO `RepVGGBlock` branches. Do not call it before continued training.
