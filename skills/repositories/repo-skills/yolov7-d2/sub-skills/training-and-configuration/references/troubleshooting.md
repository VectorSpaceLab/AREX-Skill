# Training and Configuration Troubleshooting

## `_BASE_` file not found

Some configs reference base filenames with different casing. On case-sensitive systems, `Base-YoloV7.yaml` does not resolve to `Base-YOLOv7.yaml`. Fix the `_BASE_` path in the user's config copy or choose a config whose base path resolves.

## `KeyError: No object named ... in META_ARCH_REGISTRY`

Likely causes:

- `add_yolo_config` or model imports were not executed before building the model.
- The user's installed package differs from the config's expected source version.
- The config names a WIP/closed-source architecture that is not present.

Run the root smoke script and inspect the `MODEL.META_ARCHITECTURE` value.

## Dataset not registered

Symptoms include Detectron2 errors for missing dataset names or empty test sets. Register the dataset before trainer construction and ensure `DATASETS.TRAIN`/`TEST` exactly match the registration names.

## Class count mismatch

If predictions have wrong labels or loss shapes, compare the number of `categories` in the COCO JSON to `MODEL.YOLO.CLASSES` and any class-name list. Adjust the config before training.

## Empty annotations or invalid boxes

Validate COCO JSON first. Remove or fix annotations with missing image/category ids, non-positive width/height, or boxes outside image boundaries. For segmentation, ensure mask format matches `INPUT.MASK_FORMAT`.

## W&B import failure

`train_det.py` imports the W&B logger module, and that module imports `wandb`. Install `wandb` or patch the logger import in the user's working environment even if `WANDB.ENABLED` is false.

## `mish-cuda` recommendation

The message is an optional performance hint. Do not block CPU config inspection or basic training setup on it. Install it only when the user's PyTorch/CUDA version supports it and they need GPU performance tuning.

## Training starts but loss does not improve

First verify dataset labels, class count, anchors for anchor-based models, checkpoint compatibility, input format (BGR/RGB), and augmentation settings. For transformer backbones, the repository docs warn that pretrained weights are important.
