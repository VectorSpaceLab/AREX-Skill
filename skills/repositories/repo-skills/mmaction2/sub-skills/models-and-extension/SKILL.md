---
name: models-and-extension
description: "Understand MMAction2 model families, registries, customization,
  projects, and export/deployment utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMAction2 models and extension router

Use this sub-skill when a task is about MMAction2 model families, registry-backed components, custom components, project-style extensions, multimodal/retrieval/audio/skeleton surfaces, or export/deployment/publishing utilities.

## Load these bundled references first

- [Model and extension reference](references/model-extension-reference.md) — model family map, registries, default scope behavior, custom module patterns, project extension pattern, and class-count/shape cautions.
- [Export and deployment reference](references/export-deployment-reference.md) — publish, checkpoint conversion, ONNX, TorchServe, feature extraction, and optional-extra caveats.
- [Troubleshooting](references/troubleshooting.md) — registry failures, missing custom imports, tensor shape and `num_classes` mismatches, multimodal optional dependencies, and export errors.
- [Registry probe helper](scripts/mmaction2_registry_probe.py) — safe package/registry/version probe; run with `--help` first.

## Route out of this sub-skill

- Routine config editing, annotation schemas, dataset file lists, and pipeline/data-prep details: `../data-and-configs/SKILL.md`.
- Training/testing/evaluation command construction, distributed launch, result dumps, and metrics execution: `../training-and-evaluation/SKILL.md`.
- Inference APIs, inferencer/demo workflows, visualization outputs, and label maps: `../inference-and-demos/SKILL.md`.

## Operating rules

1. Prefer registry-aware explanations: MMAction2 builds most user-facing models, datasets, transforms, losses, metrics, hooks, loops, inferencers, and visualizers through `mmaction.registry` and MMEngine registries.
2. Initialize or preserve the `mmaction` default scope before building registry objects. Use `register_all_modules(init_default_scope=True)` for standalone probes; use `init_default_scope=False` only when another OpenMMLab scope is intentionally active.
3. For custom modules, require both an import path (`custom_imports` or normal Python import) and a registered class (`@MODELS.register_module()`, `@DATASETS.register_module()`, `@TRANSFORMS.register_module()`, or `@METRICS.register_module()`).
4. Validate classifier head changes with both `num_classes` and `in_channels`; tensor shape errors usually mean the dataset/pipeline format and recognizer/head family are mismatched.
5. Treat multimodal, retrieval, AVA/spatio-temporal detection, ONNX, and TorchServe workflows as optional-extra workflows. Explain missing dependency messages instead of silently falling back to unrelated models.
