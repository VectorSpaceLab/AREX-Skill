---
name: extension-projects
description: "Extend Detectron2 with registries, configurable model components,
  custom trainers, and optional project packages without over-installing
  optional stacks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Detectron2 Extension Projects

Use this sub-skill when a task asks you to add or debug a Detectron2 extension: custom registries, custom backbones, ROI heads, meta-architectures, configurable components, trainer subclasses, or the bundled research-project packages under `detectron2.projects`.

## Read First

- For registry and config-extension patterns, read `references/extension-patterns.md`.
- For custom model component interfaces, read `references/model-components.md`.
- For bundled and optional research projects, read `references/projects-overview.md`.
- For extension failures and diagnosis, read `references/troubleshooting.md`.
- To smoke-test registry mechanics without building or training a model, run `python scripts/registry_smoke_check.py` from this sub-skill directory or copy the script into a scratch workspace.

## Choose This Sub-Skill For

- Registering or diagnosing `BACKBONE_REGISTRY`, `ROI_HEADS_REGISTRY`, `META_ARCH_REGISTRY`, `SEM_SEG_HEADS_REGISTRY`, `PROPOSAL_GENERATOR_REGISTRY`, or related model component registries.
- Wiring custom classes into Yacs configs through names such as `MODEL.BACKBONE.NAME`, `MODEL.ROI_HEADS.NAME`, or `MODEL.META_ARCHITECTURE`.
- Deciding whether to register a component, construct it with explicit arguments, or use `@configurable` plus `from_config`.
- Subclassing `DefaultTrainer` to customize `build_model`, `build_optimizer`, `build_train_loader`, `build_evaluator`, hooks, or test-time behavior.
- Loading or diagnosing installed project packages such as `detectron2.projects.point_rend`, `detectron2.projects.deeplab`, and `detectron2.projects.panoptic_deeplab`.

## Boundaries

- For dataset registration, mappers, metadata, and dataloaders, use the data/config owning sub-skill.
- For standard training, launch, checkpoints, evaluation, and inference execution, use the training/inference owning sub-skills.
- For export/deployment details, use the deployment owning sub-skill.
- Treat DensePose, TensorMask, TridentNet, ViTDet, MViTv2, PointSup, and other research projects as optional examples unless the environment explicitly includes their dependencies and the user asks for that stack.

## Working Checklist

1. Identify the extension seam: model component registry, full meta-architecture, explicit constructor override, trainer hook/classmethod, or project config adder.
2. Import the module that performs registration before asking a builder or registry to resolve a string name.
3. Add project config keys before merging a project config or setting project-specific options.
4. Match the builder's expected signature, input feature names, and `ShapeSpec` contracts.
5. Keep optional project dependencies opt-in; do not install broad extras unless the requested project requires them and the user approves.
6. Use the bundled smoke script to validate registry behavior before debugging heavier model/data/training code.
