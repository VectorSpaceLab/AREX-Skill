---
name: customization-extension
description: "Extend MMDetection 3.3.0 with custom registries, models, losses,
  datasets, transforms, hooks, optimizers, project plugins, structures, and
  2.x-to-3.x migration fixes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Customization Extension

Use this sub-skill when an agent must add, register, debug, or migrate custom MMDetection components. It covers MMEngine registry usage, `custom_imports`, project plugin layout, custom model/data/runtime classes, and `DetDataSample`/box/mask structure expectations.

## Route First

- For config inheritance, model zoo selection, `_base_`, or `cfg-options`, use `../configuration-model-zoo/SKILL.md`.
- For dataset file layout, COCO conversion, annotation schemas, or metrics, use `../datasets-evaluation/SKILL.md`.
- For train/test launch commands, resume, distributed jobs, or result dumping, use `../training-testing/SKILL.md`.
- For inference API calls or visualization outputs, use `../inference-visualization/SKILL.md`.

## Core References

- `references/registries-and-apis.md`: registry nodes, decorators, import/scope rules, structures, and migration API changes.
- `references/extension-workflows.md`: workflows for custom models, losses, datasets, transforms, hooks, optimizers, projects plugins, and structures.
- `references/troubleshooting.md`: diagnosis tables for registration, imports, default scope, class counts, data samples, transforms, optimizers, and 2.x migration failures.
- `scripts/registry_probe.py`: inspect MMDetection registry contents and verify import paths without training.

## Fast Workflow

1. Identify the component boundary: model/loss/head/backbone uses `MODELS`; dataset uses `DATASETS`; transform uses `TRANSFORMS`; hooks use `HOOKS`; optimizers and constructors use optimizer registries.
2. Register the Python class with the correct decorator from `mmdet.registry`, then ensure its module is imported by package `__init__.py` or by config-level `custom_imports`.
3. Set `default_scope='mmdet'` or initialize the `mmdet` scope before registry builds when running standalone checks.
4. Validate the component in isolation with `scripts/registry_probe.py` and a minimal `Registry.build()` or transform call before launching training.
5. When modifying data flow, confirm pipeline keys before and after each transform and ensure final packed samples expose the fields consumed by the model.

## Hard Usability Cases

- A new bbox head appears in config as `type='MyBBoxHead'` but build fails with `KeyError`; debug registry node, import side effects, and default scope before editing model logic.
- A custom transform returns missing or renamed keys; trace expected input/output keys through the pipeline and confirm packed `DetDataSample` fields before training.
