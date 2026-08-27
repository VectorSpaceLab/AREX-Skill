---
name: data-training
description: "Validate datasets, understand augmentation, and plan SSD.PyTorch
  training commands."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# data-training

Use this operating sub-skill when a Researcher needs to prepare or sanity-check SSD.PyTorch training inputs before launching a long training run. It covers VOC/COCO dataset layout, annotation transforms, SSD data augmentation, collation, training command planning, checkpoints, base VGG weights, Visdom, and CPU/CUDA handling.

## Fast routing

- For dataset directory checks, first read [references/datasets-and-augmentation.md](references/datasets-and-augmentation.md), then run the bundled validator:
  - `python scripts/validate_dataset_layout.py --dataset voc --root VOCDEVKIT_ROOT --require-train`
  - `python scripts/validate_dataset_layout.py --dataset coco --root COCO_ROOT --require-train`
- For training command construction, read [references/training-workflow.md](references/training-workflow.md), then generate templates with:
  - `python scripts/plan_training_command.py --dataset VOC --dataset-root VOCDEVKIT_ROOT --cuda true`
  - `python scripts/plan_training_command.py --dataset COCO --dataset-root COCO_ROOT --cuda true`
- For startup failures, missing files, import errors, empty targets, or CUDA surprises, read [references/troubleshooting.md](references/troubleshooting.md).

## Operating boundaries

This sub-skill owns:

- VOC and COCO training dataset skeletons and split-file expectations.
- VOC/COCO annotation transform outputs and class-count implications.
- `BaseTransform`, `SSDAugmentation`, and `detection_collate` behavior.
- `train.py` option planning, required files, checkpoints, learning-rate schedule, optional Visdom, and CUDA/CPU flags.
- Safe preflight commands and JSON-producing helper scripts.

Route out of this sub-skill when the request is not about data or training setup:

- Model construction, SSD priors, detection heads, loss internals, and inference model behavior: `../model-inference/SKILL.md`.
- Evaluation, test-time detection, demo notebook/webcam usage, and mAP reporting: `../evaluation-demos/SKILL.md`.

## Non-negotiable safety

- Do not execute dataset download scripts or bundle network download logic. The original dataset scripts are reference-only because they perform large downloads, extraction, copies, and deletes.
- Treat full training as external, data-heavy, and long-running. Only plan commands unless the user explicitly asks to run training in an appropriate Researcher session.
- Keep commands explicit about `--dataset_root`, `--save_folder`, `--basenet`, `--resume`, `--cuda`, `--batch_size`, and `--num_workers` rather than relying on hidden local defaults.
- Remember the COCO label-map import caveat: importing the package-level `data` module can fail before argument parsing if the default COCO label map is absent at the home-derived default COCO location.

## Minimal workflow

1. Identify target dataset: VOC or COCO.
2. Validate the layout with `scripts/validate_dataset_layout.py`; fix missing split files, annotation files, images, COCO JSON files, or label-map placement before training.
3. Confirm required training files:
   - Fresh training needs `vgg16_reducedfc.pth` under the configured save folder.
   - Resume training needs a checkpoint compatible with the selected dataset/model configuration.
4. Generate a command plan with `scripts/plan_training_command.py` and review the emitted notes.
5. If the user asks to execute training, warn about runtime/data cost, CUDA preference, and dependency/version constraints before running anything.
