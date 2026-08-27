---
name: segmentation
description: "Semantic segmentation with InternImage in MMSegmentation 0.x:
  config selection, train/test/image-demo commands, palettes, output handling,
  custom plugin registration, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# InternImage Segmentation Sub-skill

Use this sub-skill when a task is specifically about semantic segmentation with InternImage on MMSegmentation 0.x: selecting ADE20K, Cityscapes, COCO-Stuff, Mapillary, NYU-Depth-V2, or Pascal-Context configs; constructing train/evaluation/demo commands; handling segmentation palettes and output directories; or diagnosing InternImage MMSeg plugin/operator issues.

Do not use this sub-skill for classification, object detection, SAM instance segmentation, autonomous-driving baselines, or TensorRT/mmdeploy export planning except to identify that the request should route to a sibling sub-skill.

## Operating flow

1. Identify the user's local InternImage checkout and the segmentation goal: train, distributed train, evaluate, distributed evaluate, or image demo.
2. Pick a config from `references/config-catalog.md`. Keep the config and checkpoint from the same dataset/head/backbone family.
3. Build a command with `scripts/build_segmentation_command.py` instead of copying source launch snippets by hand. The helper is dry-run only: it prints a shell command and never launches training or inference.
4. Before recommending execution, check `references/workflows.md` for data, checkpoint, palette, output, and plugin-registration requirements.
5. If imports, palettes, output files, DCNv3, or distributed launch fail, use `references/troubleshooting.md` first.

## Runtime guardrails

- Full segmentation training/evaluation/demo runs are GPU-, dataset-, checkpoint-, and OpenMMLab-stack-dependent. Do not present command construction as runtime verification.
- The MMSeg stack used by this repository is the 0.x generation; avoid silently translating commands to MMSegmentation 1.x/2.x CLIs.
- Source labels such as `segmentation/train.py` and `segmentation/configs/ade20k/...` are provenance and command targets. Do not ask users to open the original files for instructions; use the bundled references and helper script.
- For heavy configs such as InternImage-H/G or Mask2Former, call out memory and DCNv3 CUDA-extension requirements before suggesting a run.

## Bundled references

- `references/workflows.md` - train/test/image-demo workflows, Slurm notes, plugin registration, output handling.
- `references/config-catalog.md` - distilled config families, dataset roots, palettes, checkpoint naming notes.
- `references/troubleshooting.md` - segmentation-specific failure modes and fixes.
- `scripts/build_segmentation_command.py` - deterministic command builder for train, dist-train, test, dist-test, and image-demo.
