---
name: "adelai-det"
description: "Routes AdelaiDet users through legacy-compatible setup, model
  config selection, training/evaluation, demos, text spotting, dataset
  preparation, and export/conversion workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# AdelaiDet

AdelaiDet is an AIM/Adelaide Detectron2-based research platform for instance-level recognition: object detection, instance segmentation, text spotting, keypoint detection, and related deployment utilities. Use this repo skill when a task names AdelaiDet, `adet`, FCOS, BlendMask, CondInst, BoxInst, SOLOv2, BAText/ABCNet, MEInst, FCPose, DenseCL, or asks how to train, evaluate, demo, prepare data, or export models for this repository.

## Start here

- Read `references/repo-provenance.md` before refreshing the skill or checking whether the source snapshot matches a task.
- Read `references/compatibility.md` before installing or building AdelaiDet. This repo is legacy Detectron2 code and needs a version-compatible PyTorch/CUDA stack.
- Read `references/model-overview.md` to choose a config family and understand which workflow owns it.
- Read `references/api-reference.md` for the verified import surface, config keys, registries, custom ops, and public CLIs.
- Read `references/troubleshooting.md` when install, import, CUDA extension, CLI, dataset, checkpoint, or export errors appear.

## Install and smoke-check

The verified runtime stack is CUDA-capable and legacy-compatible:

- Python 3.9
- PyTorch 1.10.x with CUDA 11.3
- TorchVision 0.11.x
- Detectron2 0.6 built for the same PyTorch/CUDA pair
- AdelaiDet installed editable from a matching source checkout
- Pillow `<10`, rapidfuzz `<3`, NumPy `1.23.x`, and OpenCV headless `4.8.x`

Do **not** start with a modern PyTorch 2.x stack for unmodified AdelaiDet CUDA extensions: the source includes legacy THC headers in `ml_nms.cu` that are absent from PyTorch 2.x.

After installation, run the skill-owned smoke check:

```bash
python scripts/check_install.py --cuda-ops
```

Run without `--cuda-ops` only when you intentionally need a CPU/import-only diagnosis.

## Route map

### `setup-build`
Use this route for environment creation, Detectron2/PyTorch/CUDA versioning, editable builds, compiled `adet._C` checks, custom op smoke tests, and install failure diagnosis.

Read:
- `sub-skills/setup-build/SKILL.md`
- `sub-skills/setup-build/references/setup-build.md`
- `sub-skills/setup-build/references/runtime-checks.md`

### `train-eval`
Use this route for Detectron2-style AdelaiDet training, evaluation, config overrides, model-family selection for training, checkpoints, distributed launches, and output directory expectations.

Read:
- `sub-skills/train-eval/SKILL.md`
- `sub-skills/train-eval/references/train-eval-workflows.md`
- `sub-skills/train-eval/references/config-selection.md`

### `demo-visualize`
Use this route for image/video/webcam demos, `VisualizationDemo`, confidence thresholds, text/non-text visualizations, and dataset visualization.

Read:
- `sub-skills/demo-visualize/SKILL.md`
- `sub-skills/demo-visualize/references/demo-workflows.md`
- `sub-skills/demo-visualize/references/visualization.md`

### `text-spotting`
Use this route for ABCNet/BAText, BezierAlign, text datasets, custom dictionaries, lexicons, text evaluation, and OCR-specific pitfalls.

Read:
- `sub-skills/text-spotting/SKILL.md`
- `sub-skills/text-spotting/references/text-workflows.md`
- `sub-skills/text-spotting/references/text-data-and-eval.md`

### `data-prep`
Use this route for COCO/PIC/LVIS/text dataset layouts, semantic mask generation, dataset registration, mapper expectations, MEInst mask encoding, and data validation.

Read:
- `sub-skills/data-prep/SKILL.md`
- `sub-skills/data-prep/references/dataset-preparation.md`
- `sub-skills/data-prep/references/data-formats.md`

### `export-convert`
Use this route for checkpoint key conversion, optimizer stripping, FCOS/BlendMask weight migration, ONNX export, and optional Caffe/NCNN/TensorRT deployment caveats.

Read:
- `sub-skills/export-convert/SKILL.md`
- `sub-skills/export-convert/references/export-and-checkpoints.md`
- `sub-skills/export-convert/references/onnx-export.md`

## Skill-owned scripts

- `scripts/check_install.py` — verify import, Detectron2 registries, config keys, and optionally CUDA custom ops.
- Sub-skill scripts wrap or adapt the repository workflows with preflight validation. When a script asks for `--repo-root`, pass a source checkout matching the provenance baseline or a refreshed AdelaiDet checkout.

## Operating cautions

- Full training, evaluation, demos with real images, and ONNX runtime validation need external datasets, model weights, and sometimes extra runtimes. Use help/dry-run checks first.
- ONNX/Caffe/NCNN/TensorRT shell pipelines from the source repository are reference-only here because they assume external workspaces and large artifacts.
- Keep installation/build issues routed to `setup-build`; do not debug model configs until `scripts/check_install.py --cuda-ops` passes for CUDA workflows.
