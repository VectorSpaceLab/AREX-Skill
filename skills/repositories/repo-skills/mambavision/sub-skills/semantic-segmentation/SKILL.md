---
name: semantic-segmentation
description: "Use MambaVision as an MMSegmentation UPerNet backbone on ADE20K,
  including config selection, checkpoint adaptation, data layout, single-GPU or
  Slurm command planning, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MambaVision Semantic Segmentation

Use this sub-skill when the task is about the published MambaVision UPerNet semantic segmentation workflow on ADE20K.

It covers:
- choosing the tiny, small, base, or L3 config
- adapting backbone checkpoint paths and decoder channels
- preparing ADE20K in the expected folder layout
- generating safe single-GPU train/test commands or adapted Slurm launch patterns
- diagnosing registry, import, channel, crop-size, AMP, and dataset layout failures

Route elsewhere:
- classification checkpoints, ImageNet validation, or the model catalog -> `../classification/SKILL.md`
- COCO detection or Cascade Mask R-CNN workflows -> `../object-detection/SKILL.md`
- generic MMSegmentation utilities, dataset converters, or deployment helpers are upstream framework topics and are not selected workflows here

Start with:
1. `references/configuration.md` to choose the config, checkpoint family, crop size, and optimizer wrapper.
2. `references/workflows.md` for single-GPU and Slurm train/test command patterns.
3. `references/backbone-adapter.md` for `MM_mamba_vision` registration, output channels, and checkpoint loading behavior.
4. `references/troubleshooting.md` when imports, ADE20K paths, checkpoint shapes, or AMP settings fail.
5. `scripts/print_mmseg_command.py --help` to see the safe command builder surface.

Expected runtime signals:
- The selected MMSegmentation test entry point reports `aAcc`, `mIoU`, and `mAcc` for ADE20K validation.
- The published ADE20K results recorded in `references/configuration.md` are 46.0 / 48.2 / 49.1 / 53.2 mIoU for tiny / small / base / L3.

Prerequisites:
- A CUDA-enabled PyTorch + OpenMMLab stack with `mmengine==0.10.1`, `mmcv==2.1.0`, `opencv-python-headless`, `mmsegmentation==1.2.2`, `mmdet==3.3.0`, and `mmpretrain==1.2.0`.
- The ADE20K dataset tree under `ADEChallengeData2016` with `images/training`, `images/validation`, `annotations/training`, and `annotations/validation`.
- The segmentation CLI in the target project must be able to import the `MM_mamba_vision` adapter; add the target project's adapter directory to `PYTHONPATH` if the framework registry cannot find it.
