---
name: data-and-training
description: "Route U-2-Net dataset validation, transform inspection, and safe
  retraining preparation without starting long training by default."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data and Training

Use this sub-skill when the task is about U-2-Net training data layout, preprocessing transforms, batch/sample fields, the multi-side BCE training loop, or preparing a safe retraining run.

## Start here

1. Confirm the user has a DUTS-style training root or a deliberately adapted equivalent.
2. Validate image/mask stem pairing with [`scripts/validate_training_layout.py`](scripts/validate_training_layout.py) before discussing a training launch.
3. Inspect one representative image and optional label with [`scripts/inspect_data_pipeline.py`](scripts/inspect_data_pipeline.py) to confirm RescaleT/ToTensorLab-like output shapes and ranges.
4. Use [training workflow](references/training-workflow.md) for the exact source training settings and safe adaptation checklist.

Do **not** start the full training loop by default. The source loop is configured for `epoch_num=100000` and data-dependent long execution; require explicit user approval and a bounded run plan first.

## Core facts

- The training dataset is expected under `train_data/DUTS/DUTS-TR/DUTS-TR/im_aug/*.jpg` with matching masks under `train_data/DUTS/DUTS-TR/DUTS-TR/gt_aug/*.png` by the same filename stem.
- `SalObjDataset` yields sample dictionaries with `imidx`, `image`, and `label` keys; training composes `RescaleT(320)`, `RandomCrop(288)`, and `ToTensorLab(flag=0)`.
- The source training loop defaults to `model_name='u2net'`, `batch_size_train=12`, Adam learning rate `0.001`, checkpoint save frequency `2000` iterations, and summed BCE losses across seven side outputs.
- `model_name` can be changed to `u2netp`; keep checkpoint paths and model constructor consistent with that choice.

## References

- [Data formats](references/data-formats.md): dataset layout, sample dict schema, and transform behavior.
- [Training workflow](references/training-workflow.md): training hyperparameters, loss setup, checkpoint behavior, and safe retraining preparation.
- [API reference](references/api-reference.md): distilled dataset/transform APIs and bundled script CLI contracts.
- [Troubleshooting](references/troubleshooting.md): missing data, mismatched stems, crop size, mask shape, memory, and checkpoint failures.

## Routing boundaries

- Route salient-object or human segmentation inference to `salient-object-inference`.
- Route portrait inference, face crops, and portrait compositing to `portrait-workflows`.
- Route U2NET/U2NETP architecture internals and checkpoint shape debugging to `model-architecture`.
- Keep PaddleHub/Gradio demos out of this sub-skill unless the user is explicitly asking about optional demos rather than retraining.
