---
name: data-and-configs
description: "Select, validate, and safely modify D-FINE dataset and YAML configs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# D-FINE data and configs router

Use this sub-skill when the task is about D-FINE dataset layout, annotation sanity, choosing a COCO/Objects365/CrowdHuman/VOC/custom config, changing YAML fields, adjusting class counts, remap policy, batch size, input size, or doing a safe dataset/config preflight.

Start with [references/data-and-configs.md](references/data-and-configs.md). For failures, use [references/troubleshooting.md](references/troubleshooting.md). For COCO-format annotation checks, run the bundled validator in [scripts/validate_detection_dataset.py](scripts/validate_detection_dataset.py).

## Route here for

- Selecting a model-size config for COCO, Objects365, Objects365-to-COCO, Objects365-to-custom, CrowdHuman, VOC, or custom COCO-format data.
- Explaining how `__include__`, `task`, `num_classes`, `remap_mscoco_category`, dataloader fields, transforms, `total_batch_size`, and input size interact.
- Preparing a custom dataset config safely before training or evaluation.
- Preflighting Object365 remap/resize assumptions without running long or mutating dataset scripts.
- Diagnosing malformed COCO JSON, missing images/annotations, wrong category IDs, class-count mistakes, or batch-size/world-size divisibility errors.

## Route away

- Training, evaluation, resume, tuning, checkpoints, DDP launch, AMP, or output directories: use [../training-evaluation/SKILL.md](../training-evaluation/SKILL.md).
- PyTorch/ONNX/OpenVINO/TensorRT inference, export, or benchmark commands that reuse a config: use [../inference-export/SKILL.md](../inference-export/SKILL.md).
- Model internals, registry construction, class-head mapping code, component changes, or deploy-mode behavior: use [../architecture-api/SKILL.md](../architecture-api/SKILL.md).

## Quick operating loop

1. Identify the dataset family and desired model size (`n`, `s`, `m`, `l`, or `x`).
2. Pick the nearest config family from the catalog in [references/data-and-configs.md](references/data-and-configs.md).
3. For custom COCO-format data, set `num_classes`, `remap_mscoco_category`, train/val `img_folder`, and train/val `ann_file` before constructing a training command.
4. Validate annotations with `python scripts/validate_detection_dataset.py --annotation <instances.json> --image-root <images-dir> --dataset-config <dataset-or-final-config.yml>`.
5. If a workflow proceeds to launch training/evaluation or inference/export, hand off to the sibling sub-skill instead of continuing here.
