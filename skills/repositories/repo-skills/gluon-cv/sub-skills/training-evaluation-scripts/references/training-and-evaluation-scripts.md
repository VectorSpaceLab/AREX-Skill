# Training and evaluation flag anatomy

Read this when you need to construct a GluonCV script-style workflow plan without reopening or depending on the original source checkout. The patterns below are **flag templates**, not executable commands.

## General decision flow

1. **Choose the family.** Classification, detection, instance segmentation, semantic segmentation, pose, action recognition/video, depth, tracking, GAN, Re-ID, dataset preparation, AutoGluon, or deployment/export.
2. **Choose the backend.** Most older image workflows are MXNet-style; Torch support is concentrated in action recognition, DirectPose, and some AutoGluon/Torch estimators.
3. **Resolve data.** Name the dataset and root before command construction. Scripts usually assume prepared benchmark layouts, not arbitrary image folders.
4. **Resolve model.** MXNet-style workflows often use `--model` or `--network`; Torch action workflows usually use `--config-file`.
5. **Resolve resources.** Set CPU/GPU flags intentionally. Many source-family defaults are GPU-oriented even when a CPU API smoke is possible elsewhere.
6. **Decide side effects.** Training/evaluation writes logs/checkpoints/results; demos may download weights; dataset workflows may download/extract/convert large archives.

## Common flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--model` | Classification, segmentation, action, or pose model name/family. | Cross-check MXNet names in `../mxnet-model-zoo/` or Torch names in `../torch-video-workflows/`. |
| `--network` | Detection network/model family. | SSD/YOLO/Faster R-CNN/CenterNet families use this heavily. |
| `--dataset` | Dataset selector such as `voc`, `coco`, `pascal`, `ade20k`, `ucf101`, `kinetics400`. | The selector rarely creates data; verify root/annotations first. |
| `--dataset-root`, `--data-dir`, `--val-data-dir` | Dataset root or split-specific path. | Use explicit user-provided paths; this skill does not assume `~/.mxnet/datasets`. |
| `--gpus`, `--num-gpus`, `--gpu-id` | Accelerator selection. | Empty `--gpus ""` or `--num-gpus 0` is safest only when the workflow supports CPU. |
| `--batch-size` | Mini-batch size. | Reduce for CPU or memory-limited GPU dry runs. |
| `--num-workers`, `--workers`, `-j` | Data-loader workers. | Use `0` or `1` for debugging path/annotation problems. |
| `--epochs`, `--num-epochs` | Training duration. | Tiny values still perform training; do not run without data/resource approval. |
| `--resume`, `--resume-params`, `--model-prefix`, `--params-file` | Checkpoint/model artifact path. | Verify architecture/classes match the checkpoint. |
| `--pretrained` | Whether to use pretrained weights. | May download; use sibling model-zoo guidance for cache/network caveats. |
| `--deploy`, `--quantized` | Evaluation/export mode switches. | Route deployment details to `../automl-deployment-export/`. |
| `--config-file` | Torch action-recognition/DirectPose config. | Route config semantics to `../torch-video-workflows/`. |

## Bundled flag-template helper

Use the helper to create a non-executable skeleton with warnings:

```bash
python scripts/build_training_command.py classification-cifar --model resnet --num-gpus 0 --epochs 1
python scripts/build_training_command.py detection-yolo --dataset voc --dataset-root /data/VOCdevkit --gpus "" --batch-size 2
python scripts/build_training_command.py action-torch --config-file configs/i3d_resnet50_v1_kinetics400.yaml --gpus ""
```

The helper prints a `flag_template` beginning with a pseudo `<script-family>` marker. That marker intentionally prevents accidental execution while preserving the flag shape.

## Family notes

### Classification

CIFAR-style workflows use `--model`, `--batch-size`, `--num-gpus`, `--num-epochs`, learning-rate flags, and CIFAR data handling. ImageNet-style workflows add `--data-dir` or RecordIO paths, optional DALI/Horovod, dtype, mixup/label smoothing, and many optimizer schedules. Finetuning uses a custom dataset root and pretrained model.

### Detection and instance segmentation

SSD, YOLO, Faster R-CNN, CenterNet, and Mask R-CNN workflows use combinations of `--network`, `--dataset`, `--dataset-root`, `--data-shape`, `--batch-size`, `--gpus`, `--num-workers`, `--epochs`, `--resume`, `--pretrained`, `--save-prefix`, `--save-json`, `--deploy`, and `--quantized`. Validate boxes/classes with `../data-transforms-datasets/` and model names/classes with `../mxnet-model-zoo/` before real training.

### Segmentation, pose, depth, and tracking

Segmentation selects `--model`, `--backbone`, `--dataset`, crop/base sizes, workers, and GPUs. Simple/Alpha pose require detector/pose model names, COCO-style keypoint data, `--num-joints`, input size, and optional webcam/image inputs. Monodepth2, SiamRPN, and SMOT are data/checkpoint-heavy and should remain planned workflows unless the user supplies data and runtime approval.

### Action recognition and Torch config workflows

MXNet action workflows expose explicit `--dataset`, `--model`, data/list, and GPU flags. Torch action and DDP workflows usually take `--config-file` plus config overrides. Use `../torch-video-workflows/` to validate registry names, config roots, tensor shapes, and CPU sanity checks before launching train/test/FPS/FLOPS/feature jobs.

### Dataset preparation

Dataset-preparation workflows expose `--download-dir`, `--target-dir`, `--no-download`, `--overwrite`, frame roots, annotation roots, and thread counts. Treat them as network/storage/large-conversion workflows unless the user explicitly approves those side effects.
