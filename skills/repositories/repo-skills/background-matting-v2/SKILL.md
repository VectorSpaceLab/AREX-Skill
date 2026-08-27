---
name: background-matting-v2
description: "Routes BackgroundMattingV2 tasks for background matting inference,
  export, and training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# BackgroundMattingV2

BackgroundMattingV2 is a computer-vision repo for high-resolution background
matting with a source-image / background-image pair. Use this root skill as a
router, not as a full manual.

## Start here

- Read `references/repo-provenance.md` when you need to check whether this skill
  still matches the repository checkout.
- Run `scripts/check_env.py` first when you only need a quick import and tiny
  forward smoke.
- Read `references/workflows.md` for the high-level route map and the decision
  points between inference, export, and training.
- Read `references/api-reference.md` for verified model and dataset signatures.
- Read `references/data-formats.md` before touching `data_path.py` or paired
  foreground/alpha/background directories.
- Read `references/backend-compatibility.md` before choosing PyTorch,
  TorchScript, or ONNX paths.
- Read `references/troubleshooting.md` for cross-cutting install, import, and
  backend issues.

## Install and inspect

This repo is source-tree based rather than a packaged wheel. For inspection,
create an isolated Python environment, install the runtime stack used by the
repo workflows, and then import the source modules from a checkout of this repo.
The verified inspection stack used for this skill was Python 3.11 with:

- `torch` + matching `torchvision`
- `kornia`
- `opencv-python`
- `onnx`
- `onnxruntime`
- `tensorboard`
- `tqdm`

A quick smoke is:

```bash
python scripts/check_env.py --repo-root <repo-checkout> --device cuda
```

Use `--device cpu` when you only need importability and tiny forward coverage. Add `onnx` when you want the ONNX smoke helper to validate export support.

## Route map

### Inference and demo
Use `sub-skills/inference-and-demo/` when the task is about:

- `inference_images.py`
- `inference_video.py`
- `inference_webcam.py`
- `inference_speed_test.py`
- choosing model type, backbone, refine mode, device, or output types
- understanding source/background pairing and alignment behavior

Read `sub-skills/inference-and-demo/SKILL.md` for the trigger terms and linked
workflow helpers.

### Export and backend compatibility
Use `sub-skills/export-and-backends/` when the task is about:

- `export_torchscript.py`
- `export_onnx.py`
- TorchScript attribute hoisting
- ONNX patch crop/replace compatibility choices
- validating export/runtime combinations

Read `sub-skills/export-and-backends/SKILL.md` when you need conversion steps or
backend troubleshooting.

### Training and data setup
Use `sub-skills/training/` when the task is about:

- `train_base.py`
- `train_refine.py`
- `data_path.py`
- paired foreground/alpha/background directory layout
- training checkpoints, logs, and benchmark evaluation
- CUDA/DDP assumptions and dataset-name selection

Read `sub-skills/training/SKILL.md` before configuring data paths or starting a
training run.

## Public surface summary

The public source-root modules you are expected to know are `model`, `dataset`,
`inference_utils`, and `data_path`. The primary classes are `MattingBase` and
`MattingRefine`. The main inference CLIs work with source/background image or
video pairs and can optionally apply homographic alignment.

## What not to do

- Do not send future agents back to the original repo docs or scripts when a
  bundled reference or script exists here.
- Do not assume training or webcam workflows are safe to run without the right
  hardware, data, and display devices.
- Do not treat CPU importability as proof of CUDA readiness.

## Local entry points

- `scripts/check_env.py`
- `sub-skills/inference-and-demo/scripts/smoke_forward.py`
- `sub-skills/export-and-backends/scripts/check_export_support.py`
- `sub-skills/training/scripts/check_data_layout.py`
