---
name: yolop
description: "Guides YOLOP multi-task driving perception workflows for BDD100K
  data preparation, training, evaluation, PyTorch demo inference, ONNX export,
  and TensorRT deployment planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# YOLOP Repo Skill

Use this skill when a task names YOLOP, "You Only Look Once for Panoptic driving Perception", BDD100K driving perception, a combined traffic-object detection + drivable-area segmentation + lane-line segmentation model, or YOLOP files such as `lib.config.default`, `lib.models.YOLOP`, `tools/demo.py`, `tools/train.py`, `export_onnx.py`, or `test_onnx.py`.

Do not use this skill for generic Ultralytics YOLO workflows, unrelated lane-detection repos, or tasks that only need a generic PyTorch/ONNX tutorial.

## Repository mental model

- YOLOP is a research-style Python repo, not an installable package with `pyproject.toml`/`setup.py`. Most workflows import the top-level `lib` package from a YOLOP checkout, so bundled helper scripts accept `--repo-root` and add that checkout to `sys.path` explicitly.
- The default network is `MCnet` from `lib.models.YOLOP.get_net(cfg)`: one YOLO-style detection head for traffic objects, one drivable-area segmentation head, and one lane-line segmentation head.
- The central configuration object is `lib.config.cfg` from `lib/config/default.py`; dataset roots, training/evaluation toggles, image size, GPU list, batch sizes, losses, and checkpoint paths live there.
- The README-documented baseline is Python 3.7 with PyTorch 1.7+/torchvision 0.8+. For modern environments, keep torch and torchvision compatible, install `requirements.txt`, and run the bundled smoke checks before trusting a workflow.

Read [references/model-overview.md](references/model-overview.md) for model outputs, architecture variants, checkpoints, and Torch Hub notes. Read [references/configuration.md](references/configuration.md) before changing dataset paths or training flags. Read [references/troubleshooting.md](references/troubleshooting.md) when imports, paths, devices, or optional backends fail.

## Start with a safe install/import smoke

From any environment that can import torch/torchvision, OpenCV, yacs, and the repo requirements, run the bundled check against a live YOLOP checkout:

```bash
python scripts/check_install.py --repo-root /path/to/YOLOP --device cpu --image-size 128
```

Use `--device cuda:0` only after installing a CUDA-capable torch/torchvision pair and confirming that the requested GPU is available. CPU checks validate API shape and ONNX-style functional behavior; they do not validate CUDA speed, TensorRT, or full BDD100K training.

## Route by task

| User task | Read next | Why |
| --- | --- | --- |
| Prepare BDD100K directories, detection JSONs, lane/drivable masks, or validate data roots | [sub-skills/data-preparation/SKILL.md](sub-skills/data-preparation/SKILL.md) | Owns dataset layout, label conversion, mask generation, and data-path failures. |
| Configure or run training, staged/single-task modes, auto-anchor, validation/evaluation, metrics, checkpoints, or DDP launch | [sub-skills/training/SKILL.md](sub-skills/training/SKILL.md) | Owns `tools/train.py`, `tools/test.py`, losses, metrics, and train/eval config semantics. |
| Run PyTorch demo inference on images, videos, streams, load checkpoints, or interpret detection/segmentation visual outputs | [sub-skills/inference/SKILL.md](sub-skills/inference/SKILL.md) | Owns `tools/demo.py`, `hubconf.py`, `DemoDataset`, NMS, masks, and visualization. |
| Export to ONNX, run ONNXRuntime inference, prepare TensorRT `.wts`, or reason about TensorRT/ZED deployment constraints | [sub-skills/export/SKILL.md](sub-skills/export/SKILL.md) | Owns `export_onnx.py`, `test_onnx.py`, `.wts` conversion, and deployment limitations. |

## Common commands from the repo contract

These are the source workflow shapes that the sub-skills expand into safe, configurable recipes:

```bash
# Train after configuring dataset roots in lib/config/default.py
PYTHONPATH=. python tools/train.py

# Distributed training; only use after matching CUDA/PyTorch and data are ready
PYTHONPATH=. python -m torch.distributed.launch --nproc_per_node=N tools/train.py

# Evaluate on BDD100K validation data
PYTHONPATH=. python tools/test.py --weights weights/End-to-end.pth

# PyTorch demo inference on a file or folder
PYTHONPATH=. python tools/demo.py --source inference/images --weights weights/End-to-end.pth --device cpu

# ONNXRuntime inference with an existing exported model
PYTHONPATH=. python test_onnx.py --weight yolop-640-640.onnx --img test.jpg
```

Prefer the bundled helper scripts in the relevant sub-skill when you need safer output paths, source-root isolation, or a small smoke test that does not mutate a checkout.

## Verification and backend limits

The generated skill was verified against CPU source imports, model construction, dummy forward-pass shapes, ONNX export mechanics using the export-specific model wrapper, ONNXRuntime CPU inference, and parser/help checks. Full BDD100K training/evaluation, benchmark speed numbers, CUDA throughput, TensorRT engine build, and ZED-camera runtime were not executed. Treat those as documented workflows requiring the prerequisites named in the sub-skills.

Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a current checkout. If commit, dirty state, package structure, or public workflow files differ, refresh this skill before relying on detailed file-level guidance.
