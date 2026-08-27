---
name: model-zoo-superanimal
description: "Route DeepLabCut Model Zoo and SuperAnimal pretrained inference,
  adaptation, pretrained projects, and custom checkpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# Model Zoo and SuperAnimal router

Use this sub-skill when a DeepLabCut task asks for Model Zoo or SuperAnimal pretrained models, no-training or zero-shot video inference, pretrained project creation, video adaptation, transfer learning from SuperAnimal weights, FMPose3D video inference, or custom pretrained checkpoints.

## Handle here

- Plan or call `deeplabcut.video_inference_superanimal(...)` for videos, destination folders, detector choices, scale lists, crops, confidence thresholds, labeled-video outputs, video adaptation, custom checkpoints, and FMPose3D 3D return payloads.
- Create a new pretrained Model Zoo project with `deeplabcut.create_pretrained_project(...)` when the user wants a project initialized from pretrained weights rather than a blank project.
- Recognize `deeplabcut.create_pretrained_human_project(...)` as the legacy TensorFlow full-human helper and prefer the more general pretrained-project API for new work.
- Explain SuperAnimal project families: quadruped, top-view mouse, human body, and the evidenced bird configuration.
- Prepare the SuperAnimal part of a transfer-learning plan, then route actual custom labeled dataset training to the PyTorch training sub-skill.

## Route elsewhere

- Installing extras, fixing import/backend/package compatibility, choosing PyTorch vs TensorFlow extras, or installing optional FMPose3D support: route to the root DeepLabCut install/compatibility guidance.
- Blank project creation, adding videos, and general `config.yaml` setup: route to `../install-and-project-setup/SKILL.md`.
- Frame extraction, labeling, training dataset creation, conversion tables, and custom labeled data preparation: route to `../data-labeling-and-training-datasets/SKILL.md`.
- Custom model training, evaluation, analyzing with trained project snapshots, and export after a training dataset exists: route to `../pytorch-training-evaluation-inference/SKILL.md`.
- Filtering predictions, outlier refinement, labeled-video details, trajectory plots, stereo camera calibration, triangulation, and generic 3D workflows: route to `../postprocessing-3d-video-exports/SKILL.md`.

## Read in order

1. [Model overview](references/model-overview.md) for model families, engine routing, API parameters, outputs, and cache/download behavior.
2. [Workflows](references/workflows.md) for no-training inference, video adaptation, pretrained projects, FMPose3D, and transfer-learning handoffs.
3. [Troubleshooting](references/troubleshooting.md) for model names, downloads, detectors, scale shifts, custom checkpoints, adaptation failures, and optional dependencies.
4. [Inference planner script](scripts/plan_superanimal_inference.py) when you need a no-download argument checklist before running real inference.

## Operating reminders

- Treat real Model Zoo inference, adaptation, and pretrained project creation as download-capable operations unless the user supplies already-present custom checkpoint paths or confirms the cache is populated.
- For PyTorch top-down SuperAnimal animal models, plan both a pose model and detector. For TensorFlow bottom-up `dlcrnet`, plan scale choices instead of detector choices.
- Do not start long adaptation or training just to answer a planning question. Use the bundled planner script and hand off to the appropriate sub-skill when the task crosses this sub-skill boundary.
- Keep runtime instructions portable: use user-provided paths, relative project paths, or placeholders; never rely on a repository checkout, source examples, source tests, local logs, or private environment locations.
