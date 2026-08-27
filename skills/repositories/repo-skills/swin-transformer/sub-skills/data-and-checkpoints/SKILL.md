---
name: data-and-checkpoints
description: "Use this repo skill for Swin-Transformer ImageNet folder, zip,
  ImageNet-22K, SimMIM data layouts, and checkpoint resume/pretrained loading
  behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# data-and-checkpoints

Use this sub-skill when a task involves data roots, zipped ImageNet maps, ImageNet-22K annotations, SimMIM input batches, checkpoint files, pretrained-vs-resume semantics, or class-head remapping.

## What this sub-skill covers

- ImageNet-1K folder layout for `torchvision.datasets.ImageFolder`.
- Zipped ImageNet layout with `train.zip`, `val.zip`, `train_map.txt`, and `val_map.txt`.
- ImageNet-22K layout and JSON map expectations for `IN22KDATASET`.
- SimMIM pretraining data shape: images plus generated masks.
- Checkpoint dictionary expectations for `load_checkpoint` and `load_pretrained`.
- ImageNet-22K-to-1K classifier head remapping through the 22K class map.

## Boundaries

- For model constructors and output tensor shapes, use `core-models`.
- For supervised train/eval commands, use `training-eval-cli`.
- For SimMIM launch commands and mask-loss details, use `simmim-workflows`.
- For MoE checkpoint sharding and Tutel-specific behavior, use `moe-and-acceleration`.

## Standard workflow

1. Identify the data mode: `imagenet` folder, zipped `imagenet`, `imagenet22K`, or SimMIM pretrain/fine-tune.
2. Read `references/data-formats.md` for the exact structure.
3. Run `scripts/validate_imagenet_layout.py` on a small or full data root before composing a training command.
4. If a checkpoint is involved, read `references/checkpoint-loading.md` to choose `--resume` vs `--pretrained` and anticipate classifier-head behavior.
5. Use `references/troubleshooting.md` if data loaders report empty datasets, malformed maps, or checkpoint key mismatches.

## Safe checks

The bundled validator checks schema and small samples only. It does not download ImageNet, rewrite validation folders, unzip archives, or load model weights.

## Linked files

- `references/data-formats.md` - folder, zip, 22K, and SimMIM data structures.
- `references/checkpoint-loading.md` - resume/pretrained/checkpoint remap behavior.
- `references/troubleshooting.md` - common data and checkpoint failures.
- `scripts/validate_imagenet_layout.py` - safe schema validator for folder, zip, and ImageNet-22K JSON map layouts.
