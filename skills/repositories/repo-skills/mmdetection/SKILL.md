---
name: mmdetection
description: "Use this skill when working with MMDetection 3.x for object
  detection, instance/panoptic segmentation, tracking-adjacent configs, model
  zoo configs, inference, visualization, training/testing commands, datasets,
  evaluation, or extension work."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMDetection

MMDetection is OpenMMLab's PyTorch-based detection toolbox. Use this root skill as a router, then open the nearest sub-skill for concrete commands, APIs, config patterns, and troubleshooting.

## Quick Import and Environment Check

Use the bundled checker when diagnosing an install before deeper work:

```bash
python scripts/check_mmdet_environment.py
```

A healthy base environment should import `mmdet`, `mmcv`, `mmengine`, and `torch`, report compatible MMDetection/MMCV/MMEngine versions, and expose inference APIs such as `DetInferencer`, `init_detector`, and `inference_detector`.

Important dependency facts:

- MMDetection 3.3.0 requires `mmcv>=2.0.0rc4,<2.2.0` and `mmengine>=0.7.1,<1.0.0`.
- Install full `mmcv` for workflows importing `mmcv.ops`; `mmcv-lite` can fail with `ModuleNotFoundError: mmcv._ext`.
- Match `torch`, `mmcv`, CUDA/CPU wheels, NumPy, and OpenCV carefully; ABI mismatches often appear during API imports.
- CPU inspection/inference is possible for many workflows, but some ops and real training/evaluation workloads are GPU- or dataset-dependent.

Read `references/troubleshooting.md` for cross-cutting install/import/backend failures. Read `references/repo-provenance.md` when deciding whether this skill is stale against a newer MMDetection checkout.

## Route by Task

| User task | Open this sub-skill | Why |
| --- | --- | --- |
| Choose a config, inspect `_base_`, apply `--cfg-options`, compare model zoo entries, or debug config loading | `sub-skills/configuration-model-zoo/SKILL.md` | Owns config inheritance, model-index/metafile navigation, model names, override validation, and config migration pointers. |
| Run image/folder/video-style inference, save prediction JSON or visualizations, use `DetInferencer`, `init_detector`, or `inference_detector` | `sub-skills/inference-visualization/SKILL.md` | Owns public inference APIs, output controls, device/palette choices, headless visualization, and deployment route selection. |
| Build training, resume, distributed, Slurm, testing, evaluation, or result-dump commands | `sub-skills/training-testing/SKILL.md` | Owns `tools/train.py`, `tools/test.py`, distributed launcher patterns, `--resume`, `--auto-scale-lr`, `work_dir`, and command validation. |
| Prepare datasets, convert image folders/annotations, configure COCO/VOC/Cityscapes/LVIS/OpenImages metrics, or debug transforms/evaluators | `sub-skills/datasets-evaluation/SKILL.md` | Owns dataset layouts, COCO-like schemas, custom dataset config, transforms, metrics, analysis tools, and tiny dataset helpers. |
| Add custom models, heads, losses, datasets, transforms, hooks, optimizer constructors, structures, or project plugins | `sub-skills/customization-extension/SKILL.md` | Owns registries, `custom_imports`, project templates, MMEngine integration, data structures, and migration/customization pitfalls. |

## Common Workflow Chains

### Config to Inference

1. Use `configuration-model-zoo` to select a compatible config and inspect inherited settings.
2. Use `inference-visualization` to choose `DetInferencer` or lower-level APIs.
3. Use root `references/troubleshooting.md` if imports fail before model construction.

### Custom Dataset Training

1. Use `datasets-evaluation` to validate annotation schema, class order, `metainfo`, and evaluator paths.
2. Use `configuration-model-zoo` to update config dataloaders, heads, and overrides.
3. Use `training-testing` to generate training/resume/test commands.
4. Use `customization-extension` only if a new dataset/transform class must be registered.

### New Component or Project Plugin

1. Use `customization-extension` for registry ownership, `custom_imports`, module layout, and smoke checks.
2. Use `configuration-model-zoo` to wire the new type into configs.
3. Use `training-testing` for safe launch command generation.

## Runtime Files

- `references/repo-provenance.md`: source commit, version, dirty state, and evidence baseline.
- `references/troubleshooting.md`: cross-cutting install/import/backend and dependency failures.
- `scripts/check_mmdet_environment.py`: safe import/version/API signature checker.

## Boundaries

This skill is self-contained guidance for future agents. It does not bundle MMDetection itself, pretrained checkpoints, datasets, videos, Docker images, or source-checkout-only tools. When a native MMDetection checkout is available, original demos/tests/tools can be used as optional verification candidates, but runtime instructions in this skill prefer bundled helpers or package APIs.
