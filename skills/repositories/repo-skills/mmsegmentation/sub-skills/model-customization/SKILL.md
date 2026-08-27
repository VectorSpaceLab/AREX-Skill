---
name: model-customization
description: "Customize MMSegmentation models, registries, projects,
  checkpoints, and model-complexity checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Customization

Use this sub-skill when extending MMSegmentation with custom model components, choosing or adapting model zoo configs, validating registry wiring, converting checkpoints, or explaining model-complexity/deployment caveats.

## Scope

This sub-skill covers:

- MMSegmentation model architecture: segmentors, data preprocessors, backbones, necks, decode heads, auxiliary heads, losses, metrics, optimizers, and schedulers.
- Registry usage through `mmseg.registry` and legacy builder aliases exposed from `mmseg.models`.
- Custom components implemented in-tree, in project packages, or in external Python packages imported by config.
- Model zoo/config selection, optional projects, checkpoint conversion planning, model publishing, and FLOPs/parameter caveats.

Use sibling skills instead for:

- Dataset layout, transforms, palettes, and evaluators beyond metric registration: `data-configuration`.
- Launching train/test jobs, distributed runners, and result reporting: `training-evaluation`.
- Runtime inference APIs, visualization, or serving: `inference`.

## Fast Routing

- Need to understand what can be customized or which built-ins exist? Read [model-components](references/model-components.md).
- Need to add a custom backbone, decode head, loss, metric, optimizer, scheduler, or project package? Read [customization-recipes](references/customization-recipes.md).
- Need to adapt pretrained weights, publish a checkpoint, or explain why a conversion is unsafe? Read [checkpoint-conversion](references/checkpoint-conversion.md).
- Need to debug `KeyError`, `custom_imports`, `default_scope`, shape mismatch, optional dependency, FLOPs, or MMCV-op failures? Read [troubleshooting](references/troubleshooting.md).
- Need to check whether a type is registered after importing optional modules? Run [inspect_registry.py](scripts/inspect_registry.py).

## Default Workflow

1. Identify the target extension point: `MODELS` for segmentors/backbones/necks/heads/losses/data preprocessors, `METRICS` for evaluators, `OPTIMIZERS` or `OPTIM_WRAPPER_CONSTRUCTORS` for optimizer behavior, and `PARAM_SCHEDULERS` for schedulers.
2. Confirm the component is imported before config build: either import it from the package `__init__.py` path or add `custom_imports = dict(imports=[...], allow_failed_imports=False)` to the config.
3. Keep `default_scope = 'mmseg'` unless intentionally composing registries from another OpenMMLab package.
4. Smoke-check registry visibility with `scripts/inspect_registry.py` before debugging model math.
5. Build or instantiate the smallest safe config first, then run a tiny forward/loss test before launching training.
6. Treat checkpoint conversion and FLOPs as verification tasks, not guarantees: both depend on exact source checkpoint schemas, target key names, optional dependencies, and supported operators.

## Guardrails

- Prefer `mmseg.registry.MODELS.build(...)` for new guidance; legacy `build_backbone`, `build_head`, `build_loss`, and `build_segmentor` still exist but warn that `MODELS.build()` is preferred.
- Register custom model classes with `@MODELS.register_module()` and custom metrics with `@METRICS.register_module()`.
- A config `type='MyType'` only works after Python imports the module that runs the registration decorator.
- Do not promise that a source checkpoint can be loaded or converted unless key mapping, tensor shapes, class counts, and optional dependency versions are checked.
- Do not treat FLOPs as paper-ready without verifying unsupported ops, post-processing omissions, input shape, and head support.
