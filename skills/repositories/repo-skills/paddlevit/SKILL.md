---
name: paddlevit
description: "Guide PaddleViT computer-vision workflows for transformer and MLP
  image classification, object detection, semantic segmentation, DINO
  self-supervision, GANs, configuration, distributed/AMP execution, and Paddle
  deployment with explicit data, backend, and checkpoint boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PaddleViT

Use this skill when a task names PaddleViT/PPViT, its standalone model
folders, PaddlePaddle vision transformers, or a workflow that matches one of
its classification, detection, segmentation, self-supervised, GAN, or export
surfaces. PaddleViT is a collection of source-rooted projects, not one
installable Python package: each model folder commonly has its own `config.py`,
model module, dataset code, and entry script.

## Start with a bounded plan

Before writing a command, record:

1. task family and exact model directory;
2. operation: inspect, configure, train, evaluate, predict, export, or port;
3. YAML config, recursive `BASE` files, data root/split, checkpoint prefix, and
   output directory;
4. expected device (`cpu`, one CUDA device, or distributed CUDA), budget, and
   whether downloads or long training are permitted;
5. preprocessing (channel order, resize/crop, normalization) and expected
   output shape/metric.

Run the read-only environment probe before attributing failures to a model:

```bash
python scripts/check_paddlevit_environment.py --help
python scripts/check_paddlevit_environment.py --json
```

Install PaddlePaddle using the official wheel that matches the host and CUDA
runtime. The repository documents PaddlePaddle 2.1-era APIs; current releases
may need a per-model smoke or a small compatibility patch. Add `yacs` and
`pyyaml` for the shared configuration pattern. Segmentation additionally uses
OpenCV, SciPy, and `cityscapesScripts`; COCO detection uses `pycocotools`; GAN
LSUN workflows use `lmdb`. Do not install every optional dependency or download
weights/data merely to inspect a config.

## Route by user intent

- [Classification](sub-skills/classification/SKILL.md): ViT, DeiT, Swin,
  VOLO, CSwin, PVTv2, BEiT, mobile/MLP/Conv/Rep families, MAE fine-tuning,
  ImageNet-style data, and facial-expression Swin.
- [Detection](sub-skills/detection/SKILL.md): DETR, Swin/PVTv2 detection,
  COCO layout, transforms, matching, RPN/RoI/FPN, train/eval and post-process.
- [Segmentation](sub-skills/segmentation/SKILL.md): SETR, UperNet, DPT,
  Segmenter, Trans2Seg, SegFormer, TopFormer, dataset layouts, demo and mIoU
  validation.
- [Self-supervised](sub-skills/self-supervised/SKILL.md): DINO multi-crop
  teacher/student training, checkpoint/resume, AMP and multi-GPU boundaries.
- [Generative](sub-skills/generative/SKILL.md): TransGAN, Styleformer,
  CIFAR/STL10/CelebA/LSUN-LMDB data and FID/PSNR/SSIM evaluation.
- [Deployment and operations](sub-skills/deployment-and-operations/SKILL.md):
  config precedence, environment diagnosis, AMP/distributed launch, static
  export, Paddle Inference, prediction, quantization and optional weight port.

Read [model-catalog.md](references/model-catalog.md) when a request does not
name a model family. Read [configuration.md](references/configuration.md) when
YAML, CLI overrides, source-root imports, or checkpoint paths are involved.
Read [troubleshooting.md](references/troubleshooting.md) before retrying an
import, backend, data, export, or checkpoint failure.

## Source-root discipline

Run one family in one fresh process. Put only the selected model directory (and
its documented sibling utilities) on `PYTHONPATH`; many folders contain bare
modules named `config`, `datasets`, `utils`, or `models`. Never combine several
model directories in one interpreter and assume imports are unambiguous.
Generated helper scripts are source-independent and must not be used as proof
that a source model's current API is compatible.

## Evidence and safety gates

A config parse, dependency import, or tiny CPU forward does not prove CUDA,
AMP, distributed, dataset, checkpoint, or benchmark behavior. For GPU claims,
run a tiny operation on the requested CUDA device. For a real metric, require a
real compatible split and checkpoint. Treat training, multi-scale/slide
segmentation, COCO evaluation, DINO ImageNet pretraining, GAN FID, multi-GPU
launch, export, quantization, and cross-framework porting as explicit
operations with an approved output path and stop condition.

Do not overwrite checkpoints, delete demo output trees, mutate a dataset, or
fetch external weights/data without explicit authorization. Prefer a new output
prefix and read-only preflight. Record the source commit and effective config
in any downstream experiment handoff; consult
[repo-provenance.md](references/repo-provenance.md) before deciding whether a
checkout is stale.
