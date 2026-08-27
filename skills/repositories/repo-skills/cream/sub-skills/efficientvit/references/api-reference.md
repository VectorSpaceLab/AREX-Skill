# EfficientViT API Reference

## Purpose

Read this when you need the verified model-builder and CLI surface for EfficientViT.
The inspection environment confirmed the classification builders and their returned module structure.

## Verified builder signatures

Classification builders live in `classification/model/build.py` and are registered with timm:

- `EfficientViT_M0(num_classes=1000, pretrained=False, distillation=False, fuse=False, pretrained_cfg=None, model_cfg=EfficientViT_m0)`
- `EfficientViT_M1(num_classes=1000, pretrained=False, distillation=False, fuse=False, pretrained_cfg=None, model_cfg=EfficientViT_m1)`
- `EfficientViT_M2(num_classes=1000, pretrained=False, distillation=False, fuse=False, pretrained_cfg=None, model_cfg=EfficientViT_m2)`
- `EfficientViT_M3(num_classes=1000, pretrained=False, distillation=False, fuse=False, pretrained_cfg=None, model_cfg=EfficientViT_m3)`
- `EfficientViT_M4(num_classes=1000, pretrained=False, distillation=False, fuse=False, pretrained_cfg=None, model_cfg=EfficientViT_m4)`
- `EfficientViT_M5(num_classes=1000, pretrained=False, distillation=False, fuse=False, pretrained_cfg=None, model_cfg=EfficientViT_m5)`

`replace_batchnorm(net)` is the helper used to fuse batchnorm for deployment-style inspection.

## Observed structure

A created classification model exposes a `head` attribute that is a `BN_Linear` wrapper containing a linear layer at `head.l`.
That matters when you want to inspect or compare the final classifier weights.

## CLI surface

### Classification

`classification/main.py` parses the standard ImageNet options plus:

- `--model`
- `--data-path`
- `--resume`
- `--eval`
- `--dist-eval`
- `--batch-size`
- `--output_dir`
- `--device`
- `--dist-url`
- `--world_size`

### Speed / throughput

The original `classification/speed_test.py` is a script-style benchmark with no argument parser.
The bundled benchmark helper replaces that with explicit `--model`, `--device`, `--batch-size`, and timing flags.

### Downstream detection / segmentation

`downstream/efficientvit.py` exports the same family names for MMDetection backbones, but the downstream workflow depends on the MMDetection/MMCV stack and the `dist_train.sh` / `dist_test.sh` wrappers.

## Practical notes

- Use the classification builders for local import and model-shape checks.
- Use the downstream wrappers only when the COCO / MMDetection dependencies are installed.
- The model zoo URLs in the source repository are evidence, not runtime dependencies; future agents should use user-supplied checkpoints or publicly documented downloads.
