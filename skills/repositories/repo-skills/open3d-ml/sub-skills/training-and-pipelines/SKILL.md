---
name: training-and-pipelines
description: "Guides Open3D-ML config-driven training, inference, evaluation,
  registry use, and model selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training and Pipelines

Use this sub-skill when you want to train, test, or run inference with an
Open3D-ML model, or when you need to construct a config-driven pipeline from a
model, dataset, and pipeline definition.

## What this sub-skill covers

- Repo config files and the `Config` loader/merge logic.
- Registry-driven creation of datasets, models, and pipelines.
- Semantic segmentation and object detection workflows.
- PyTorch model and pipeline usage, with TensorFlow described as an optional
  backend when a compatible build exists.
- Safe command construction for a pipeline launcher without running training.
- Model zoo and checkpoint selection guidance.

## When to route here

- "How do I train RandLANet on SemanticKITTI?"
- "How do I run inference with PointPillars?"
- "Why does a config override not take effect?"
- "How do I build the right model/dataset/pipeline combination?"
- "How do I compare semantic segmentation and object detection workflows?"

## Use the bundled helper

Run `scripts/build_run_pipeline_command.py` when you want a safe, non-training
summary of how a config-driven pipeline would be launched.

## Reading order

1. Read `references/config-reference.md` for `Config` loading and merge rules.
2. Read `references/workflows.md` for direct API and config-driven usage.
3. Read `references/model-overview.md` for model families and dataset pairings.
4. Read `references/troubleshooting.md` when a registry or version mismatch
   occurs.

## Boundary notes

Include:
- Model/dataset/pipeline selection and command construction.
- Config file anatomy and override semantics.
- Direct API or launcher-shaped workflows for training, testing, and inference.

Exclude:
- Dataset layout validation; use `datasets-and-preprocessing`.
- Visualization and TensorBoard details; use `visualization-and-extensions`.
- Generic install/backend troubleshooting; use `install-and-inspect`.

## Minimal workflow

1. Pick a config file or a model/dataset/pipeline trio.
2. Resolve the class names via the registry.
3. Check the command shape with `scripts/build_run_pipeline_command.py`.
4. Execute the direct API or launcher in a suitable environment.

## Good handoff signals

A future agent should be able to answer these from this sub-skill alone:

- How `Config.load_from_file` and CLI-style overrides interact.
- Which models are available for segmentation and detection.
- How to detect a registry miss versus a backend mismatch.
- Which workflows are CPU-safe versus backend-dependent.
