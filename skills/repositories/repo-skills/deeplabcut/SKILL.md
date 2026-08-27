---
name: deeplabcut
description: "Route DeepLabCut markerless pose-estimation workflows, project
  setup, PyTorch training/inference, maDLC tracking, Model Zoo, post-processing,
  3D, and export tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# DeepLabCut repo skill

Use this skill when the user is working with the `deeplabcut` Python package for markerless animal or object pose estimation, including project setup, annotation data preparation, PyTorch training/evaluation/inference, multi-animal tracking, SuperAnimal/Model Zoo workflows, labeled-video outputs, 3D triangulation, and model export.

## First checks

- Package import check:

  ```python
  import deeplabcut
  print(deeplabcut.__version__)
  ```

- DeepLabCut supports Python 3.10-3.12. The default DeepLabCut 3.x engine is PyTorch; TensorFlow remains optional/legacy.
- Install the headless package for API/CLI-style workflows: `pip install deeplabcut`.
- Install GUI support only when the task needs it: `pip install "deeplabcut[gui]"`.
- Install exactly one TensorFlow extra only when legacy TensorFlow projects are in scope: `tf`, `tf-cu11`, `tf-cu12`, `tf-latest`, or `apple_mchips`.
- Run [scripts/check_deeplabcut_install.py](scripts/check_deeplabcut_install.py) when you need a safe local import, public API, launcher, and optional backend probe.

## Route by task

1. [install-and-project-setup](sub-skills/install-and-project-setup/SKILL.md)
   - Install/import questions, GUI or lite launcher behavior, package extras, project creation, adding videos, 3D project skeletons, and safe `config.yaml` or project-tree inspection.
2. [data-labeling-and-training-datasets](sub-skills/data-labeling-and-training-datasets/SKILL.md)
   - Frame extraction, label checking, annotation table formats, external data conversion, `create_training_dataset`, shuffles, train/test splits, and tiny safe fixture projects.
3. [pytorch-training-evaluation-inference](sub-skills/pytorch-training-evaluation-inference/SKILL.md)
   - DeepLabCut 3.x PyTorch training, evaluation, image/video inference, snapshot/device choices, `pytorch_config.yaml`, and model export.
4. [multi-animal-tracking](sub-skills/multi-animal-tracking/SKILL.md)
   - maDLC identity decisions, raw detections, tracklet conversion, stitching, transformer re-identification, and tracking failure recovery.
5. [model-zoo-superanimal](sub-skills/model-zoo-superanimal/SKILL.md)
   - SuperAnimal and Model Zoo no-training inference, pretrained projects, adaptation, transfer learning handoffs, custom checkpoints, and download/cache planning.
6. [postprocessing-3d-video-exports](sub-skills/postprocessing-3d-video-exports/SKILL.md)
   - Filtering, outlier refinement, dataset merge, labeled videos, trajectory plots, video utilities, 3D calibration/triangulation, and export outputs.

## Shared references

- [Repository provenance](references/repo-provenance.md) records the source version and evidence paths for refresh decisions.
- [Installation and entry points](references/installation.md) explains install flavors, launcher behavior, and backend choices.
- [API index](references/api-index.md) maps important public APIs to the owning sub-skill.
- [Compatibility notes](references/compatibility.md) summarizes PyTorch/TensorFlow, GUI, OpenVINO, FMPose3D, CPU/GPU, and optional dependency boundaries.
- [Troubleshooting](references/troubleshooting.md) covers cross-cutting import, install, launcher, backend, and path failures before routing to workflow-specific troubleshooting.

## Operating boundaries

- Do not run training, inference, model downloads, GUI launch, or video-writing steps until the user has confirmed the target project, data paths, outputs, and compute expectations.
- Treat DeepLabCut project `config.yaml` as the authority for project path, scorer, videos, bodyparts, individuals, training fractions, iteration, and engine.
- Use CPU-safe inspection and bundled planning scripts for diagnosis. GPU-backed training or inference is usually recommended for real workloads, but simple API/config checks can run on CPU.
- Do not mix TensorFlow extras in one environment. If a task is TensorFlow-specific, confirm the exact extra and Python/CUDA/Metal compatibility before installing or repairing packages.
- Keep source projects and generated outputs separate: DeepLabCut creates project artifacts such as `labeled-data/`, `training-datasets/`, `dlc-models-pytorch/`, prediction `.h5/.csv`, labeled videos, and exports under user-chosen project/output directories.
