# Dataset Layouts

## Purpose

Read this before running any project workflow that expects ImageNet, ImageNet-22k, subImageNet, or COCO-style data.
The bundled `../scripts/check_dataset_layout.py` validates the common layouts without mutating data.

## ImageNet-1k

Used by AutoFormer, AutoFormerV2, EfficientViT classification, MiniViT, TinyCLIP evaluation, TinyViT, and iRPE DeiT.

Standard folder layout:

```text
ImageNet/
├── train/
│   ├── class_a/
│   └── ...
└── val/
    ├── class_a/
    └── ...
```

Several workflows also accept `train.tar` / `val.tar` archives.

## ImageNet-22k

Used by TinyViT pretraining and TinyCLIP pretraining / evaluation variants.

Typical layout:

```text
ImageNet-22k/
├── in22k_image_names.txt
├── n00004475.zip
├── n00005787.zip
└── ...
```

TinyViT also expects a sibling or symlinked ImageNet-1k directory for finetuning and evaluation.

## subImageNet / sampled ImageNet

Used by AutoFormer and Cream search workflows.

Expected shape after generation:

```text
./data/
├── imagenet/
│   ├── train/
│   └── val/
└── subImageNet/
    ├── info.txt
    └── subimages_list.txt
```

The bundled skill treats the source scripts that copy images as reference evidence only; use the read-only layout checker instead of the original mutating generators.

## COCO 2017

Used by EfficientViT downstream and iRPE DETR.

Typical layout:

```text
coco/
├── annotations/
├── train2017/
├── val2017/
└── test2017/   # optional
```

## Why these checks matter

Most training / evaluation failures in this repo family come from one of four causes:

1. Wrong folder name.
2. Wrong split name.
3. Missing symlink or archive.
4. A workflow that expects a sampled or copied subset instead of the full dataset.
