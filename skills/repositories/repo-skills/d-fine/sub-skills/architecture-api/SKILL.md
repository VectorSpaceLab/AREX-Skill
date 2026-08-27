---
name: architecture-api
description: "Inspect and modify D-FINE architecture, registry, YAMLConfig,
  model components, deploy mode, and API behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# D-FINE Architecture and API Router

Use this sub-skill when a task is about D-FINE internals rather than just running a training or inference command: YAML registry construction, component names in configs, model assembly, D-FINE decoder behavior, deploy mode, criterion/postprocessor APIs, checkpoint shape mismatches, or adding a custom component.

## Route here for

- Explaining how `YAMLConfig`, `GLOBAL_CONFIG`, `register()`, and `create()` turn YAML `type` names into Python objects.
- Inspecting model components such as `DFINE`, `HGNetv2`, `HybridEncoder`, `DFINETransformer`, `DFINECriterion`, `HungarianMatcher`, and `DFINEPostProcessor`.
- Diagnosing `The module ... is not registered`, `Missing inject config`, invalid `type` entries, or component channel/stride mismatches.
- Understanding deploy-mode conversion before ONNX export or inference.
- Planning code changes for a new backbone, encoder, decoder, criterion, matcher, postprocessor, optimizer, transform, dataset, or evaluator.
- Checking a config/model safely with `scripts/inspect_dfine_model.py` before long training or export.

## Route away

- Dataset paths, COCO/custom annotation schemas, `num_classes`, `remap_mscoco_category`, and YAML catalog selection: use [../data-and-configs/SKILL.md](../data-and-configs/SKILL.md).
- Training, `--test-only`, resume, tuning, DDP, AMP, EMA, or output directories: use [../training-evaluation/SKILL.md](../training-evaluation/SKILL.md).
- PyTorch/ONNX/OpenVINO/TensorRT inference, export, and benchmark commands: use [../inference-export/SKILL.md](../inference-export/SKILL.md).

## First actions

1. Read [references/api-reference.md](references/api-reference.md) for verified signatures, registry semantics, and component relationships.
2. Read [references/model-architecture.md](references/model-architecture.md) when the task asks about D-FINE, FDR/GO-LSD-related knobs, model sizes, deploy mode, or component responsibilities.
3. Run `python scripts/inspect_dfine_model.py --repo-root <d-fine-checkout> --config <config.yml> --build-model` for a safe import/config/model probe. Add `--allow-pretrained` only when the user wants pretrained backbone lookup/download behavior.
4. For errors, use [references/troubleshooting.md](references/troubleshooting.md) before editing code or config.

## Safety and evidence rules

- Disable HGNetv2 pretrained lookup for inspection unless the user explicitly wants to test pretrained weight availability.
- Treat config keys and registered class names as case-sensitive.
- Prefer inspecting config construction and parameter counts before attempting a dummy forward; full forward, training, or evaluation can be slow and data/backend dependent.
- When adding a component, update both the Python registration/import path and the YAML `type`/injection references that select it.
