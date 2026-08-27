---
name: cream
description: "Routes DisCo Researcher to Cream-family vision NAS, compression,
  distillation, and relative-position-encoding workflows across the AutoFormer,
  AutoFormerV2, Cream, CDARTS, EfficientViT, MiniViT, TinyCLIP, TinyViT, and
  iRPE project families."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Cream

Use this skill when the user is working with the **Cream** monorepo or one of its vision-model subprojects.
It is a router, not a manual: pick the matching sub-skill first, then read the bundled references and run the bundled checks.

## What this skill covers

- AutoFormer and AutoFormerV2 search / evaluation / subImageNet workflows.
- Cream and CDARTS NAS, retrain, test, and dataset-prep workflows.
- EfficientViT classification plus downstream detection / segmentation.
- MiniViT Mini-DeiT and Mini-Swin distillation / compression workflows.
- TinyCLIP OpenCLIP-based inference, evaluation, and pretraining.
- TinyViT model creation, evaluation, sparse-logit saving, and training.
- iRPE integration for DeiT and DETR.

## Quick setup

Use a CUDA-capable inspection environment with the shared packages validated for this repo family:

```bash
python -m pip install torch torchvision timm==0.4.12 yacs easydict termcolor ftfy regex tqdm huggingface_hub webdataset braceexpand pandas psutil tensorboard tensorboardX graphviz scikit-image opencv-python thop fvcore submitit onnx onnxruntime pytest open_clip_torch
```

For legacy NAS routes, the bundled compatibility notes explain the `torch._six` shim and other historical-dependency caveats.

## Minimal environment check

```bash
python scripts/check_environment.py --modules torch,torchvision,timm,open_clip,yacs,easydict,ftfy,regex,webdataset,huggingface_hub,submitit,fvcore
python scripts/check_dataset_layout.py --help
```

## Route map

| Route | Read this sub-skill for | Typical user phrases |
| --- | --- | --- |
| `sub-skills/nas-search/` | AutoFormer, AutoFormerV2, Cream, and CDARTS search / retrain / test / dataset prep | "AutoFormer", "S3", "Cream NAS", "CDARTS", "subImageNet", "search architecture" |
| `sub-skills/efficientvit/` | EfficientViT classification and downstream detection / segmentation | "EfficientViT", "ImageNet eval", "COCO downstream", "RetinaNet", "Mask R-CNN" |
| `sub-skills/minivit/` | Mini-DeiT and Mini-Swin distillation / compression workflows | "MiniViT", "Mini-DeiT", "Mini-Swin", "weight multiplexing" |
| `sub-skills/tinyclip/` | TinyCLIP inference, evaluation, and pretraining | "TinyCLIP", "OpenCLIP", "zero-shot", "pretrain", "weight inheritance" |
| `sub-skills/tinyvit/` | TinyViT evaluation, sparse-logit saving, finetuning, and training | "TinyViT", "save logits", "22k to 1k", "higher resolution" |
| `sub-skills/irpe/` | iRPE for DeiT and DETR | "iRPE", "relative position encoding", "DeiT with iRPE", "DETR with iRPE" |

## Shared helpers

- `scripts/check_environment.py` — import and backend smoke check for the shared Python environment.
- `scripts/check_dataset_layout.py` — validate ImageNet, ImageNet-22k, subImageNet, and COCO-style layouts.
- `scripts/check_custom_ops.py` — report whether the optional `rpe_ops` extensions are built.
- `scripts/check_legacy_imports.py` — probe the legacy NAS modules under a modern-torch compatibility shim.

## Cross-cutting references

- `references/compatibility.md` — read when you need the verified environment baseline, legacy-torch caveats, or the TinyCLIP package note.
- `references/dataset-layouts.md` — read when you need the canonical ImageNet, ImageNet-22k, subImageNet, or COCO folder shapes.
- `references/troubleshooting.md` — read first for repo-wide failure patterns before you narrow the issue to a specific sub-skill.

## Read provenance before refreshing

Read `references/repo-provenance.md` when you need to decide whether this skill still matches a Cream checkout.
If the repository commit, dirty state, or major evidence paths changed, refresh the skill instead of reusing it blindly.

## Notes

- The generated skill is self-contained. Do not rely on the original repository checkout at runtime.
- Project-specific commands, API signatures, model names, and troubleshooting details live in the sub-skill references.
- Do not run the source repository's heavy training, search, or download commands unless the user explicitly asks for them.
