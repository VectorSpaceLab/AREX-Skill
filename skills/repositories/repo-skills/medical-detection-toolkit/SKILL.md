---
name: medical-detection-toolkit
description: "Route MedicalDetectionToolkit research tasks across experiment
  configuration, medical-image data preparation, detector architecture,
  prediction/evaluation, and legacy CUDA compatibility while preserving the
  repository's unmaintained and version-sensitive boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MedicalDetectionToolkit

Use this repo skill when a task names MedicalDetectionToolkit/MDT or asks about
its legacy 2D/3D medical object-detection workflows, experiment configs, toy/
LIDC/PET-CT loaders, Retina U-Net/Mask R-CNN-style models, prediction
consolidation, evaluation, or custom NMS/RoIAlign extensions.

## First checks

1. Treat the exact source revision as part of the task. Read
   [repo provenance](references/repo-provenance.md) before deciding whether a
   current checkout can use this graph.
2. Expect a legacy environment: the published metadata pins Python-3.6-era
   dependencies including `torch==0.4.1`, and the README says the project is no
   longer maintained. Do not silently replace it with nnDetection; that is a
   separate framework.
3. Separate portable configuration/data/analysis guidance from exact detector
   execution. The latter imports old `torch.utils.ffi` CUDA wrappers and must
   pass the compatibility route before any model run.
4. For a new data path, validate a bounded copied/synthetic case first; never
   download clinical data or run destructive packing/deletion as a smoke test.

## Route by task

- **Configure an experiment, choose dimensions/models, inspect CLI modes/folds,
  create an experiment directory, or make a bounded toy fixture:** read
  [configuration-and-experiments](sub-skills/configuration-and-experiments/SKILL.md).
- **Prepare arrays/manifests, preserve label semantics, adapt toy/LIDC/PET-CT
  loaders, or reason about patching/tiling/augmentation:** read
  [data-and-preprocessing](sub-skills/data-and-preprocessing/SKILL.md).
- **Choose or explain MRCNN, U-FRCNN, RetinaNet, Retina U-Net, Detection U-Net,
  FPN/backbone, anchors, heads, losses, or model result contracts:** read
  [models-and-architectures](sub-skills/models-and-architectures/SKILL.md).
- **Run/inspect prediction modes, saved outputs, WBC, 2D-to-3D merging, ROI or
  patient metrics, CSVs, or monitoring plots:** read
  [inference-and-evaluation](sub-skills/inference-and-evaluation/SKILL.md).
- **Diagnose NMS/RoIAlign import/build/ABI/device issues:** read
  [cuda-extensions](sub-skills/cuda-extensions/SKILL.md) and stop at its
  compatibility gate before claiming model execution.

Cross-workflow requests should follow this order: configuration → data
contract → model choice → prediction/evaluation; insert CUDA compatibility at
the model boundary when a custom operator is imported.

## Installation and inspection guidance

For source checkout use, install into an isolated environment only after
choosing a dependency variant. The repository's historical requirements are
not a modern default; for metadata/API inspection, use
`python -m pip install --no-deps -e .` and then verify metadata with
`python -c "from importlib.metadata import version; print(version('medicaldetectiontoolkit'))"`.
This only proves package metadata; follow the leaf backend/data checks before
running a workflow. Exact reproduction requires the old pinned dependencies and
is a separate compatibility decision.

For a historical reproduction, use an isolated environment matching the
checkout's documented Python/PyTorch/CUDA ABI only if those artifacts are
actually available. For source/API inspection, use a modern isolated Python
only to inspect portable modules and record compatibility failures; a current
PyTorch CUDA tensor smoke does not validate the repository's custom extensions.
The package distribution is `medicaldetectiontoolkit` (source metadata version
`0.0.1`), while the checkout exposes top-level modules such as `models`,
`utils`, `predictor`, and `evaluator`.

Do not put source checkout paths, private environments, generated experiment
outputs, precompiled `.so`/`.o` files, or external datasets into a Researcher
workflow. Use the bundled validators and compatibility checker in the leaf
sub-skills; each is read-only or bounded by default.

## Shared failure policy

- If a loader fails, check package-version drift, axes, channel count, manifest
  names, and label semantics before changing the model.
- If an old detector import fails at `torch.utils.ffi`, classify it as a legacy
  ABI/toolchain block; do not patch imports or claim a CPU substitute.
- If WBC/evaluation fails, validate the result schema and keep raw prediction
  artifacts immutable before changing thresholds.
- If a path would overwrite data, copy it to a temporary workspace and stop for
  explicit review.

Read [cross-cutting troubleshooting](references/troubleshooting.md) for the
common install/import/data/runtime decision table. This root file is a router;
API tables, schemas, long workflows, and failure matrices live in the linked
leaf references.
