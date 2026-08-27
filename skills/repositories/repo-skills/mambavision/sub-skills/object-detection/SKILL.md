---
name: object-detection
description: "Use MambaVision as an MMDetection Cascade Mask R-CNN backbone on
  COCO, with tiny/small/base configs, checkpoint path adaptation, train/test
  command planning, and OpenMMLab failure diagnosis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MambaVision Object Detection

Use this sub-skill for the published MambaVision object-detection setup: Cascade Mask R-CNN on COCO with the bundled detection configs and adapter.

## Route here for

- choosing the tiny, small, or base detection config
- adapting backbone pretrained paths and detector checkpoint paths
- preparing COCO train/val annotation layout
- building single-GPU or Slurm train/test commands
- reading bbox and segm metrics from MMDetection output
- diagnosing `MM_mamba_vision` registry, import, version, and checkpoint issues

## Route elsewhere

- classification checkpoints, model catalog, or ImageNet validation -> `../classification/SKILL.md`
- ADE20K / MMSegmentation backbone use -> `../semantic-segmentation/SKILL.md`
- generic MMDetection utility folders that are not MambaVision-specific -> do not treat them as this workflow

Start with:

- `references/configuration.md`
- `references/backbone-adapter.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/print_mmdet_command.py`

Safe preflight checks:

- `python scripts/print_mmdet_command.py --help` to inspect the bundled command-template helper.
- In the user's target MMDetection project, run the selected training/test entry point's `--help` before launching any heavy job.

This skill is a router and reference hub. It does not launch training jobs or download checkpoints on its own.
